# _*_ coding: utf-8 _*_
"""Master Data API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.core.dependencies import get_db
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
    - `user_id`: 사용자 ID (선택사항)
      - 제공된 경우: 사용자 권한에 따라 접근 가능한 Process만 반환
        - super 권한 그룹: 모든 활성 Process 반환
        - plc 권한 그룹: 지정된 Process만 반환
        - 권한이 없으면 Process 목록이 비어있음
      - 제공되지 않은 경우: 모든 활성 Process 반환 (권한 필터링 없음)
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
    1. API 호출: `GET /v1/masters?user_id=user001` (권한 필터링) 또는 `GET /v1/masters` (전체 조회)
    2. Plant 드롭다운: `response.plants` 사용
    3. Plant 선택 시: `response.processesByPlant[selectedPlantId]` 사용
    4. Process 선택 시: `response.linesByProcess[selectedProcessId]` 사용
    
    **사용 예시:**
    ```
    GET /v1/masters?user_id=user001  # 권한 기반 필터링
    GET /v1/masters                   # 전체 조회 (권한 필터링 없음)
    ```
    """,
)
def get_masters_for_dropdown(
    user_id: Optional[str] = Query(
        None, description="사용자 ID (권한 기반 필터링용, 선택사항)", example="user001"
    ),
    db: Session = Depends(get_db),
):
    """
    권한 기반 마스터 데이터 조회 (드롭다운용)
    
    user_id가 제공된 경우 사용자 권한에 따라 접근 가능한 공정만 포함하여 반환합니다.
    user_id가 제공되지 않은 경우 모든 활성 공정을 반환합니다.
    """
    try:
        # 사용자 권한 기반 접근 가능한 공정 조회
        accessible_process_ids = None
        if user_id:
            program_crud = ProgramCRUD(db)
            accessible_processes = program_crud.get_accessible_processes(user_id)
            accessible_process_ids = (
                [p.process_id for p in accessible_processes]
                if accessible_processes
                else None
            )

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
    
    **파라미터:**
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
    - 활성 공정만 조회: `GET /v1/masters/processes`
    - 모든 공정 조회: `GET /v1/masters/processes?include_inactive=true`
    - 공정명 내림차순 정렬: `GET /v1/masters/processes?sort_by=process_name&sort_order=desc`
    """,
)
def get_processes(
    include_inactive: bool = Query(False, description="비활성 공정 포함 여부"),
    sort_by: str = Query("process_name", description="정렬 기준 (process_id, process_name, create_dt)"),
    sort_order: str = Query("asc", description="정렬 순서 (asc, desc)"),
    db: Session = Depends(get_db),
):
    """
    공정 목록 조회
    
    공정 기준정보 테이블에서 공정 목록을 조회합니다.
    """
    try:
        process_crud = ProcessMasterCRUD(db)
        processes = process_crud.get_all_processes(
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

