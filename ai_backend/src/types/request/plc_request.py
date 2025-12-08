# _*_ coding: utf-8 _*_
"""PLC request models."""
from typing import List, Optional

from pydantic import BaseModel, Field


class PLCMappingItem(BaseModel):
    """PLC-PGM 매핑 항목"""

    plc_uuids: List[str] = Field(
        ..., description="매핑할 PLC UUID 리스트", min_items=1
    )
    program_id: str = Field(..., description="매핑할 PGM ID")


class PLCMappingRequest(BaseModel):
    """PLC-PGM 매핑 저장 요청"""

    items: List[PLCMappingItem] = Field(
        ..., description="PLC-PGM 매핑 항목 리스트", min_items=1
    )


class PLCDeleteRequest(BaseModel):
    """PLC 삭제 요청"""

    plc_uuids: List[str] = Field(
        ..., description="삭제할 PLC UUID 리스트", min_items=1
    )


class PLCBatchCreateItem(BaseModel):
    """PLC 일괄 생성 항목"""

    plant_id: str = Field(..., description="Plant ID")
    process_id: str = Field(..., description="공정 ID")
    line_id: str = Field(..., description="Line ID")
    plc_name: str = Field(..., description="PLC명")
    unit: Optional[str] = Field(None, description="호기")
    plc_id: str = Field(..., description="PLC ID")
    create_user: str = Field(..., description="생성 사용자")


class PLCBatchCreateRequest(BaseModel):
    """PLC 다건 생성 요청"""

    items: List[PLCBatchCreateItem] = Field(
        ..., description="생성할 PLC 목록", min_items=1
    )


class PLCBatchUpdateItem(BaseModel):
    """PLC 일괄 수정 항목"""

    plc_uuid: str = Field(..., description="PLC UUID (필수)")
    plant_id: Optional[str] = Field(None, description="Plant ID")
    process_id: Optional[str] = Field(None, description="공정 ID")
    line_id: Optional[str] = Field(None, description="Line ID")
    plc_name: Optional[str] = Field(None, description="PLC명")
    unit: Optional[str] = Field(None, description="호기")
    plc_id: Optional[str] = Field(None, description="PLC ID")
    program_id: Optional[str] = Field(None, description="매핑할 PGM ID")
    update_user: str = Field(..., description="수정 사용자")


class PLCBatchUpdateRequest(BaseModel):
    """PLC 다건 수정 요청"""

    items: List[PLCBatchUpdateItem] = Field(
        ..., description="수정할 PLC 목록", min_items=1
    )

