# _*_ coding: utf-8 _*_
"""Master Data API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from src.core.dependencies import get_db
from src.core.permissions import check_any_role_dependency
from src.database.crud.master_crud import MasterHierarchyCRUD, ProcessMasterCRUD
from src.database.crud.program_crud import ProgramCRUD
from src.types.response.plc_response import MasterDropdownResponse, ProcessItem, ProcessListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/masters", tags=["master-data"])


@router.get(
    "",
    response_model=MasterDropdownResponse,
    summary="권한 기반 마스터 데이터 조회 (드롭다운용)",
    description="""
    사용자 권한에 따라 접근 가능한 마스터 데이터를 조회합니다.
    
    **화면 용도:** 
    - PLC 관리 화면의 Plant, 공정, Line 드롭다운
    - Program 등록 화면의 공정 드롭다운
    - PLC-PGM 매핑 화면의 드롭다운
    
    **권한 기반 필터링:**
    - `user_id`: 사용자 ID (필수)
      - 시스템 관리자/통합 관리자: 모든 활성 Process 반환
      - 공정 관리자: 지정된 Process만 반환
      - 일반 사용자: 접근 불가 (403 에러)
    - 계층 구조 포함 (processesByPlant, linesByProcess)
    
    **응답 구조:**
    ```json
    {
      "plants": [
        {"id": "plant_001", "code": "plant_001", "name": "Plant 1"}
      ],
      "processesByPlant": {
        "plant_001": [
          {"id": "process_001", "code": "process_001", "name": "모듈"},
          {"id": "process_002", "code": "process_002", "name": "전극"}
        ]
      },
      "linesByProcess": {
        "process_001": [
          {"id": "line_001", "code": "line_001", "name": "1라인"},
          {"id": "line_002", "code": "line_002", "name": "2라인"}
        ]
      }
    }
    ```
    
    **프론트엔드 사용 흐름:**
    1. API 호출: `GET /v1/masters?user_id=user001` (user_id 필수)
    2. Plant 드롭다운: `response.plants` 사용
    3. Plant 선택 시: `response.processesByPlant[selectedPlantId]` 사용
    4. Process 선택 시: `response.linesByProcess[selectedProcessId]` 사용
    
    **사용 예시:**
    ```
    GET /v1/masters?user_id=user001  # 권한 기반 필터링 (필수)
    ```
    """,
)
def get_masters_for_dropdown(
    request: Request,
    user_id: Optional[str] = Query(None, description="사용자 ID (SSO 미사용 시 필수)", example="user001"),
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
):
    """
    권한 기반 마스터 데이터 조회 (드롭다운용)
    
    사용자 권한에 따라 접근 가능한 공정만 포함하여 반환합니다.
    - 시스템 관리자/통합 관리자: 모든 활성 공정
    - 공정 관리자: 지정된 공정만
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        # request.state.user_id 우선 사용 (미들웨어에서 설정된 경우), 없으면 파라미터 user_id 사용 (테스트용)
        check_user_id = None
        if hasattr(request.state, "user_id") and request.state.user_id:
            check_user_id = request.state.user_id
        elif user_id:
            check_user_id = user_id
        
        if not check_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 ID가 필요합니다."
            )
        
        # 사용자 권한 기반 접근 가능한 공정 ID 목록 조회
        # None이면 모든 공정 접근 가능, List[str]이면 특정 공정만, []이면 접근 불가
        program_crud = ProgramCRUD(db)
        accessible_process_ids = program_crud.get_accessible_process_ids(check_user_id)

        # 권한 필터링된 마스터 데이터 조회
        master_crud = MasterHierarchyCRUD(db)
        masters = master_crud.get_masters_for_mapping_dropdown(
            accessible_process_ids
        )

        # code 필드 추가 (id를 code로 사용)
        plants = [
            {"id": p["id"], "code": p["id"], "name": p["name"]}
            for p in masters["plants"]
        ]

        processes_by_plant = {}
        for plant_id, process_list in masters["processesByPlant"].items():
            processes_by_plant[plant_id] = [
                {"id": p["id"], "code": p["id"], "name": p["name"]}
                for p in process_list
            ]

        lines_by_process = {}
        for process_id, line_list in masters["linesByProcess"].items():
            lines_by_process[process_id] = [
                {"id": line["id"], "code": line["id"], "name": line["name"]}
                for line in line_list
            ]

        return MasterDropdownResponse(
            plants=plants,
            processesByPlant=processes_by_plant,
            linesByProcess=lines_by_process,
        )
    except Exception as e:
        logger.error("마스터 데이터 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"마스터 데이터 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get(
    "/processes",
    response_model=ProcessListResponse,
    summary="공정 목록 조회",
    description="""
    공정 기준정보 목록을 조회합니다.
    
    **화면 용도:**
    - 그룹 관리 화면의 공정 선택 드롭다운
    - 공정 기준정보 관리 화면의 목록 표시
    - 공정별 통계 및 분석 화면
    
    **권한 기반 필터링:**
    - `user_id`: 사용자 ID (필수)
      - 시스템 관리자/통합 관리자: 모든 공정 반환
      - 공정 관리자: 지정된 공정만 반환
      - 일반 사용자: 접근 불가 (403 에러)
    
    **파라미터:**
    - `user_id`: 사용자 ID (필수)
    - `include_inactive`: 비활성 공정 포함 여부 (기본값: False)
    - `sort_by`: 정렬 기준 (기본값: process_name)
      - `process_id`: 공정 ID
      - `process_name`: 공정명
      - `create_dt`: 생성일시
    - `sort_order`: 정렬 순서 (기본값: asc)
      - `asc`: 오름차순
      - `desc`: 내림차순
    
    **응답 데이터:**
    - 공정 목록 (공정 ID, 공정명, 설명, 활성화 여부, 생성일시 등)
    - 전체 개수
    
    **사용 예시:**
    - 활성 공정만 조회: `GET /v1/masters/processes?user_id=user001`
    - 모든 공정 조회: `GET /v1/masters/processes?user_id=user001&include_inactive=true`
    - 공정명 내림차순 정렬: `GET /v1/masters/processes?user_id=user001&sort_by=process_name&sort_order=desc`
    """,
)
def get_processes(
    user_id: str = Query(..., description="사용자 ID (필수)", example="user001"),
    include_inactive: bool = Query(False, description="비활성 공정 포함 여부"),
    sort_by: str = Query("process_name", description="정렬 기준 (process_id, process_name, create_dt)"),
    sort_order: str = Query("asc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db),
    _: None = Depends(check_any_role_dependency),
):
    """
    공정 목록 조회
    
    사용자 권한에 따라 접근 가능한 공정만 조회합니다.
    - 시스템 관리자/통합 관리자: 모든 공정
    - 공정 관리자: 지정된 공정만
    - 일반 사용자: 접근 불가 (403 에러)
    """
    try:
        # request.state.user_id 우선 사용 (미들웨어에서 설정된 경우), 없으면 파라미터 user_id 사용 (테스트용)
        check_user_id = None
        if hasattr(request.state, "user_id") and request.state.user_id:
            check_user_id = request.state.user_id
        elif user_id:
            check_user_id = user_id
        
        if not check_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="사용자 ID가 필요합니다."
            )
        
        # 사용자 권한 기반 접근 가능한 공정 조회
        program_crud = ProgramCRUD(db)
        accessible_process_ids = program_crud.get_accessible_process_ids(check_user_id)
        
        process_crud = ProcessMasterCRUD(db)
        
        # 모든 공정 접근 가능한 경우 (system_admin 또는 integrated_admin)
        # None = 모든 공정 접근 가능을 의미
        if accessible_process_ids is None:
            processes = process_crud.get_all_processes(
                include_inactive=include_inactive,
                sort_by=sort_by,
                sort_order=sort_order
            )
        else:
            # 특정 공정만 접근 가능한 경우 (process_manager)
            processes = process_crud.get_processes_by_ids(
                process_ids=accessible_process_ids,
                include_inactive=include_inactive,
                sort_by=sort_by,
                sort_order=sort_order
            )
        
        items = [ProcessItem.from_orm(process) for process in processes]
        
        return ProcessListResponse(
            items=items,
            total_count=len(items)
        )
    except Exception as e:
        logger.error("공정 목록 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공정 목록 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e

