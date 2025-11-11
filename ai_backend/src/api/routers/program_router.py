# _*_ coding: utf-8 _*_
"""Program Management API endpoints."""
import logging
from typing import List, Optional

import io
import urllib.parse
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from src.api.services.program_service import ProgramService
from src.api.services.s3_download_service import S3DownloadService
from src.core.dependencies import (
    get_program_service,
    get_db,
    get_s3_download_service,
    get_knowledge_status_service,
)
from src.api.services.knowledge_status_service import KnowledgeStatusService
from src.database.crud.program_crud import ProgramCRUD
from src.types.response.program_response import (
    ProgramInfo,
    ProgramValidationResult,
    RegisterProgramResponse,
    ProgramListItem,
    ProgramListResponse,
)
from src.types.response.plc_response import (
    ProgramMappingItem,
    ProgramMappingListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/programs", tags=["program-management"])


@router.get("/files/download")
def download_file(
    file_type: str = Query(
        ...,
        description=(
            "파일 타입: "
            "template (정적), logic_file, logic_classification, "
            "plc_ladder_comment (동적 - program_id 필수)"
        ),
    ),
    program_id: Optional[str] = Query(
        None, description="Program ID (동적 파일인 경우 필수)"
    ),
    db: Session = Depends(get_db),
    s3_download_service: S3DownloadService = Depends(get_s3_download_service),
):
    """
    범용 파일 다운로드 API

    Args:
        file_type: 파일 타입
            - "template": PGM 등록용 템플릿 (XLSX) - 정적 파일
            - "logic_file": 로직 파일 (program_id 필수)
            - "logic_classification": Logic 분류체계 (XLSX) - program_id 필수
            - "plc_ladder_comment": PLC Ladder Comment 파일 (CSV) - program_id 필수
        program_id: Program ID (동적 파일인 경우 필수)

    Returns:
        StreamingResponse: 파일 다운로드 응답
    """
    try:
        file_content, filename, content_type = (
            s3_download_service.download_program_file(
                file_type=file_type,
                program_id=program_id,
                db_session=db,
            )
        )

        # 한글 파일명 처리를 위한 URL 인코딩
        encoded_filename = urllib.parse.quote(filename.encode("utf-8"))

        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{encoded_filename}"
                )
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            "파일 다운로드 실패: file_type=%s, program_id=%s, error=%s",
            file_type,
            program_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 다운로드 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.post(
    "/register",
    response_model=RegisterProgramResponse,
    summary="프로그램 등록",
    description="""
    PLC 프로그램을 등록하고 처리합니다.
    
    **처리 단계:**
    1. **유효성 검사** (동기): 파일 형식, 내용 검증
    2. **즉시 응답 반환**: 유효성 검사 결과 반환
    3. **백그라운드 처리** (비동기):
       - S3에 파일 업로드 및 ZIP 압축 해제
       - 템플릿 및 템플릿 데이터 생성
       - 데이터 전처리 및 Document 생성
       - Vector DB 인덱싱 요청
    
    **필수 파일:**
    - `ladder_zip`: PLC ladder logic 파일들이 포함된 ZIP 압축 파일
      - 압축 해제 후 각 로직 파일이 분리됨
    - `classification_xlsx`: 템플릿 분류체계 데이터 (XLSX)
      - 컬럼: FOLDER_ID, FOLDER_NAME, SUB_FOLDER_NAME, LOGIC_ID, LOGIC_NAME
      - 로직 파일명과 매칭되어 템플릿 데이터 생성
    - `device_comment_csv`: Device 설명 파일 (CSV)
      - Ladder 로직의 device에 대한 코멘트 정보
    
    **유효성 검사 항목:**
    - ZIP 파일 무결성 검사
    - XLSX 파일 형식 및 필수 컬럼 검증
    - CSV 파일 형식 검증
    - 로직 파일명과 분류체계 데이터 교차 검증
    
    **응답:**
    - 성공 시: `status="success"`, `message="파일 등록 요청하였습니다."`
    - 실패 시: `status="validation_failed"`, 에러 목록 포함
    
    **예외 상황:**
    - `PROGRAM_REGISTRATION_ERROR`: 등록 처리 중 오류
    - 유효성 검사 실패: 에러 목록이 `validation_result.errors`에 포함
    """,
)
async def register_program(
    ladder_zip: UploadFile = File(..., description="PLC ladder logic ZIP 파일", example="ladder_files.zip"),
    classification_xlsx: UploadFile = File(
        ..., description="템플릿 분류체계 데이터 XLSX 파일", example="classification.xlsx"
    ),
    device_comment_csv: UploadFile = File(..., description="Device 설명 CSV 파일", example="device_comment.csv"),
    program_title: str = Form(..., description="프로그램 제목", example="공정1 PLC 프로그램"),
    program_description: Optional[str] = Form(None, description="프로그램 설명", example="공정1 라인용 PLC 프로그램"),
    user_id: str = Form(default="user", description="사용자 ID", example="user001"),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    프로그램 등록 API

    - ladder_zip: PLC ladder logic 파일들이 포함된 압축 파일
    - classification_xlsx: 템플릿 분류체계 데이터 (로직 파일명 포함)
    - device_comment_csv: ladder 로직에 있는 device 설명

    유효성 검사를 통과하면:
    1. S3에 파일 업로드 및 ZIP 압축 해제 (비동기)
    2. 백엔드 DB에 메타데이터 저장 (비동기)
    3. Vector DB 인덱싱 요청 (비동기)
    """
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리

    result = await program_service.register_program(
        program_title=program_title,
        program_description=program_description,
        user_id=user_id,
        ladder_zip=ladder_zip,
        classification_xlsx=classification_xlsx,
        device_comment_csv=device_comment_csv,
    )

    # 유효성 검사 결과 구성
    validation_result = None
    if result.get("is_valid") and result.get("warnings"):
        validation_result = ProgramValidationResult(
            is_valid=True,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            checked_files=result.get("checked_files", []),
        )
    elif not result.get("is_valid"):
        validation_result = ProgramValidationResult(
            is_valid=False,
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
            checked_files=result.get("checked_files", []),
        )

    return RegisterProgramResponse(
        status="success" if result.get("is_valid") else "validation_failed",
        message=result.get(
            "message", "프로그램이 등록되었습니다. 백그라운드에서 처리 중입니다."
        ),
        data=ProgramInfo(**result) if result.get("program_id") else None,
        validation_result=validation_result,
    )


@router.get(
    "",
    response_model=ProgramListResponse,
    summary="프로그램 목록 조회",
    description="""
    프로그램 목록을 검색, 필터링, 페이지네이션, 정렬 기능으로 조회합니다.
    
    **화면 용도:** PLC 등록 관리 화면의 테이블 데이터
    
    **검색 기능:**
    - `program_id`: PGM ID로 정확한 검색
    - `program_name`: 제목으로 부분 일치 검색
    
    **필터링 기능:**
    - `status`: 등록 상태로 필터링
      - `preparing`: 준비 중
      - `uploading`: 업로드 중
      - `processing`: 처리 중
      - `embedding`: 임베딩 중
      - `completed`: 성공
      - `failed`: 실패
      - `indexing_failed`: 인덱싱 실패
    - `create_user`: 작성자로 필터링
    
    **페이지네이션:**
    - `page`: 페이지 번호 (기본값: 1, 최소: 1)
    - `page_size`: 페이지당 항목 수 (기본값: 10, 최소: 1, 최대: 100)
    
    **정렬:**
    - `sort_by`: 정렬 기준 (기본값: `create_dt`)
      - `create_dt`: 등록일시
      - `program_id`: PGM ID
      - `program_name`: 제목
      - `status`: 상태
    - `sort_order`: 정렬 순서 (기본값: `desc`)
      - `asc`: 오름차순
      - `desc`: 내림차순
    
    **응답 데이터:**
    - 프로그램 목록 (PGM ID, 제목, 공정명, 파일 개수, 상태, 처리 시간 등)
    - 전체 개수 및 페이지 정보
    
    **사용 예시:**
    - 전체 목록: `GET /programs?page=1&page_size=10`
    - 검색: `GET /programs?program_name=공정1&page=1`
    - 필터링: `GET /programs?status=completed&page=1`
    """,
)
def get_program_list(
    program_id: Optional[str] = Query(None, description="PGM ID로 검색", example="pgm001"),
    program_name: Optional[str] = Query(None, description="제목으로 검색", example="공정1"),
    status_filter: Optional[str] = Query(
        None, description="등록 상태로 필터링 (preparing, uploading, processing, embedding, completed, failed, indexing_failed)", alias="status", example="completed"
    ),
    create_user: Optional[str] = Query(None, description="작성자로 필터링", example="user001"),
    page: int = Query(1, ge=1, description="페이지 번호", example=1),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수", example=10),
    sort_by: str = Query(
        "create_dt",
        description="정렬 기준 (create_dt, program_id, program_name, status)",
        example="create_dt",
    ),
    sort_order: str = Query("desc", description="정렬 순서 (asc, desc)", example="desc"),
    db: Session = Depends(get_db),
):
    """
    프로그램 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

    화면: PLC 등록 관리 화면의 테이블 데이터
    - PGM ID, 제목으로 검색
    - 등록 상태, 작성자로 필터링
    - 페이지네이션 및 정렬 지원
    """
    try:
        program_crud = ProgramCRUD(db)
        programs, total_count = program_crud.get_programs(
            program_id=program_id,
            program_name=program_name,
            status=status_filter,
            create_user=create_user,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Program ID 리스트로 PLC와 ProcessMaster 조인하여 공정 정보 조회
        program_ids = [p.program_id for p in programs]
        process_name_map = {}
        if program_ids:
            from src.database.models.plc_models import PLC
            from src.database.models.master_models import ProcessMaster

            plcs = (
                db.query(PLC, ProcessMaster)
                .outerjoin(
                    ProcessMaster,
                    PLC.process_id_snapshot == ProcessMaster.process_id,
                )
                .filter(PLC.program_id.in_(program_ids))
                .filter(PLC.is_active.is_(True))
                .all()
            )

            for plc, process_master in plcs:
                if process_master:
                    process_name_map[plc.program_id] = (
                        process_master.process_name
                    )

        # Document 통계는 metadata_json에 저장된 것을 사용
        # (백그라운드 작업에서 주기적으로 업데이트됨)

        # ProgramListItem으로 변환
        items = []
        for program in programs:
            # metadata_json에서 파일 개수 추출
            metadata = program.metadata_json or {}
            ladder_file_count = metadata.get("ladder_file_count", 0)
            # 기본값 1 (CSV 파일 1개)
            comment_file_count = metadata.get("comment_file_count", 1)

            # 등록 소요시간 계산
            processing_time = None
            if program.completed_at and program.create_dt:
                duration = program.completed_at - program.create_dt
                total_seconds = int(duration.total_seconds())
                if total_seconds > 0:
                    minutes = total_seconds // 60
                    if minutes > 0:
                        processing_time = f"{minutes} min"
                    else:
                        processing_time = f"{total_seconds} sec"

            # 상태 표시명 매핑
            status_display_map = {
                "preparing": "준비 중",
                "uploading": "업로드 중",
                "processing": "처리 중",
                "embedding": "임베딩 중",
                "completed": "성공",
                "failed": "실패",
                "indexing_failed": "인덱싱 실패",
            }
            status_display = status_display_map.get(
                program.status, program.status
            )

            # 진행률 계산 (업로드 중, 처리 중, 임베딩 중)
            # metadata_json에 저장된 document_stats 사용
            if program.status in ["uploading", "processing", "embedding"]:
                from src.api.services.progress_update_service import (
                    ProgressUpdateService,
                )

                progress_service = ProgressUpdateService(db)
                stats = metadata.get("document_stats", {})

                # 통계가 없거나 오래된 경우 실시간 계산 (fallback)
                if not stats:
                    stats = progress_service.calculate_document_stats(
                        program.program_id
                    )

                if program.status == "uploading":
                    # 업로드 중: 전체 파일 수는 항상 3개 (ladder_logic, comment, template)
                    total_files = stats.get("total_upload", 3)
                    uploaded = stats.get("uploaded", 0)
                    if total_files > 0:
                        progress = round((uploaded / total_files) * 30)
                        status_display = f"업로드 중({progress}%)"
                    else:
                        status_display = "업로드 중(0%)"
                elif program.status == "processing":
                    # 처리 중: metadata의 total_expected 우선, 없으면 total_processed
                    total_files = metadata.get(
                        "total_expected", stats.get("total_processed", 0)
                    )
                    processed = stats.get("processed", 0)
                    if total_files > 0:
                        progress = 31 + round((processed / total_files) * 30)
                        status_display = f"처리 중({progress}%)"
                    else:
                        status_display = "처리 중(31%)"
                elif program.status == "embedding":
                    # 임베딩 중: metadata의 total_expected 우선, 없으면 total_processed
                    total_files = metadata.get(
                        "total_expected", stats.get("total_processed", 0)
                    )
                    embedded = stats.get("embedded", 0)
                    if total_files > 0:
                        progress = 61 + round((embedded / total_files) * 39)
                        status_display = f"임베딩 중({progress}%)"
                    else:
                        status_display = "임베딩 중(61%)"

            # 공정명 조회
            process_name = process_name_map.get(program.program_id)

            items.append(
                ProgramListItem(
                    program_id=program.program_id,
                    program_name=program.program_name,
                    process_name=process_name,
                    ladder_file_count=ladder_file_count,
                    comment_file_count=comment_file_count,
                    status=program.status,
                    status_display=status_display,
                    processing_time=processing_time,
                    create_user=program.create_user,
                    create_dt=program.create_dt,
                )
            )

        total_pages = (total_count + page_size - 1) // page_size

        return ProgramListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("프로그램 목록 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로그램 목록 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get("/mapping", response_model=ProgramMappingListResponse)
def get_program_list_for_mapping(
    program_id: Optional[str] = Query(None, description="PGM ID로 검색"),
    program_name: Optional[str] = Query(None, description="제목으로 검색"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(10, ge=1, le=100, description="페이지당 항목 수"),
    db: Session = Depends(get_db),
):
    """
    PGM 프로그램 목록 조회 (매핑용)

    화면: PLC 관리 화면의 PGM 프로그램 테이블
    - PGM ID, 제목으로 검색
    - Ladder 파일 개수, Comment 파일 개수 표시
    - 등록자(등록일시) 표시
    - 간단한 정보만 반환 (매핑 선택용)
    """
    try:
        program_crud = ProgramCRUD(db)
        programs, total_count = program_crud.get_programs(
            program_id=program_id,
            program_name=program_name,
            status=None,  # 매핑용이므로 상태 필터링 없음
            create_user=None,
            page=page,
            page_size=page_size,
            sort_by="create_dt",
            sort_order="desc",
        )

        items = []
        for program in programs:
            # metadata_json에서 파일 개수 추출
            metadata = program.metadata_json or {}
            ladder_file_count = metadata.get("ladder_file_count", 0)
            comment_file_count = metadata.get("comment_file_count", 1)

            items.append(
                ProgramMappingItem(
                    program_id=program.program_id,
                    program_name=program.program_name,
                    ladder_file_count=ladder_file_count,
                    comment_file_count=comment_file_count,
                    create_user=program.create_user,
                    create_dt=program.create_dt,
                )
            )

        total_pages = (total_count + page_size - 1) // page_size

        return ProgramMappingListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("PGM 프로그램 목록 조회 실패 (매핑용): %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PGM 프로그램 목록 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get("/user/{user_id}", response_model=List[ProgramInfo])
async def get_user_programs(
    user_id: str,
    program_service: ProgramService = Depends(get_program_service),
):
    """사용자의 프로그램 목록 조회 (기존 API 유지)"""
    programs = await program_service.get_user_programs(user_id)
    return [ProgramInfo(**p) for p in programs]


@router.get("/{program_id}", response_model=ProgramInfo)
async def get_program(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램 정보 조회"""
    program = await program_service.get_program(program_id, user_id)
    return ProgramInfo(**program)


@router.post("/{program_id}/retry")
async def retry_failed_files(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    retry_type: str = Query(
        default="all", description="재시도 타입 (preprocessing, document, all)"
    ),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    실패한 파일 재시도 API

    - preprocessing: 전처리 실패 파일만 재시도
    - document: Document 저장 실패 파일만 재시도
    - all: 모든 실패 파일 재시도
    """
    result = await program_service.retry_failed_files(
        program_id=program_id, user_id=user_id, retry_type=retry_type
    )
    return result


@router.get("/{program_id}/failures")
async def get_program_failures(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    failure_type: Optional[str] = Query(
        default=None,
        description=(
            "실패 타입 필터 "
            "(preprocessing, document_storage, vector_indexing)"
        ),
    ),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램의 실패 정보 목록 조회"""
    failures = await program_service.get_program_failures(
        program_id=program_id, user_id=user_id, failure_type=failure_type
    )
    return {
        "program_id": program_id,
        "failures": failures,
        "count": len(failures),
    }


@router.post("/{program_id}/knowledge-status/sync")
async def sync_knowledge_status(
    program_id: str,
    knowledge_status_service: KnowledgeStatusService = Depends(
        get_knowledge_status_service
    ),
):
    """
    Program의 Knowledge 상태 동기화 API

    외부 Knowledge API를 호출하여 Document 상태를 업데이트합니다.

    Args:
        program_id: Program ID

    Returns:
        Dict: 동기화 결과
    """
    try:
        result = await knowledge_status_service.sync_document_status(
            program_id=program_id
        )
        return result
    except Exception as e:
        logger.error(
            "Knowledge 상태 동기화 실패: program_id=%s, error=%s",
            program_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge 상태 동기화 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get("/{program_id}/knowledge-status")
async def get_knowledge_status(
    program_id: str,
    knowledge_status_service: KnowledgeStatusService = Depends(
        get_knowledge_status_service
    ),
):
    """
    Program의 Knowledge 상태 조회 API

    KnowledgeReference의 repo_id로 외부 API를 호출하여 현재 상태를 조회합니다.

    Args:
        program_id: Program ID

    Returns:
        Dict: Knowledge 상태 정보
    """
    try:
        from src.database.models.knowledge_reference_models import (
            KnowledgeReference,
        )
        from shared_core.models import Document

        # Program과 연결된 Document를 통해 KnowledgeReference 조회
        documents_with_ref = (
            knowledge_status_service.db.query(Document)
            .filter(Document.program_id == program_id)
            .filter(Document.is_deleted.is_(False))
            .filter(Document.knowledge_reference_id.isnot(None))
            .all()
        )

        if not documents_with_ref:
            return {
                "program_id": program_id,
                "knowledge_references": [],
                "message": "Knowledge Reference를 찾을 수 없습니다.",
            }

        # Document의 knowledge_reference_id로 KnowledgeReference 조회
        knowledge_ref_ids = {
            doc.knowledge_reference_id
            for doc in documents_with_ref
            if doc.knowledge_reference_id
        }

        knowledge_refs = (
            knowledge_status_service.db.query(KnowledgeReference)
            .filter(KnowledgeReference.reference_id.in_(knowledge_ref_ids))
            .filter(KnowledgeReference.is_deleted.is_(False))
            .filter(KnowledgeReference.is_active.is_(True))
            .all()
        )

        if not knowledge_refs:
            return {
                "program_id": program_id,
                "knowledge_references": [],
                "message": "활성화된 Knowledge Reference를 찾을 수 없습니다.",
            }

        # 각 KnowledgeReference의 repo_id로 문서 목록 조회
        repo_statuses = []
        for knowledge_ref in knowledge_refs:
            repo_id = knowledge_ref.repo_id
            if not repo_id:
                continue

            documents = await knowledge_status_service.get_repo_documents(
                repo_id
            )

            repo_statuses.append(
                {
                    "reference_id": knowledge_ref.reference_id,
                    "reference_type": knowledge_ref.reference_type,
                    "name": knowledge_ref.name,
                    "repo_id": repo_id,
                    "documents": documents if documents else [],
                    "document_count": len(documents) if documents else 0,
                }
            )

        return {
            "program_id": program_id,
            "knowledge_references": repo_statuses,
            "total_references": len(repo_statuses),
        }

    except Exception as e:
        logger.error(
            "Knowledge 상태 조회 실패: program_id=%s, error=%s",
            program_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge 상태 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.delete("", response_model=dict)
async def delete_programs(
    program_ids: List[str] = Query(
        ..., description="삭제할 프로그램 ID 리스트"
    ),
    user_id: Optional[str] = Query(
        None, description="사용자 ID (권한 확인용)"
    ),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    프로그램 삭제 (여러 개 일괄 삭제)

    화면: PLC 등록 관리 화면의 삭제 버튼
    - 체크박스로 선택된 프로그램들을 일괄 삭제
    - S3 파일, Documents, Knowledge, 관련 테이블 메타정보 모두 처리
    """
    try:
        if not program_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="삭제할 프로그램 ID가 필요합니다.",
            )

        results = []
        errors = []

        for program_id in program_ids:
            try:
                result = await program_service.delete_program(
                    program_id=program_id, user_id=user_id
                )
                results.append(result)
            except Exception as e:
                logger.error(
                    "프로그램 삭제 실패: program_id=%s, error=%s",
                    program_id,
                    str(e),
                )
                errors.append({"program_id": program_id, "error": str(e)})

        return {
            "message": f"{len(results)}개의 프로그램이 삭제되었습니다.",
            "deleted_count": len(results),
            "failed_count": len(errors),
            "results": results,
            "errors": errors,
            "requested_ids": program_ids,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("프로그램 일괄 삭제 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"프로그램 삭제 중 오류가 발생했습니다: {str(e)}",
        ) from e


