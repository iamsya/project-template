# _*_ coding: utf-8 _*_
"""PLC Management API endpoints."""
import io
import logging
import zipfile
from typing import List, Optional

import pandas as pd
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
from sqlalchemy.orm import Session
from src.core.dependencies import (
    get_accessible_process_ids_dependency,
    get_db,
    get_user_id_dependency,
    get_user_name,
)
from src.core.permissions import check_any_role_dependency, is_process_accessible
from src.database.crud.plc_crud import PLCCRUD
from src.types.request.plc_request import (
    PLCBatchCreateRequest,
    PLCBatchUpdateRequest,
    PLCDeleteRequest,
    PLCMappingRequest,
)
from src.types.response.exceptions import HandledException
from src.types.response.plc_response import (
    PLCBasicInfo,
    PLCBatchCreateResponse,
    PLCBatchUpdateResponse,
    PLCDeleteResponse,
    PLCListItem,
    PLCListResponse,
    PLCMappingResponse,
    PLCTreeResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/plcs", tags=["plc-management"])


# 구체적인 경로는 동적 경로보다 먼저 정의해야 함 (FastAPI 경로 매칭 순서)
# 동적 경로(/{plc_uuid})는 모든 구체적인 경로 다음에 정의


@router.get(
    "",
    response_model=PLCListResponse,
    summary="PLC 기준 정보 목록 조회",
    description="""
    PLC 기준 정보 목록을 검색, 필터링, 페이지네이션, 정렬 기능으로 조회합니다.
    
    **화면 용도:**
    - PLC-PGM 매핑 화면의 PLC 기준 정보 테이블
    - PLC 등록 화면의 PLC 기준 정보 테이블
    
    **권한 기반 필터링:**
    - `user_id`: 사용자 ID (필수)
      - 시스템 관리자/통합 관리자: 모든 공정의 PLC 조회 가능
      - 공정 관리자: 지정된 공정의 PLC만 조회 가능
      - 일반 사용자: 접근 불가 (403 에러)
    
    **필터링 기능:**
    - `plant_id`: Plant ID로 필터링
    - `process_id`: 공정 ID로 필터링 (접근 가능한 공정만)
    - `line_id`: Line ID로 필터링
    - `program_name`: PGM명으로 필터링 (부분 일치)
    
    **검색 기능:**
    - `plc_id`: PLC ID로 검색 (부분 일치)
    - `plc_name`: PLC 명으로 검색 (부분 일치)
    
    **페이지네이션:**
    - `page`: 페이지 번호 (기본값: 1, 최소: 1)
    - `page_size`: 페이지당 항목 수 (기본값: 10, 최소: 1, 최대: 100)
    
    **정렬:**
    - `sort_by`: 정렬 기준 (기본값: `plc_id`)
      - `plc_id`: PLC ID
      - `plc_name`: PLC 명
      - `create_dt`: 생성일시
    - `sort_order`: 정렬 순서 (기본값: `asc`)
      - `asc`: 오름차순
      - `desc`: 내림차순
    
    **응답 데이터:**
    - PLC 목록 (ID, PLC ID, PLC 명, 계층 구조 정보, 매핑된 PGM ID, 매핑 정보 등)
    - 전체 개수 및 페이지 정보
    
    **사용 예시:**
    - 전체 목록: `GET /v1/plcs?user_id=user001&page=1&page_size=10`
    - 계층별 필터링: `GET /v1/plcs?user_id=user001&plant_id=KY1&process_id=process001&line_id=line001`
    - PLC ID 검색: `GET /v1/plcs?user_id=user001&plc_id=M1CFB01000`
    - PLC 명 검색: `GET /v1/plcs?user_id=user001&plc_name=CELL_FABRICATOR`
    - PGM명 필터링: `GET /v1/plcs?user_id=user001&program_name=라벨부착`
    - 복합 검색 및 정렬: `GET /v1/plcs?user_id=user001&plant_id=KY1&process_id=process001&program_name=라벨부착&sort_by=plc_id&sort_order=desc&page=1&page_size=20`
    """,
)
def get_plc_list(
    plant_id: Optional[str] = Query(
        None, description="Plant ID로 필터링", example="plant001"
    ),
    process_id: Optional[str] = Query(
        None, description="공정 ID로 필터링 (접근 가능한 공정만)", example="process001"
    ),
    line_id: Optional[str] = Query(
        None, description="Line ID로 필터링", example="line001"
    ),
    plc_id: Optional[str] = Query(None, description="PLC ID로 검색", example="plc001"),
    plc_name: Optional[str] = Query(
        None, description="PLC 명으로 검색", example="PLC001"
    ),
    program_name: Optional[str] = Query(
        None, description="PGM명으로 필터링", example="라벨부착"
    ),
    page: int = Query(1, ge=1, description="페이지 번호", example=1),
    page_size: int = Query(
        10,
        ge=1,
        le=10000,
        description="페이지당 항목 수 (페이지네이션 없이 모든 데이터를 가져오려면 큰 값 사용, 예: 10000)",
        example=10,
    ),
    sort_by: str = Query(
        "plc_id",
        description="정렬 기준 (plc_id, plc_name, create_dt)",
        example="plc_id",
    ),
    sort_order: str = Query("asc", description="정렬 순서 (asc, desc)", example="asc"),
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC 기준 정보 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

    화면: PLC-PGM 매핑 화면, PLC 등록 화면의 PLC 기준 정보 테이블
    - Plant, 공정, Line, PLC ID, PLC 명으로 검색/필터링
    - PGM명으로 필터링 (매핑된 PGM 기준)
    - 매핑된 PGM ID, 등록자(매핑일시) 표시
    - 권한 기반 공정 필터링 적용
    """
    try:

        # process_id가 제공된 경우, 접근 가능한 공정인지 확인
        if process_id:
            if not is_process_accessible(process_id, accessible_process_ids):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"공정 '{process_id}'에 접근할 권한이 없습니다.",
                )

        # 접근 가능한 공정만 필터링 (process_id가 제공되지 않은 경우)
        # accessible_process_ids가 None이면 모든 공정, 리스트면 해당 공정만
        plc_crud = PLCCRUD(db)
        plcs, total_count = plc_crud.get_plcs(
            plant_id=plant_id,
            process_id=process_id,
            line_id=line_id,
            plc_id=plc_id,
            plc_name=plc_name,
            program_name=program_name,
            accessible_process_ids=accessible_process_ids,  # 권한 기반 필터링
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # PLC의 mapping_user로 User 조인하여 매핑 사용자 정보 조회
        from src.database.models.user_models import User

        mapping_user_ids = {p.mapping_user for p in plcs if p.mapping_user}
        mapping_user_map = {}  # user_id -> User 객체 매핑
        if mapping_user_ids:
            users = (
                db.query(User)
                .filter(User.user_id.in_(mapping_user_ids))
                .filter(User.is_deleted.is_(False))
                .all()
            )

            for user in users:
                mapping_user_map[user.user_id] = user

        # Master 테이블과 조인하여 계층 구조 정보 조회
        items = []
        for plc in plcs:
            # 직접 필드로 계층 구조 정보 조회
            hierarchy_ids = {
                "plant_id": plc.plant_id,
                "process_id": plc.process_id,
                "line_id": plc.line_id,
            }
            # 계층 구조 정보 조회
            hierarchy = None
            if any(hierarchy_ids.values()):
                hierarchy = plc_crud._get_hierarchy_with_names(hierarchy_ids)

            items.append(
                PLCListItem(
                    plc_uuid=plc.plc_uuid,
                    plc_id=plc.plc_id,
                    plc_name=plc.plc_name,
                    plant=hierarchy.get("plant", {}).get("name") if hierarchy else None,
                    plant_id=plc.plant_id,
                    process=(
                        hierarchy.get("process", {}).get("name") if hierarchy else None
                    ),
                    process_id=plc.process_id,
                    line=hierarchy.get("line", {}).get("name") if hierarchy else None,
                    line_id=plc.line_id,
                    unit=plc.unit,
                    program_id=plc.program_id,
                    mapping_user=plc.mapping_user,
                    mapping_user_name=(
                        mapping_user_map.get(plc.mapping_user).name
                        if plc.mapping_user and mapping_user_map.get(plc.mapping_user)
                        else None
                    ),
                    mapping_dt=plc.mapping_dt,
                )
            )

        total_pages = (total_count + page_size - 1) // page_size

        return PLCListResponse(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    except Exception as e:
        logger.error("PLC 목록 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 목록 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.put(
    "/mapping",
    response_model=PLCMappingResponse,
    summary="PLC-PGM 매핑 저장",
    description="""
    여러 PLC에 각각 다른 PGM 프로그램을 매핑합니다.
    
    **화면 용도:** PLC 관리 화면의 매핑 저장 기능
    
    **주요 기능:**
    - 여러 매핑 항목을 한 번에 처리
    - 각 항목마다 여러 PLC에 동일한 PGM 프로그램 매핑 가능
    - 이전 매핑 정보를 `previous_program_id`에 저장 (히스토리 관리)
    - 매핑 일시 기록
    
    **요청 파라미터:**
    - `items`: PLC-PGM 매핑 항목 리스트
      - `plc_uuids`: 매핑할 PLC UUID 리스트 (배열)
      - `program_id`: 매핑할 PGM 프로그램 ID
    
    **요청 예시:**
    ```json
    {
      "items": [
        {"plc_uuids": ["uuid1", "uuid2"], "program_id": "pgm1"},
        {"plc_uuids": ["uuid3"], "program_id": "pgm2"}
      ]
    }
    ```
    
    **응답:**
    - `success`: 전체 성공 여부
    - `mapped_count`: 성공적으로 매핑된 PLC 개수
    - `failed_count`: 매핑 실패한 PLC 개수
    - `errors`: 실패한 PLC의 오류 정보 리스트
    
    **처리 로직:**
    1. 각 PLC의 현재 `program_id`를 `previous_program_id`에 저장
    2. 새로운 `program_id`로 업데이트
    3. `mapping_dt` 업데이트
    
    **예외 상황:**
    - PLC를 찾을 수 없는 경우: 해당 PLC는 실패 처리
    - PGM 프로그램을 찾을 수 없는 경우: 해당 PLC는 실패 처리
    """,
)
def update_plc_program_mapping(
    request_body: PLCMappingRequest,
    db: Session = Depends(get_db),
    check_user_id: str = Depends(get_user_id_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC-PGM 매핑 저장

    여러 매핑 항목을 한 번에 처리합니다.

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정의 PLC 매핑 가능
    - 공정 관리자: 지정된 공정의 PLC만 매핑 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        # 권한 체크 (일반 사용자 제외)
        from src.core.permissions import check_any_role

        check_any_role(check_user_id, db)

        # SSO 사용 여부에 따라 사용자 이름 가져오기
        mapping_user = get_user_name(
            user_id=check_user_id,
            db=db,
            default="user",
        )

        plc_crud = PLCCRUD(db)
        success_count = 0
        failed_count = 0
        errors = []

        # 각 매핑 항목 처리
        for item in request_body.items:
            try:
                # 매핑할 PLC들의 process_id 권한 체크
                plcs_to_check = [plc_crud.get_plc(uuid) for uuid in item.plc_uuids]
                for plc in plcs_to_check:
                    if plc and plc.process_id:
                        if not is_process_accessible(
                            plc.process_id, accessible_process_ids
                        ):
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=(
                                    f"PLC '{plc.plc_id}'의 공정 "
                                    f"'{plc.process_id}'에 접근할 권한이 없습니다."
                                ),
                            )

                result = plc_crud.update_plc_program_mapping(
                    plc_uuids=item.plc_uuids,
                    program_id=item.program_id,
                    mapping_user=mapping_user,  # SSO 여부에 따라 자동 처리
                )
                success_count += result["success_count"]
                failed_count += result["failed_count"]
                errors.extend(result["errors"])
            except Exception as e:
                failed_count += len(item.plc_uuids)
                errors.append(f"매핑 항목 처리 실패: {str(e)}")
                logger.warning(f"매핑 항목 처리 실패: {str(e)}")

        return PLCMappingResponse(
            success=failed_count == 0,
            mapped_count=success_count,
            failed_count=failed_count,
            errors=errors,
        )
    except Exception as e:
        logger.error("PLC-PGM 매핑 저장 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC-PGM 매핑 저장 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get(
    "/tree",
    response_model=PLCTreeResponse,
    summary="PLC Tree 구조 조회",
    description="""
    채팅 메뉴에서 PLC를 선택하기 위한 Tree 구조를 조회합니다.
    
    **Hierarchy 구조:**
    - Plant → 공정(Process) → Line → PLC명 → 호기(Unit) → PLC ID
    
    **테이블 스키마:**
    - PLANT_ID (Plant, 마스터 데이터)
    - PROCESS_ID (공정, 마스터 데이터)
    - LINE_ID (Line, 마스터 데이터)
    - PLC_NAME (PLC명, 사용자 입력)
    - UNIT (호기, 사용자 입력)
    - PLC_ID (PLC ID, 사용자 입력)
    
    **응답 구조:**
    ```json
    {
      "data": [
        {
          "plant": "Plant1",
          "procList": [
            {
              "proc": "Process1",
              "lineList": [
                {
                  "line": "Line1",
                  "plcNameList": [
                    {
                      "plcName": "PLC_NAME1",
                      "unitList": [
                        {
                          "unit": "1",
                          "info": [
                            {
                              "plc_id": "PLC001",
                              "plc_uuid": "uuid",
                              "create_dt": "2025/10/31 18:39",
                              "user": "admin"
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    }
    ```
    
    **특징:**
    - 활성화된 PLC만 조회 (is_active=true)
    - program_id가 있는 PLC만 조회 (프로그램이 매핑된 PLC만)
    - 활성화된 Plant, Process, Line만 조회
    - 정렬 순서: Plant → Process → Line → PLC명 → 호기
    """,
)
def get_plc_tree(
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC Tree 구조 조회 (채팅 메뉴에서 PLC 선택용)

    Hierarchy: Plant → 공정 → Line → PLC명 → 호기 → PLC ID

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정의 PLC 조회 가능
    - 공정 관리자: 지정된 공정의 PLC만 조회 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        plc_crud = PLCCRUD(db)
        tree_data = plc_crud.get_plc_tree(accessible_process_ids=accessible_process_ids)

        return PLCTreeResponse(data=tree_data)
    except Exception as e:
        logger.error("PLC Tree 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC Tree 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.delete(
    "",
    response_model=PLCDeleteResponse,
    summary="PLC 삭제 (단일/일괄)",
    description="""
    PLC를 삭제합니다 (소프트 삭제). 단일 또는 여러 PLC를 일괄 삭제할 수 있습니다.
    
    **화면 용도:** PLC 등록 화면에서 PLC 삭제 (단일 또는 다중 선택)
    
    **삭제 방식:**
    - 소프트 삭제: `is_deleted = True`로 설정
    - `deleted_at`에 삭제 일시 저장
    - `deleted_by`에 삭제자 저장
    - 매핑된 `program_id` 제거 (None으로 설정)
    - 실제 데이터는 삭제되지 않음
    
    **단일/일괄 삭제:**
    - `plc_uuids` 배열에 1개만 넣으면 단일 삭제
    - `plc_uuids` 배열에 여러 개를 넣으면 일괄 삭제
    
    **주의사항:**
    - PLC 삭제 시 매핑된 PGM ID도 함께 해제됩니다.
    
    **요청 파라미터:**
    - `plc_uuids`: 삭제할 PLC UUID 리스트 (1개 이상)
    - `delete_user`: 삭제 사용자
    
    """,
)
def delete_plcs(
    request_body: PLCDeleteRequest,
    db: Session = Depends(get_db),
    check_user_id: str = Depends(get_user_id_dependency),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC 일괄 삭제

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정의 PLC 삭제 가능
    - 공정 관리자: 지정된 공정의 PLC만 삭제 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        plc_crud = PLCCRUD(db)

        # 삭제할 PLC들의 process_id 권한 체크
        plcs_to_check = [plc_crud.get_plc(uuid) for uuid in request_body.plc_uuids]
        for plc in plcs_to_check:
            if plc and plc.process_id:
                if not is_process_accessible(plc.process_id, accessible_process_ids):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=(
                            f"PLC '{plc.plc_id}'의 공정 "
                            f"'{plc.process_id}'에 접근할 권한이 없습니다."
                        ),
                    )

        # PLC 일괄 삭제
        deleted_count = plc_crud.delete_plcs(
            plc_uuids=request_body.plc_uuids, delete_user=check_user_id
        )

        return PLCDeleteResponse(
            success=True,
            deleted_count=deleted_count,
            message=f"{deleted_count}개의 PLC가 성공적으로 삭제되었습니다.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PLC 일괄 삭제 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 일괄 삭제 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.post(
    "/batch",
    response_model=PLCBatchCreateResponse,
    summary="PLC 다건 저장",
    description="""
    여러 PLC를 일괄 생성합니다.
    
    **화면 용도:** PLC 등록 화면에서 새 PLC 추가 시
    
    **요청 파라미터:**
    - `items`: 생성할 PLC 목록
      - 각 항목: `plant_id`, `process_id`, `line_id`, `plc_name`, `unit`, `plc_id`, `create_user`
    
    **응답:**
    - 성공 시: `message="PLC가 생성되었습니다."`
    - 실패 시: `message="일부 항목 생성 중 오류가 발생했습니다."` + `errors` 배열
    
    **예외 상황:**
    - 중복된 PLC ID: 해당 항목만 실패 처리
    - 존재하지 않는 Plant/Process/Line ID: 해당 항목만 실패 처리
    """,
)
def batch_create_plcs(
    request_body: PLCBatchCreateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC 다건 저장 (생성)

    새 PLC 추가 시 호출되는 API입니다.

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정에 PLC 생성 가능
    - 공정 관리자: 지정된 공정에만 PLC 생성 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        plc_crud = PLCCRUD(db)
        from src.database.crud.master_crud import (
            LineMasterCRUD,
            PlantMasterCRUD,
            ProcessMasterCRUD,
        )

        plant_crud = PlantMasterCRUD(db)
        process_crud = ProcessMasterCRUD(db)
        line_crud = LineMasterCRUD(db)

        created_count = 0
        failed_count = 0
        errors = []

        for item in request_body.items:
            try:
                # process_id 기반 권한 체크
                if not is_process_accessible(item.process_id, accessible_process_ids):
                    error_msg = (
                        f"PLC ID {item.plc_id}: "
                        f"공정 '{item.process_id}'에 접근할 권한이 없습니다."
                    )
                    errors.append(error_msg)
                    failed_count += 1
                    continue

                # 마스터 데이터 유효성 검사
                plant = plant_crud.get_plant(item.plant_id)
                if not plant:
                    errors.append(f"PLC ID {item.plc_id}: 존재하지 않는 Plant ID입니다")
                    failed_count += 1
                    continue

                process = process_crud.get_process(item.process_id)
                if not process:
                    errors.append(f"PLC ID {item.plc_id}: 존재하지 않는 공정 ID입니다")
                    failed_count += 1
                    continue

                line = line_crud.get_line(item.line_id)
                if not line:
                    errors.append(f"PLC ID {item.plc_id}: 존재하지 않는 Line ID입니다")
                    failed_count += 1
                    continue

                # PLC 생성
                try:
                    plc_crud.create_plc(
                        plant_id=item.plant_id,
                        process_id=item.process_id,
                        line_id=item.line_id,
                        plc_name=item.plc_name,
                        plc_id=item.plc_id,
                        create_user=item.create_user,
                        unit=item.unit,
                    )
                    created_count += 1
                except HandledException as e:
                    error_detail = e.msg_only or str(e)
                    error_msg = f"PLC ID {item.plc_id}: {error_detail}"
                    errors.append(error_msg)
                    failed_count += 1

            except Exception as e:
                errors.append(f"PLC ID {item.plc_id}: {str(e)}")
                failed_count += 1

        # 성공 메시지 결정
        if failed_count == 0:
            message = f"{created_count}개의 PLC가 생성되었습니다."
        else:
            message = "일부 항목 생성 중 오류가 발생했습니다."

        return PLCBatchCreateResponse(
            success=failed_count == 0,
            message=message,
            created_count=created_count,
            failed_count=failed_count,
            errors=errors,
        )
    except Exception as e:
        logger.error("PLC 다건 저장 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 다건 저장 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.post(
    "/upload-excel",
    response_model=PLCBatchCreateResponse,
    summary="PLC 엑셀 업로드",
    description="""
    엑셀 파일을 업로드하여 PLC 데이터를 일괄 등록합니다.
    
    **엑셀 파일 형식:**
    - 헤더: 번호, Plant, 공정, Line, 장비명 - 실 사용, 호기, PLC ID
    - Plant, 공정, Line은 이름으로 입력하며, 시스템에서 ID를 자동으로 조회합니다.
    
    **매핑 규칙:**
    - Plant (이름) → PlantMaster에서 조회 → plant_id 사용
    - 공정 (이름) → ProcessMaster에서 조회 → process_id 사용
    - Line (이름) → LineMaster에서 조회 → line_id 사용
    - 장비명 - 실 사용 → plc_name
    - 호기 → unit
    - PLC ID → plc_id (공백이면 해당 행 무시)
    
    **주의사항:**
    - PLC ID가 공백인 행은 건너뜁니다.
    - Plant, 공정, Line 이름이 존재하지 않으면 해당 행은 실패 처리됩니다.
    - 중복된 PLC ID가 있으면 해당 행은 실패 처리됩니다.
    """,
)
def upload_plc_excel(
    excel_file: UploadFile = File(
        ..., description="PLC 데이터 엑셀 파일 (XLSX)", example="plc_data.xlsx"
    ),
    create_user: str = Form(..., description="생성 사용자", example="user001"),
    db: Session = Depends(get_db),
):
    """
    PLC 엑셀 업로드 API

    엑셀 파일을 파싱하여 PLC 데이터를 일괄 등록합니다.
    """
    try:
        # 엑셀 파일 읽기
        excel_file.file.seek(0)
        excel_content = excel_file.file.read()
        excel_file.file.seek(0)

        # 파일이 비어있는지 확인
        if not excel_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="업로드된 파일이 비어있습니다.",
            )

        # 파일 확장자 확인
        filename = excel_file.filename or ""
        if filename and not filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"엑셀 파일 형식이 아닙니다. 파일명: {filename}",
            )

        # XLSX 파일인 경우 ZIP 형식인지 확인 (XLSX는 ZIP 압축된 XML 파일)
        is_xlsx = filename.lower().endswith(".xlsx")
        if is_xlsx:
            try:
                is_zip = zipfile.is_zipfile(io.BytesIO(excel_content))
                if not is_zip:
                    logger.warning(
                        "XLSX 파일이 ZIP 형식이 아닙니다. "
                        "파일명: %s, 파일 크기: %d bytes",
                        filename,
                        len(excel_content),
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=(
                            "파일이 올바른 XLSX 형식이 아닙니다. "
                            "다음 사항을 확인해주세요:\n"
                            "1. 파일이 암호화되어 있지 않은지 확인 (암호화된 파일은 지원하지 않습니다)\n"
                            "2. 파일이 손상되지 않았는지 확인\n"
                            "3. 파일이 실제로 XLSX 형식인지 확인 (다른 형식을 .xlsx로 저장한 경우)\n"
                            "4. 파일을 다시 저장하여 업로드해보세요"
                        ),
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.warning(
                    "ZIP 형식 확인 중 오류: %s, 파일명: %s", str(e), filename
                )

        # pandas로 엑셀 파일 파싱
        try:
            # XLSX 파일인 경우 openpyxl, XLS 파일인 경우 xlrd 사용
            if filename.lower().endswith(".xls"):
                df = pd.read_excel(io.BytesIO(excel_content), header=0, engine="xlrd")
            else:
                df = pd.read_excel(
                    io.BytesIO(excel_content), header=0, engine="openpyxl"
                )
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(
                "엑셀 파일 파싱 실패: 파일명=%s, 오류 타입=%s, 메시지=%s",
                filename,
                error_type,
                error_msg,
            )

            if (
                "not a zip file" in error_msg.lower()
                or "badzipfile" in error_msg.lower()
                or "zipfile" in error_type.lower()
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "파일이 올바른 XLSX 형식이 아닙니다. "
                        "다음 사항을 확인해주세요:\n"
                        "1. 파일이 암호화되어 있지 않은지 확인 (암호화된 파일은 지원하지 않습니다)\n"
                        "2. 파일이 손상되지 않았는지 확인\n"
                        "3. 파일이 실제로 XLSX 형식인지 확인\n"
                        "4. 파일을 다시 저장하여 업로드해보세요"
                    ),
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"엑셀 파일 파싱 실패: {error_msg}",
            )

        # 필수 컬럼 확인
        required_columns = ["Plant", "공정", "Line", "장비명 - 실 사용", "PLC ID"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"필수 컬럼이 없습니다: {', '.join(missing_columns)}. "
                    f"현재 컬럼: {', '.join(df.columns.tolist())}"
                ),
            )

        # CRUD 인스턴스 생성
        plc_crud = PLCCRUD(db)
        from src.database.crud.master_crud import (
            LineMasterCRUD,
            PlantMasterCRUD,
            ProcessMasterCRUD,
        )

        plant_crud = PlantMasterCRUD(db)
        process_crud = ProcessMasterCRUD(db)
        line_crud = LineMasterCRUD(db)

        created_count = 0
        failed_count = 0
        skipped_count = 0
        errors = []

        # Plant, 공정, Line 이름으로 ID 조회 캐시 (성능 최적화)
        plant_name_to_id = {}
        process_name_to_id = {}
        line_name_to_id = {}

        # 모든 활성 Plant 조회
        all_plants = plant_crud.get_all_plants(include_inactive=False)
        plant_name_to_id = {plant.plant_name: plant.plant_id for plant in all_plants}

        # 모든 활성 Process 조회
        all_processes = process_crud.get_all_processes(include_inactive=False)
        process_name_to_id = {
            process.process_name: process.process_id for process in all_processes
        }

        # 모든 활성 Line 조회
        all_lines = line_crud.get_all_lines(include_inactive=False)
        line_name_to_id = {line.line_name: line.line_id for line in all_lines}

        # 각 행 처리
        for idx, row in df.iterrows():
            try:
                # PLC ID 확인 (공백 허용)
                plc_id_raw = row.get("PLC ID", "")
                if pd.notna(plc_id_raw):
                    plc_id = str(plc_id_raw).strip()
                    if plc_id == "nan":
                        plc_id = ""
                else:
                    plc_id = ""

                # PLC ID가 있는 경우에만 중복 확인 (스킵)
                if plc_id:
                    existing_plc = plc_crud.get_plc_by_plc_id(plc_id)
                    if existing_plc:
                        skipped_count += 1
                        logger.info(
                            "행 %d (PLC ID: %s): 이미 존재하는 PLC이므로 스킵합니다.",
                            idx + 2,
                            plc_id,
                        )
                        continue

                # Plant 이름으로 ID 조회
                plant_name = str(row.get("Plant", "")).strip()
                if not plant_name or plant_name == "nan":
                    errors.append(f"행 {idx + 2}: Plant 이름이 없습니다.")
                    failed_count += 1
                    continue

                plant_id = plant_name_to_id.get(plant_name)
                if not plant_id:
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    errors.append(
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): "
                        f"Plant '{plant_name}'를 찾을 수 없습니다."
                    )
                    failed_count += 1
                    continue

                # 공정 이름으로 ID 조회
                process_name = str(row.get("공정", "")).strip()
                if not process_name or process_name == "nan":
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    errors.append(
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): 공정 이름이 없습니다."
                    )
                    failed_count += 1
                    continue

                process_id = process_name_to_id.get(process_name)
                if not process_id:
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    error_msg = (
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): "
                        f"공정 '{process_name}'를 찾을 수 없습니다."
                    )
                    errors.append(error_msg)
                    failed_count += 1
                    continue

                # Line 이름으로 ID 조회
                line_name = str(row.get("Line", "")).strip()
                if not line_name or line_name == "nan":
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    errors.append(
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): Line 이름이 없습니다."
                    )
                    failed_count += 1
                    continue

                line_id = line_name_to_id.get(line_name)
                if not line_id:
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    error_msg = (
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): "
                        f"Line '{line_name}'를 찾을 수 없습니다."
                    )
                    errors.append(error_msg)
                    failed_count += 1
                    continue

                # 장비명 - 실 사용
                plc_name = str(row.get("장비명 - 실 사용", "")).strip()
                if not plc_name or plc_name == "nan":
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    errors.append(
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): 장비명이 없습니다."
                    )
                    failed_count += 1
                    continue

                # 호기 (선택사항)
                unit = row.get("호기", "")
                if pd.notna(unit):
                    unit = str(unit).strip()
                    if unit == "nan" or unit == "":
                        unit = None
                else:
                    unit = None

                # PLC 생성 (기존 create_plc 함수 사용)
                try:
                    plc_crud.create_plc(
                        plant_id=plant_id,
                        process_id=process_id,
                        line_id=line_id,
                        plc_name=plc_name,
                        plc_id=plc_id,
                        create_user=create_user,
                        unit=unit,
                    )
                    created_count += 1
                except HandledException as e:
                    error_detail = e.msg_only or str(e)
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    error_msg = (
                        f"행 {idx + 2} (PLC ID: {plc_id_display}): {error_detail}"
                    )
                    errors.append(error_msg)
                    failed_count += 1
                except Exception as e:
                    plc_id_display = plc_id if plc_id else "(PLC ID 없음)"
                    error_msg = f"행 {idx + 2} (PLC ID: {plc_id_display}): {str(e)}"
                    errors.append(error_msg)
                    failed_count += 1

            except Exception as e:
                errors.append(f"행 {idx + 2}: 처리 중 오류 발생: {str(e)}")
                failed_count += 1

        # 성공 메시지 결정
        if failed_count == 0:
            if skipped_count > 0:
                message = (
                    f"{created_count}개의 PLC가 생성되었습니다. "
                    f"(이미 존재하는 {skipped_count}개는 스킵되었습니다)"
                )
            else:
                message = f"{created_count}개의 PLC가 생성되었습니다."
        else:
            if skipped_count > 0:
                message = (
                    f"{created_count}개 성공, {failed_count}개 실패, "
                    f"{skipped_count}개 스킵되었습니다."
                )
            else:
                message = f"{created_count}개 성공, {failed_count}개 실패했습니다."

        return PLCBatchCreateResponse(
            success=failed_count == 0,
            message=message,
            created_count=created_count,
            failed_count=failed_count,
            errors=errors,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("PLC 엑셀 업로드 실패: %s", str(e))
        error_detail = f"PLC 엑셀 업로드 중 오류가 발생했습니다: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        ) from e


@router.put(
    "/batch",
    response_model=PLCBatchUpdateResponse,
    summary="PLC 다건 수정",
    description="""
    여러 PLC를 일괄 수정합니다.
    
    **화면 용도:** PLC 등록 화면에서 기존 PLC 수정 시
    
    **요청 파라미터:**
    - `items`: 수정할 PLC 목록
      - 각 항목: `plc_uuid` (필수), `plant_id` (선택), `process_id` (선택), `line_id` (선택), `plc_name`, `unit`, `plc_id`, `update_user`
    
    **응답:**
    - 성공 시: `message="PLC가 수정되었습니다."`
    - 실패 시: `message="일부 항목 수정 중 오류가 발생했습니다."` + `errors` 배열
    
    **예외 상황:**
    - PLC를 찾을 수 없음: 해당 항목만 실패 처리
    - 중복된 PLC ID: 해당 항목만 실패 처리
    """,
)
def batch_update_plcs(
    request_body: PLCBatchUpdateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC 다건 수정

    기존 PLC 수정 시 호출되는 API입니다.

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정의 PLC 수정 가능
    - 공정 관리자: 지정된 공정의 PLC만 수정 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        plc_crud = PLCCRUD(db)
        from src.database.crud.master_crud import (
            LineMasterCRUD,
            PlantMasterCRUD,
            ProcessMasterCRUD,
        )

        plant_crud = PlantMasterCRUD(db)
        process_crud = ProcessMasterCRUD(db)
        line_crud = LineMasterCRUD(db)

        updated_count = 0
        failed_count = 0
        errors = []

        for item in request_body.items:
            try:
                # 기존 PLC 조회
                existing_plc = plc_crud.get_plc(item.plc_uuid)
                if not existing_plc:
                    errors.append(f"PLC UUID {item.plc_uuid}: PLC를 찾을 수 없습니다")
                    failed_count += 1
                    continue

                # process_id 변경 여부 확인 및 권한 체크
                target_process_id = (
                    item.process_id if item.process_id else existing_plc.process_id
                )
                if target_process_id:
                    if not is_process_accessible(
                        target_process_id, accessible_process_ids
                    ):
                        error_msg = (
                            f"PLC UUID {item.plc_uuid}: "
                            f"공정 '{target_process_id}'에 접근할 권한이 없습니다."
                        )
                        errors.append(error_msg)
                        failed_count += 1
                        continue

                # 마스터 데이터 유효성 검사 (plant_id, process_id, line_id가 제공된 경우)
                if item.plant_id:
                    plant = plant_crud.get_plant(item.plant_id)
                    if not plant:
                        errors.append(
                            f"PLC UUID {item.plc_uuid}: 존재하지 않는 Plant ID입니다"
                        )
                        failed_count += 1
                        continue

                if item.process_id:
                    process = process_crud.get_process(item.process_id)
                    if not process:
                        errors.append(
                            f"PLC UUID {item.plc_uuid}: 존재하지 않는 공정 ID입니다"
                        )
                        failed_count += 1
                        continue

                if item.line_id:
                    line = line_crud.get_line(item.line_id)
                    if not line:
                        errors.append(
                            f"PLC UUID {item.plc_uuid}: 존재하지 않는 Line ID입니다"
                        )
                        failed_count += 1
                        continue

                # PLC 수정
                updated_plc = plc_crud.update_plc(
                    plc_uuid=item.plc_uuid,
                    plc_name=item.plc_name,
                    unit=item.unit,
                    plc_id=item.plc_id,
                    update_user=item.update_user,
                    plant_id=item.plant_id,
                    process_id=item.process_id,
                    line_id=item.line_id,
                    program_id=item.program_id,
                )
                if updated_plc:
                    updated_count += 1
                else:
                    errors.append(f"PLC UUID {item.plc_uuid}: PLC를 찾을 수 없습니다")
                    failed_count += 1

            except HandledException as e:
                error_msg = f"PLC UUID {item.plc_uuid}: {e.msg or str(e)}"
                errors.append(error_msg)
                failed_count += 1
            except Exception as e:
                errors.append(f"PLC UUID {item.plc_uuid}: {str(e)}")
                failed_count += 1

        # 성공 메시지 결정
        if failed_count == 0:
            message = f"{updated_count}개의 PLC가 수정되었습니다."
        else:
            message = "일부 항목 수정 중 오류가 발생했습니다."

        return PLCBatchUpdateResponse(
            success=failed_count == 0,
            message=message,
            updated_count=updated_count,
            failed_count=failed_count,
            errors=errors,
        )
    except Exception as e:
        logger.error("PLC 다건 수정 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 다건 수정 중 오류가 발생했습니다: {str(e)}",
        ) from e


# ==========================================
# 동적 경로 (모든 구체적인 경로 다음에 정의)
# FastAPI는 위에서 아래로 경로를 매칭하므로,
# 구체적인 경로(/tree, /masters/dropdown 등)를 먼저 정의하고
# 동적 경로(/{plc_uuid})는 마지막에 정의해야 함
# ==========================================


@router.get("/{plc_uuid}", response_model=Optional[PLCBasicInfo])
def get_plc_by_id(
    plc_uuid: str,
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
    accessible_process_ids: Optional[List[str]] = Depends(
        get_accessible_process_ids_dependency
    ),
):
    """
    PLC 정보 조회 (PLC_UUID로)

    - plc_uuid: PLC의 UUID (Primary Key)
    - is_deleted가 false인 경우에만 조회합니다 (사용 중으로 인식).
    - 기본 정보만 반환합니다 (plc_uuid, plc_id, plc_name, 계층 구조, program_id).
    - 검색 결과가 없으면 200 OK와 함께 null을 반환합니다 (REST API 규칙).

    **권한 기반 필터링:**
    - 시스템 관리자/통합 관리자: 모든 공정의 PLC 조회 가능
    - 공정 관리자: 지정된 공정의 PLC만 조회 가능
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        # PLC 조회
        plc_crud = PLCCRUD(db)
        plc = plc_crud.get_plc(plc_uuid)

        # 검색 결과가 비어 있어도 200 OK 반환 (REST API 규칙)
        if not plc:
            return None

        # is_deleted 체크 (is_active는 deprecated)
        if plc.is_deleted:
            return None

        # 권한 체크: PLC의 process_id에 접근 권한이 있는지 확인
        if plc.process_id:
            if not is_process_accessible(plc.process_id, accessible_process_ids):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="PLC에 접근할 권한이 없습니다.",
                )

        # program_id 변경 여부 체크
        program_id_changed = (
            plc.previous_program_id is not None
            and plc.previous_program_id != plc.program_id
        )

        # 계층 구조 정보 조회
        hierarchy_ids = {
            "plant_id": plc.plant_id,
            "process_id": plc.process_id,
            "line_id": plc.line_id,
        }
        hierarchy = plc_crud._get_hierarchy_with_names(hierarchy_ids)

        return PLCBasicInfo(
            id=plc.plc_uuid,
            plc_id=plc.plc_id,
            plc_name=plc.plc_name,
            plant=hierarchy.get("plant", {}).get("name") if hierarchy else None,
            process=hierarchy.get("process", {}).get("name") if hierarchy else None,
            line=hierarchy.get("line", {}).get("name") if hierarchy else None,
            unit=plc.unit,
            program_id=plc.program_id,
            program_id_changed=program_id_changed,
            previous_program_id=plc.previous_program_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("PLC 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e
