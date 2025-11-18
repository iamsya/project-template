# _*_ coding: utf-8 _*_
"""PLC response models."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PLCInfo(BaseModel):
    """PLC 정보"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="계획")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="라인")
    equipment_group: Optional[str] = Field(None, description="설비 그룹")
    unit: Optional[str] = Field(None, description="유닛")
    program_id: Optional[str] = Field(None, description="Program ID")
    mapping_dt: Optional[datetime] = Field(None, description="매핑 일시")
    mapping_user: Optional[str] = Field(None, description="매핑 사용자")
    is_active: bool = Field(..., description="활성화 여부")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="메타데이터")
    create_dt: datetime = Field(..., description="생성 일시")
    create_user: str = Field(..., description="생성 사용자")
    update_dt: Optional[datetime] = Field(None, description="수정 일시")
    update_user: Optional[str] = Field(None, description="수정 사용자")

    class Config:
        from_attributes = True


class PLCBasicInfo(BaseModel):
    """PLC 기본 정보 (is_active=True일 때만 반환)"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="계획")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="라인")
    equipment_group: Optional[str] = Field(None, description="설비 그룹")
    unit: Optional[str] = Field(None, description="유닛")
    program_id: Optional[str] = Field(None, description="Program ID")
    program_id_changed: bool = Field(
        False,
        description="Program ID 변경 여부 (previous_program_id와 다를 경우 True)",
    )
    previous_program_id: Optional[str] = Field(None, description="이전 Program ID")

    class Config:
        from_attributes = True


class PLCListItem(BaseModel):
    """PLC 목록 항목 (매핑 화면용)"""

    id: str = Field(..., description="PLC ID (Primary Key)")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    plant: Optional[str] = Field(None, description="Plant")
    process: Optional[str] = Field(None, description="공정")
    line: Optional[str] = Field(None, description="Line")
    equipment_group: Optional[str] = Field(None, description="장비 그룹")
    unit: Optional[str] = Field(None, description="호기")
    program_id: Optional[str] = Field(
        None, description="매핑된 PGM ID"
    )
    mapping_user: Optional[str] = Field(None, description="매핑 등록자")
    mapping_dt: Optional[datetime] = Field(None, description="매핑 일시")

    class Config:
        from_attributes = True


class PLCListResponse(BaseModel):
    """PLC 목록 응답"""

    items: List[PLCListItem] = Field(..., description="PLC 목록")
    total_count: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")


class ProgramMappingItem(BaseModel):
    """PGM 프로그램 매핑용 항목 (간단한 정보)"""

    program_id: str = Field(..., description="프로그램 ID (PGM ID)")
    program_name: str = Field(..., description="프로그램 제목")
    ladder_file_count: int = Field(
        default=0, description="Ladder 파일 개수"
    )
    comment_file_count: int = Field(
        default=0, description="Comment 파일 개수"
    )
    create_user: str = Field(..., description="등록자")
    create_dt: datetime = Field(..., description="등록일시")

    class Config:
        from_attributes = True


class ProgramMappingListResponse(BaseModel):
    """PGM 프로그램 매핑용 목록 응답"""

    items: List[ProgramMappingItem] = Field(
        ..., description="프로그램 목록"
    )
    total_count: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")


class PLCMappingRequest(BaseModel):
    """PLC-PGM 매핑 저장 요청"""

    plc_uuids: List[str] = Field(
        ..., description="매핑할 PLC UUID 리스트", min_items=1
    )
    program_id: str = Field(..., description="매핑할 PGM ID")
    mapping_user: str = Field(..., description="매핑 사용자")


class PLCMappingResponse(BaseModel):
    """PLC-PGM 매핑 저장 응답"""

    success: bool = Field(..., description="성공 여부")
    mapped_count: int = Field(..., description="매핑된 PLC 개수")
    failed_count: int = Field(..., description="실패한 PLC 개수")
    errors: List[str] = Field(
        default_factory=list, description="에러 메시지 리스트"
    )


class PLCDropdownItem(BaseModel):
    """드롭다운용 PLC 항목 (프론트엔드 필터링용)"""

    plc_uuid: str = Field(..., description="PLC UUID")
    plc_id: str = Field(..., description="PLC 식별자")
    plc_name: str = Field(..., description="PLC 이름")
    unit: Optional[str] = Field(None, description="호기")
    plant_id: Optional[str] = Field(None, description="Plant ID")
    plant_name: Optional[str] = Field(None, description="Plant 이름")
    process_id: Optional[str] = Field(None, description="Process ID")
    process_name: Optional[str] = Field(None, description="Process 이름")
    line_id: Optional[str] = Field(None, description="Line ID")
    line_name: Optional[str] = Field(None, description="Line 이름")


class PLCDropdownResponse(BaseModel):
    """드롭다운용 PLC 목록 응답"""

    items: List[PLCDropdownItem] = Field(..., description="전체 PLC 목록")
    total_count: int = Field(..., description="전체 개수")


# Tree API용 Response 모델
class PLCTreeInfo(BaseModel):
    """PLC Tree 정보 (호기별 PLC 정보)"""

    plc_id: str = Field(..., description="PLC ID")
    plc_uuid: str = Field(..., description="PLC UUID")
    create_dt: str = Field(..., description="등록일시")
    user: str = Field(..., description="등록자")


class PLCTreeUnitItem(BaseModel):
    """PLC Tree Unit 항목"""

    unit: str = Field(..., description="호기")
    info: List[PLCTreeInfo] = Field(..., description="PLC 정보 리스트")


class PLCTreePlcNameItem(BaseModel):
    """PLC Tree PLC명 항목"""

    plcName: str = Field(..., description="PLC명")
    unitList: List[PLCTreeUnitItem] = Field(..., description="호기 리스트")


class PLCTreeLineItem(BaseModel):
    """PLC Tree Line 항목"""

    line: str = Field(..., description="Line 이름")
    plcNameList: List[PLCTreePlcNameItem] = Field(..., description="PLC명 리스트")


class PLCTreeProcItem(BaseModel):
    """PLC Tree 공정 항목"""

    proc: str = Field(..., description="공정 이름")
    lineList: List[PLCTreeLineItem] = Field(..., description="Line 리스트")


class PLCTreePlantItem(BaseModel):
    """PLC Tree Plant 항목"""

    plant: str = Field(..., description="Plant 이름")
    procList: List[PLCTreeProcItem] = Field(..., description="공정 리스트")


class PLCTreeResponse(BaseModel):
    """PLC Tree 응답"""

    data: List[PLCTreePlantItem] = Field(..., description="Plant 리스트")


# 드롭다운용 마스터 데이터 Response 모델 (프론트엔드 최적화)
class MasterDropdownItem(BaseModel):
    """드롭다운용 기본 항목"""

    id: str = Field(..., description="ID (Primary Key)")
    code: str = Field(..., description="코드")
    name: str = Field(..., description="이름")


class MasterDropdownResponse(BaseModel):
    """
    드롭다운용 마스터 데이터 응답 (프론트엔드 최적화)
    
    연쇄 드롭다운 구현에 최적화된 구조:
    - plants: Plant 목록 (첫 번째 드롭다운)
    - processesByPlant: Plant ID를 키로 하는 Process 목록 맵 (두 번째 드롭다운)
    - linesByProcess: Process ID를 키로 하는 Line 목록 맵 (세 번째 드롭다운)
    
    프론트엔드 사용 예시:
    ```javascript
    // Plant 드롭다운
    const plants = response.plants;
    
    // Plant 선택 시 Process 드롭다운
    const processes = response.processesByPlant[selectedPlantId] || [];
    
    // Process 선택 시 Line 드롭다운
    const lines = response.linesByProcess[selectedProcessId] || [];
    ```
    """

    plants: List[MasterDropdownItem] = Field(
        ..., description="Plant 목록 (첫 번째 드롭다운)"
    )
    processesByPlant: Dict[str, List[MasterDropdownItem]] = Field(
        ...,
        description="Plant ID를 키로 하는 Process 목록 맵 (두 번째 드롭다운)",
        example={"plant_001": [{"id": "process_001", "code": "PRC1", "name": "Process 1"}]},
    )
    linesByProcess: Dict[str, List[MasterDropdownItem]] = Field(
        ...,
        description="Process ID를 키로 하는 Line 목록 맵 (세 번째 드롭다운)",
        example={"process_001": [{"id": "line_001", "code": "LN1", "name": "Line 1"}]},
    )


# PLC 생성 Request/Response 모델
class PLCCreateRequest(BaseModel):
    """PLC 생성 요청"""

    plant_id: str = Field(..., description="Plant ID (드롭다운 선택)")
    process_id: str = Field(..., description="공정 ID (드롭다운 선택)")
    line_id: str = Field(..., description="Line ID (드롭다운 선택)")
    plc_name: str = Field(..., description="PLC명 (사용자 입력)")
    unit: Optional[str] = Field(None, description="호기 (사용자 입력, 선택사항)")
    plc_id: str = Field(..., description="PLC ID (사용자 입력)")
    create_user: str = Field(..., description="생성 사용자")


class PLCCreateResponse(BaseModel):
    """PLC 생성 응답"""

    success: bool = Field(..., description="성공 여부")
    plc_uuid: Optional[str] = Field(None, description="생성된 PLC UUID")
    message: str = Field(..., description="응답 메시지")


class PLCUpdateRequest(BaseModel):
    """PLC 수정 요청"""

    plc_name: Optional[str] = Field(None, description="PLC명 (수정 시)")
    unit: Optional[str] = Field(None, description="호기 (수정 시)")
    plc_id: Optional[str] = Field(None, description="PLC ID (수정 시)")
    update_user: str = Field(..., description="수정 사용자")


class PLCUpdateResponse(BaseModel):
    """PLC 수정 응답"""

    success: bool = Field(..., description="성공 여부")
    plc_uuid: Optional[str] = Field(None, description="수정된 PLC UUID")
    message: str = Field(..., description="응답 메시지")


class PLCDeleteRequest(BaseModel):
    """PLC 삭제 요청 (일괄 삭제용)"""

    plc_uuids: List[str] = Field(
        ..., description="삭제할 PLC UUID 리스트", min_items=1
    )
    delete_user: str = Field(..., description="삭제 사용자")


class PLCDeleteResponse(BaseModel):
    """PLC 삭제 응답"""

    success: bool = Field(..., description="성공 여부")
    deleted_count: int = Field(..., description="삭제된 PLC 개수")
    message: str = Field(..., description="응답 메시지")


class PLCBatchItem(BaseModel):
    """PLC 일괄 저장 항목"""

    plc_uuid: Optional[str] = Field(
        None, description="PLC UUID (있으면 수정, 없으면 생성)"
    )
    plant_id: str = Field(..., description="Plant ID")
    process_id: str = Field(..., description="공정 ID")
    line_id: str = Field(..., description="Line ID")
    plc_name: str = Field(..., description="PLC명")
    unit: Optional[str] = Field(None, description="호기")
    plc_id: str = Field(..., description="PLC ID")
    update_user: str = Field(..., description="저장 사용자")


class PLCBatchSaveRequest(BaseModel):
    """PLC 일괄 저장 요청"""

    items: List[PLCBatchItem] = Field(
        ..., description="저장할 PLC 목록", min_items=1
    )


class PLCBatchSaveResponse(BaseModel):
    """PLC 일괄 저장 응답"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    created_count: int = Field(..., description="생성된 PLC 개수")
    updated_count: int = Field(..., description="수정된 PLC 개수")
    failed_count: int = Field(..., description="실패한 PLC 개수")
    errors: List[str] = Field(
        default_factory=list, description="에러 메시지 리스트"
    )
