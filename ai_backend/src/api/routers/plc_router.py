# _*_ coding: utf-8 _*_
"""PLC Management API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from src.core.dependencies import get_db
from src.database.crud.master_crud import MasterHierarchyCRUD
from src.database.crud.plc_crud import PLCCRUD
from src.types.response.exceptions import HandledException
from src.types.response.plc_response import (
    MasterDropdownResponse,
    PLCBasicInfo,
    PLCDeleteRequest,
    PLCDeleteResponse,
    PLCListResponse,
    PLCListItem,
    PLCMappingRequest,
    PLCMappingResponse,
    PLCTreeResponse,
    PLCBatchCreateRequest,
    PLCBatchCreateResponse,
    PLCBatchUpdateRequest,
    PLCBatchUpdateResponse,
    SimpleMasterDropdownResponse,
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
    
    **필터링 기능:**
    - `plant_id`: Plant ID로 필터링
    - `process_id`: 공정 ID로 필터링
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
    - 전체 목록: `GET /v1/plcs?page=1&page_size=10`
    - 계층별 필터링: `GET /v1/plcs?plant_id=KY1&process_id=process001&line_id=line001`
    - PLC ID 검색: `GET /v1/plcs?plc_id=M1CFB01000`
    - PLC 명 검색: `GET /v1/plcs?plc_name=CELL_FABRICATOR`
    - PGM명 필터링: `GET /v1/plcs?program_name=라벨부착`
    - 복합 검색 및 정렬: `GET /v1/plcs?plant_id=KY1&process_id=process001&program_name=라벨부착&sort_by=plc_id&sort_order=desc&page=1&page_size=20`
    """,
)
def get_plc_list(
    plant_id: Optional[str] = Query(None, description="Plant ID로 필터링", example="plant001"),
    process_id: Optional[str] = Query(None, description="공정 ID로 필터링", example="process001"),
    line_id: Optional[str] = Query(None, description="Line ID로 필터링", example="line001"),
    plc_id: Optional[str] = Query(None, description="PLC ID로 검색", example="plc001"),
    plc_name: Optional[str] = Query(None, description="PLC 명으로 검색", example="PLC001"),
    program_name: Optional[str] = Query(None, description="PGM명으로 필터링", example="라벨부착"),
    page: int = Query(1, ge=1, description="페이지 번호", example=1),
    page_size: int = Query(10, ge=1, le=10000, description="페이지당 항목 수 (페이지네이션 없이 모든 데이터를 가져오려면 큰 값 사용, 예: 10000)", example=10),
    sort_by: str = Query(
        "plc_id",
        description="정렬 기준 (plc_id, plc_name, create_dt)",
        example="plc_id",
    ),
    sort_order: str = Query("asc", description="정렬 순서 (asc, desc)", example="asc"),
    db: Session = Depends(get_db),
):
    """
    PLC 기준 정보 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

    화면: PLC-PGM 매핑 화면, PLC 등록 화면의 PLC 기준 정보 테이블
    - Plant, 공정, Line, PLC ID, PLC 명으로 검색/필터링
    - PGM명으로 필터링 (매핑된 PGM 기준)
    - 매핑된 PGM ID, 등록자(매핑일시) 표시
    """
    try:
        plc_crud = PLCCRUD(db)
        plcs, total_count = plc_crud.get_plcs(
            plant_id=plant_id,
            process_id=process_id,
            line_id=line_id,
            plc_id=plc_id,
            plc_name=plc_name,
            program_name=program_name,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

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
                    id=plc.plc_uuid,
                    plc_id=plc.plc_id,
                    plc_name=plc.plc_name,
                    plant=hierarchy.get("plant", {}).get("name")
                    if hierarchy
                    else None,
                    process=hierarchy.get("process", {}).get("name")
                    if hierarchy
                    else None,
                    line=hierarchy.get("line", {}).get("name")
                    if hierarchy
                    else None,
                    unit=plc.unit,
                    program_id=plc.program_id,
                    mapping_user=plc.mapping_user,
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
    여러 PLC에 하나의 PGM 프로그램을 매핑합니다.
    
    **화면 용도:** PLC 관리 화면의 매핑 저장 기능
    
    **주요 기능:**
    - 여러 PLC ID에 동일한 PGM 프로그램 매핑
    - 이전 매핑 정보를 `previous_program_id`에 저장 (히스토리 관리)
    - 매핑 사용자 및 매핑 일시 기록
    
    **요청 파라미터:**
    - `plc_uuids`: 매핑할 PLC UUID 리스트 (배열)
    - `program_id`: 매핑할 PGM 프로그램 ID
    - `mapping_user`: 매핑을 수행한 사용자 ID
    
    **응답:**
    - `success`: 전체 성공 여부
    - `mapped_count`: 성공적으로 매핑된 PLC 개수
    - `failed_count`: 매핑 실패한 PLC 개수
    - `errors`: 실패한 PLC의 오류 정보 리스트
    
    **처리 로직:**
    1. 각 PLC의 현재 `program_id`를 `previous_program_id`에 저장
    2. 새로운 `program_id`로 업데이트
    3. `mapping_user`, `mapping_dt` 업데이트
    
    **예외 상황:**
    - PLC를 찾을 수 없는 경우: 해당 PLC는 실패 처리
    - PGM 프로그램을 찾을 수 없는 경우: 전체 실패
    """,
)
def update_plc_program_mapping(
    request: PLCMappingRequest,
    db: Session = Depends(get_db),
):
    """
    PLC-PGM 매핑 저장

    여러 PLC에 하나의 PGM을 매핑합니다.
    """
    try:
        plc_crud = PLCCRUD(db)
        result = plc_crud.update_plc_program_mapping(
            plc_uuids=request.plc_uuids,
            program_id=request.program_id,
            mapping_user=request.mapping_user,
        )

        return PLCMappingResponse(
            success=result["failed_count"] == 0,
            mapped_count=result["success_count"],
            failed_count=result["failed_count"],
            errors=result["errors"],
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
):
    """
    PLC Tree 구조 조회 (채팅 메뉴에서 PLC 선택용)
    
    Hierarchy: Plant → 공정 → Line → PLC명 → 호기 → PLC ID
    """
    try:
        plc_crud = PLCCRUD(db)
        tree_data = plc_crud.get_plc_tree()

        return PLCTreeResponse(data=tree_data)
    except Exception as e:
        logger.error("PLC Tree 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PLC Tree 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get(
    "/masters/dropdown",
    response_model=SimpleMasterDropdownResponse,
    summary="드롭다운용 마스터 데이터 전체 조회",
    description="""
    PLC 추가 화면에서 사용할 드롭다운 데이터를 전체 조회합니다.
    
    **화면 용도:** PLC 추가 화면의 Plant, 공정, Line 드롭다운
    
    **응답 구조:**
    ```json
    {
      "plants": [
        {"id": "plant_001", "name": "Plant 1"},
        {"id": "plant_002", "name": "Plant 2"}
      ],
      "processes": [
        {"id": "process_001", "name": "Process 1"},
        {"id": "process_002", "name": "Process 2"}
      ],
      "lines": [
        {"id": "line_001", "name": "Line 1"},
        {"id": "line_002", "name": "Line 2"}
      ]
    }
    ```
    
    **프론트엔드 사용 예시:**
    ```javascript
    // 단순 리스트로 반환 (계층 구조 없음)
    const plants = response.plants;
    const processes = response.processes;
    const lines = response.lines;
    ```
    
    **특징:**
    - 마스터 테이블에서 활성화된 데이터만 조회 (is_active=true)
    - 계층 구조 없이 단순 리스트로 반환
    - 정렬 순서: 이름 순서
    """,
)
def get_masters_for_dropdown(
    db: Session = Depends(get_db),
):
    """
    드롭다운용 마스터 데이터 전체 조회
    
    마스터 테이블에서 활성화된 Plant, 공정, Line을 단순 리스트로 반환합니다.
    계층 구조가 필요 없는 경우 사용합니다.
    """
    try:
        master_crud = MasterHierarchyCRUD(db)
        masters = master_crud.get_all_masters_for_dropdown()

        return SimpleMasterDropdownResponse(
            plants=masters["plants"],
            processes=masters["processes"],
            lines=masters["lines"],
        )
    except Exception as e:
        logger.error("드롭다운용 마스터 데이터 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"드롭다운용 마스터 데이터 조회 중 오류가 발생했습니다: {str(e)}",
        ) from e


@router.get(
    "/mapping/dropdown",
    response_model=MasterDropdownResponse,
    summary="PLC-PGM 매핑 화면용 드롭다운 데이터 조회",
    description="""
    PLC-PGM 매핑 화면에서 사용할 드롭다운 데이터를 조회합니다.
    
    **화면 용도:** PLC-PGM 매핑 화면의 Plant, 공정, Line 드롭다운
    
    **권한 기반 필터링:**
    - `user_id`: 사용자 ID (필수)
    - 사용자가 접근 가능한 Plant, Process, Line만 반환
    - Process는 사용자 권한에 따라 필터링됩니다
      - super 권한 그룹: 모든 활성 Process 반환
      - plc 권한 그룹: 지정된 Process만 반환
      - 권한이 없으면 Process 목록이 비어있음
    - 계층 구조 포함 (processesByPlant, linesByProcess)
    
    **응답 구조:**
    ```json
    {
      "plants": [
        {"id": "plant_001", "name": "Plant 1"},
        {"id": "plant_002", "name": "Plant 2"}
      ],
      "processesByPlant": {
        "plant_001": [
          {"id": "process_001", "name": "모듈"},
          {"id": "process_002", "name": "전극"}
        ],
        "plant_002": [
          {"id": "process_003", "name": "조립"}
        ]
      },
      "linesByProcess": {
        "process_001": [
          {"id": "line_001", "name": "1라인"},
          {"id": "line_002", "name": "2라인"}
        ],
        "process_002": [
          {"id": "line_003", "name": "1라인"}
        ]
      }
    }
    ```
    
    **프론트엔드 사용 흐름:**
    1. API 호출: `GET /v1/plcs/mapping/dropdown?user_id=user001`
    2. Plant 드롭다운: `response.plants` 사용
    3. Plant 선택 시: `response.processesByPlant[selectedPlantId]` 사용
    4. Process 선택 시: `response.linesByProcess[selectedProcessId]` 사용
    5. Line 선택 후: `GET /v1/plcs?plant_id=xxx&process_id=xxx&line_id=xxx` 호출하여 PLC 목록 조회
    
    **사용 예시:**
    ```
    GET /v1/plcs/mapping/dropdown?user_id=user001
    ```
    """,
)
def get_mapping_dropdown(
    user_id: str = Query(..., description="사용자 ID (권한 기반 필터링용)", example="user001"),
    db: Session = Depends(get_db),
):
    """
    PLC-PGM 매핑 화면용 드롭다운 데이터 조회
    
    사용자 권한에 따라 접근 가능한 공정만 포함하여 반환합니다.
    """
    try:
        # 사용자 권한 기반 접근 가능한 공정 조회
        from src.database.crud.program_crud import ProgramCRUD
        
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
        
        return MasterDropdownResponse(
            plants=masters["plants"],
            processesByPlant=masters["processesByPlant"],
            linesByProcess=masters["linesByProcess"],
        )
    except Exception as e:
        logger.error("매핑 화면용 드롭다운 데이터 조회 실패: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"드롭다운 데이터 조회 중 오류가 발생했습니다: {str(e)}",
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
    request: PLCDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    PLC 일괄 삭제
    """
    try:
        plc_crud = PLCCRUD(db)
        
        # 권한 체크 (API 직접 호출 시)
        if not plc_crud.check_plc_management_permission(request.delete_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="PLC 삭제 권한이 없습니다.",
            )
        
        # PLC 일괄 삭제
        deleted_count = plc_crud.delete_plcs(
            plc_uuids=request.plc_uuids, delete_user=request.delete_user
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
    request: PLCBatchCreateRequest,
    db: Session = Depends(get_db),
):
    """
    PLC 다건 저장 (생성)
    
    새 PLC 추가 시 호출되는 API입니다.
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

        for item in request.items:
            try:
                # 마스터 데이터 유효성 검사
                plant = plant_crud.get_plant(item.plant_id)
                if not plant:
                    errors.append(
                        f"PLC ID {item.plc_id}: 존재하지 않는 Plant ID입니다"
                    )
                    failed_count += 1
                    continue

                process = process_crud.get_process(item.process_id)
                if not process:
                    errors.append(
                        f"PLC ID {item.plc_id}: 존재하지 않는 공정 ID입니다"
                    )
                    failed_count += 1
                    continue

                line = line_crud.get_line(item.line_id)
                if not line:
                    errors.append(
                        f"PLC ID {item.plc_id}: 존재하지 않는 Line ID입니다"
                    )
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
                    error_msg = f"PLC ID {item.plc_id}: {e.msg or str(e)}"
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
    request: PLCBatchUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    PLC 다건 수정
    
    기존 PLC 수정 시 호출되는 API입니다.
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

        for item in request.items:
            try:
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
                    errors.append(
                        f"PLC UUID {item.plc_uuid}: PLC를 찾을 수 없습니다"
                    )
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
):
    """
    PLC 정보 조회 (PLC_UUID로)

    - plc_uuid: PLC의 UUID (Primary Key)
    - is_deleted가 false인 경우에만 조회합니다 (사용 중으로 인식).
    - 기본 정보만 반환합니다 (plc_uuid, plc_id, plc_name, 계층 구조, program_id).
    - 검색 결과가 없으면 200 OK와 함께 null을 반환합니다 (REST API 규칙).
    """
    try:
        plc_crud = PLCCRUD(db)
        plc = plc_crud.get_plc(plc_uuid)

        # 검색 결과가 비어 있어도 200 OK 반환 (REST API 규칙)
        if not plc:
            return None

        # is_deleted 체크 (is_active는 deprecated)
        if plc.is_deleted:
            return None

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
