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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/programs", tags=["program-management"])


@router.get(
    "/files/download",
    summary="프로그램 파일 다운로드",
    description="""
    S3에 저장된 프로그램 관련 파일을 다운로드합니다.
    
    **화면 용도:** PGM 상세 팝업에서 파일 클릭 시 다운로드
    
    **파일 타입:**
    - `program_classification`: Program 분류 체계 엑셀 파일 (XLSX)
    - `program_logic`: Program Logic 파일 (ZIP - Program CSV 파일 압축)
    - `program_comment`: Program Comment 파일 (CSV)
    
    **사용 방법:**
    1. 상세 조회 API (`GET /programs/{program_id}`)에서 `files` 배열 확인
    2. 각 파일의 `file_type` 사용
    3. 다운로드 링크 생성: `/programs/files/download?file_type={file_type}&program_id={program_id}&user_id={user_id}`
    
    **예시:**
    ```
           GET /v1/programs/files/download?file_type=program_classification&program_id=PGM_000001&user_id=user001
           GET /v1/programs/files/download?file_type=program_logic&program_id=PGM_000001&user_id=user001
           GET /v1/programs/files/download?file_type=program_comment&program_id=PGM_000001&user_id=user001
    ```
    
    **보안:**
    - program_id로 먼저 권한 검증 수행
    - 사용자가 접근 가능한 공정의 파일만 다운로드 가능
    
    **응답:**
    - 파일 다운로드 스트림 (Content-Disposition 헤더 포함)
    - 원본 파일명으로 다운로드됨
    """,
)
def download_file(
    file_type: str = Query(
        ...,
        description=(
            "파일 타입: "
            "program_classification (Program 분류 체계 엑셀), "
            "program_logic (Program Logic ZIP 파일), "
            "program_comment (Program Comment CSV)"
        ),
        example="program_classification",
    ),
    program_id: str = Query(
        ..., description="Program ID", example="PGM_000001"
    ),
    user_id: str = Query(..., description="사용자 ID (권한 검증용)", example="user001"),
    db: Session = Depends(get_db),
    s3_download_service: S3DownloadService = Depends(get_s3_download_service),
):
    """
    S3 파일 다운로드 API (file_type + program_id 방식)

    Args:
        file_type: 파일 타입 (program_classification, program_logic, program_comment)
        program_id: Program ID
        user_id: 사용자 ID (권한 검증용)

    Returns:
        StreamingResponse: 파일 다운로드 응답
    """
    try:
        # 권한 검증 및 파일 다운로드
        program_crud = ProgramCRUD(db)
        
        # 1. Program 존재 확인 및 권한 검증
        program = program_crud.get_program(program_id)
        if not program:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"프로그램을 찾을 수 없습니다: {program_id}",
            )
        
        # 2. 사용자 권한 확인 (process_id 기반)
        if program.process_id:
            accessible_process_ids = (
                program_crud.get_accessible_process_ids(user_id)
            )
            if accessible_process_ids is not None:  # None이면 모든 공정 접근 가능
                if program.process_id not in accessible_process_ids:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="프로그램 파일에 접근할 권한이 없습니다.",
                    )
        
        # 3. 파일 다운로드 (file_type + program_id로 조회)
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
    
    **요청 파라미터:**
    - `program_title`: PGM Name (프로그램 제목, 필수)
    - `process_id`: 공정 ID (드롭다운 선택, 필수)
    - `program_description`: 프로그램 설명 (선택사항)
    - `user_id`: 사용자 ID (기본값: "user")
    
    **Program ID 생성 규칙:**
    - 형식: `pgm_{process_id}_{타임스탬프(10자리)}`
    - 예: `pgm_process_001_2501011200`
    - 타임스탬프: YYMMDDHHMM (연도 2자리, 월일시분)
    
    **필수 파일:**
    - `ladder_zip`: Logic 파일 (Program CSV 파일을 zip으로 압축)
      - 압축 해제 후 각 로직 파일이 분리됨
    - `template_xlsx`: 템플릿 분류 체계 엑셀 파일 (XLSX)
      - 컬럼: FOLDER_ID, FOLDER_NAME, SUB_FOLDER_NAME, LOGIC_ID, LOGIC_NAME
      - 로직 파일명과 매칭되어 템플릿 데이터 생성
    - `comment_csv`: PLC Ladder Comment 파일 (CSV)
      - Ladder 로직의 device에 대한 코멘트 정보
    
    **유효성 검사 항목:**
    - ZIP 파일 무결성 검사
    - XLSX 파일 형식 및 필수 컬럼 검증
    - CSV 파일 형식 검증
    - 로직 파일명과 분류체계 데이터 교차 검증
    
    **응답:**
    - 성공 시: `status="success"`, `message="파일 유효성 검사 성공"`
    - 실패 시: `status="validation_failed"`, `error_sections`에 섹션별로 그룹화된 에러 목록 포함
      - "분류체계 데이터 유효성 검사" 섹션
      - "PLC Ladder 파일 유효성 검사" 섹션
    
    **예외 상황:**
    - `PROGRAM_REGISTRATION_ERROR`: 등록 처리 중 오류
    - 유효성 검사 실패: 에러 목록이 `validation_result.errors`에 포함
    """,
)
async def register_program(
    ladder_zip: UploadFile = File(..., description="PLC ladder logic ZIP 파일", example="ladder_files.zip"),
    template_xlsx: UploadFile = File(
        ..., description="템플릿 분류체계 데이터 XLSX 파일", example="template.xlsx"
    ),
    comment_csv: UploadFile = File(..., description="PLC Ladder Comment CSV 파일", example="comment.csv"),
    program_title: str = Form(..., description="PGM Name (프로그램 제목)", example="공정1 PLC 프로그램"),
    process_id: str = Form(..., description="공정 ID (드롭다운 선택, 필수)", example="process_001"),
    program_description: Optional[str] = Form(None, description="프로그램 설명", example="공정1 라인용 PLC 프로그램"),
    user_id: str = Form(default="user", description="사용자 ID", example="user001"),
    program_service: ProgramService = Depends(get_program_service),
):
    """
    프로그램 등록 API

    - ladder_zip: PLC ladder logic 파일들이 포함된 압축 파일
    - template_xlsx: 템플릿 분류체계 데이터 (로직 파일명 포함)
    - comment_csv: ladder 로직에 있는 device 설명

    유효성 검사를 통과하면:
    1. S3에 파일 업로드 및 ZIP 압축 해제 (비동기)
    2. 백엔드 DB에 메타데이터 저장 (비동기)
    3. Vector DB 인덱싱 요청 (비동기)
    """
    # Service Layer에서 전파된 HandledException을 그대로 전파
    # Global Exception Handler가 자동으로 처리

    result = await program_service.register_program(
        program_title=program_title,
        process_id=process_id,
        program_description=program_description,
        user_id=user_id,
        ladder_zip=ladder_zip,
        template_xlsx=template_xlsx,
        comment_csv=comment_csv,
    )

    # 유효성 검사 결과 구성
    validation_result = None
    if result.get("is_valid") and result.get("warnings"):
        validation_result = ProgramValidationResult(
            is_valid=True,
            errors=result.get("errors", []),
            error_sections=None,
            warnings=result.get("warnings", []),
            checked_files=result.get("checked_files", []),
        )
    elif not result.get("is_valid"):
        validation_result = ProgramValidationResult(
            is_valid=False,
            errors=result.get("errors", []),
            error_sections=result.get("error_sections"),  # 섹션별 그룹화된 에러
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
    
    **화면 용도:**
    - PLC-PGM 매핑 화면의 PGM 프로그램 테이블
    - PGM 등록 화면의 프로그램 목록 테이블
    
    **검색 기능:**
    - `program_id`: PGM ID로 정확한 검색
    - `program_name`: 제목으로 부분 일치 검색
    
    **필터링 기능:**
    - `process_id`: 공정 ID로 필터링 (드롭다운 선택)
    - `status`: 등록 상태로 필터링
      - `preparing`: 준비 중
      - `uploading`: 업로드 중
      - `processing`: 처리 중
      - `embedding`: 임베딩 중
      - `completed`: 성공
      - `failed`: 실패
      - `indexing_failed`: 인덱싱 실패
    - `create_user`: 작성자로 필터링
    
    **권한 기반 필터링:**
    - `user_id`: 사용자 ID (선택사항)
    - `user_id`가 제공된 경우: 사용자의 권한 그룹에 따라 접근 가능한 공정의 PGM만 조회
      - super 권한 그룹: 모든 공정의 PGM 조회 가능
      - plc 권한 그룹: 지정된 공정의 PGM만 조회 가능
      - 권한이 없으면 빈 결과 반환
    - `user_id`가 없는 경우: 모든 프로그램 조회 (권한 필터링 없음)
    
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
    - 전체 목록 (권한 필터링): `GET /v1/programs?user_id=user001&page=1&page_size=10`
    - 전체 목록 (권한 필터링 없음): `GET /v1/programs?page=1&page_size=10`
    - 공정별 필터링: `GET /v1/programs?user_id=user001&process_id=process001`
    - PGM ID 검색: `GET /v1/programs?user_id=user001&program_id=PGM_000001`
    - PGM Name 검색: `GET /v1/programs?user_id=user001&program_name=라벨부착`
    - 상태별 필터링: `GET /v1/programs?user_id=user001&status=completed`
    - 복합 검색 및 정렬: `GET /v1/programs?user_id=user001&process_id=process001&program_name=라벨부착&status=completed&sort_by=create_dt&sort_order=desc&page=1&page_size=20`
    
    **주의사항:**
    - `user_id`가 제공되면 권한 기반 필터링이 적용됩니다
    - `user_id`가 없으면 모든 프로그램을 조회합니다 (권한 필터링 없음)
    """,
)
def get_program_list(
    program_id: Optional[str] = Query(None, description="PGM ID로 검색", example="pgm001"),
    program_name: Optional[str] = Query(None, description="제목으로 검색", example="공정1"),
    process_id: Optional[str] = Query(None, description="공정 ID로 필터링 (드롭다운 선택)", example="process_001"),
    status_filter: Optional[str] = Query(
        None, description="등록 상태로 필터링 (preparing, uploading, processing, embedding, completed, failed, indexing_failed)", alias="status", example="completed"
    ),
    create_user: Optional[str] = Query(None, description="작성자로 필터링", example="user001"),
    user_id: Optional[str] = Query(None, description="사용자 ID (권한 기반 필터링용, 선택사항)", example="user001"),
    page: int = Query(1, ge=1, description="페이지 번호", example=1),
    page_size: int = Query(10, ge=1, le=10000, description="페이지당 항목 수 (페이지네이션 없이 모든 데이터를 가져오려면 큰 값 사용, 예: 10000)", example=10),
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

    화면: PLC-PGM 매핑 화면, PGM 등록 화면의 프로그램 목록 테이블
    - PGM ID, 제목으로 검색
    - 공정, 등록 상태, 작성자로 필터링
    - 사용자 권한 기반 필터링 (user_id 선택사항)
    - 페이지네이션 및 정렬 지원
    """
    try:
        program_crud = ProgramCRUD(db)
        programs, total_count = program_crud.get_programs(
            program_id=program_id,
            program_name=program_name,
            process_id=process_id,
            status=status_filter,
            create_user=create_user,
            user_id=user_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Program의 process_id로 ProcessMaster 조인하여 공정 정보 조회
        from src.database.models.master_models import ProcessMaster
        
        process_ids = {p.process_id for p in programs if p.process_id}
        process_name_map = {}
        if process_ids:
            processes = (
                db.query(ProcessMaster)
                .filter(ProcessMaster.process_id.in_(process_ids))
                .filter(ProcessMaster.is_active.is_(True))
                .all()
            )
            
            for process in processes:
                process_name_map[process.process_id] = process.process_name

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

            # 공정명 조회 (Program.process_id 사용)
            process_name = process_name_map.get(program.process_id) if program.process_id else None

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


@router.get(
    "/{program_id}",
    response_model=Optional[ProgramInfo],
    summary="프로그램 상세 정보 조회",
    description="""
    프로그램의 상세 정보를 조회합니다 (팝업 상세 조회용).
    
    **화면 용도:** PGM 등록 목록에서 항목 선택 시 팝업으로 표시되는 상세 정보
    
    **응답 데이터:**
    - 기본 정보: PGM ID, PGM Name, 공정, 상태 등
    - 파일 정보: Logic 분류 체계 파일, Logic 파일, Comment 파일
      - 각 파일의 원본 파일명, 파일 크기, 확장자
      - 다운로드 링크 생성용 `download_file_type` 포함
    
    **파일 다운로드:**
    - 응답의 `files` 배열에서 각 파일 정보 확인
    - 각 파일의 `download_file_type`과 `program_id`를 사용하여 다운로드 링크 생성
    - 다운로드 API: `GET /programs/files/download?file_type={download_file_type}&program_id={program_id}&user_id={user_id}`
    - 예시:
      ```
      GET /v1/programs/files/download?file_type=program_classification&program_id=PGM_000001&user_id=user001
      GET /v1/programs/files/download?file_type=program_logic&program_id=PGM_000001&user_id=user001
      GET /v1/programs/files/download?file_type=program_comment&program_id=PGM_000001&user_id=user001
      ```
    
    **응답:**
    - 검색 결과가 없으면 200 OK와 함께 null을 반환합니다 (REST API 규칙).
    - 검색 결과가 있으면 프로그램 상세 정보를 반환합니다.
    
    **예외 상황:**
    - `CHAT_ACCESS_DENIED`: 접근 권한 없음
    """,
)
async def get_program(
    program_id: str,
    user_id: str = Query(default="user", description="사용자 ID"),
    program_service: ProgramService = Depends(get_program_service),
):
    """프로그램 상세 정보 조회 (팝업용)"""
    program = await program_service.get_program(program_id, user_id)
    # 검색 결과가 비어 있어도 200 OK 반환 (REST API 규칙)
    if program is None:
        return None
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


