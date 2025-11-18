# _*_ coding: utf-8 _*_
"""Program response models."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProgramValidationResult(BaseModel):
    """유효성 검사 결과"""
    is_valid: bool = Field(..., description="유효성 검사 통과 여부")
    errors: list = Field(default_factory=list, description="에러 목록")
    error_sections: Optional[Dict[str, List[str]]] = Field(
        None, description="섹션별로 그룹화된 에러 목록"
    )
    warnings: list = Field(default_factory=list, description="경고 목록")
    checked_files: list = Field(default_factory=list, description="체크된 파일 목록")
    file_count_in_zip: Optional[int] = Field(
        None, description="ZIP 파일 내 파일 수"
    )
    file_count_in_xlsx: Optional[int] = Field(
        None, description="XLSX 파일 내 로직 파일명 수"
    )
    matched_files: Optional[list] = Field(None, description="매칭된 파일 목록")
    missing_files: Optional[list] = Field(None, description="누락된 파일 목록")


class ProcessDropdownItem(BaseModel):
    """공정 드롭다운 항목"""
    process_id: str = Field(..., description="공정 ID")
    process_name: str = Field(..., description="공정명")

    class Config:
        from_attributes = True


class ProcessDropdownResponse(BaseModel):
    """공정 드롭다운 목록 응답"""
    processes: List[ProcessDropdownItem] = Field(
        default_factory=list,
        description="접근 가능한 공정 목록 (권한이 없으면 빈 배열)",
    )


class ProgramFileInfo(BaseModel):
    """프로그램 파일 정보 (팝업 다운로드용)"""
    file_type: str = Field(
        ...,
        description=(
            "파일 타입: "
            "program_classification (Program 분류 체계), "
            "program_logic (Program Logic 파일), "
            "program_comment (Program Comment)"
        ),
    )
    original_filename: str = Field(..., description="원본 파일명")
    file_size: int = Field(..., description="파일 크기 (bytes)")
    file_extension: str = Field(..., description="파일 확장자")
    download_file_type: str = Field(
        ...,
        description=(
            "다운로드 API용 file_type "
            "(program_classification, program_logic, program_comment)"
        ),
    )


class ProgramInfo(BaseModel):
    """프로그램 정보"""
    program_id: str = Field(..., description="프로그램 ID (PGM ID)")
    program_title: str = Field(..., description="프로그램 제목 (PGM Name)")
    program_description: Optional[str] = Field(None, description="프로그램 설명")
    process_id: Optional[str] = Field(None, description="공정 ID")
    process_name: Optional[str] = Field(None, description="공정명")
    user_id: Optional[str] = Field(None, description="생성 사용자 ID")
    status: str = Field(..., description="처리 상태")
    error_message: Optional[str] = Field(None, description="에러 메시지")
    is_valid: Optional[bool] = Field(None, description="유효성 검사 통과 여부")
    errors: Optional[list] = Field(None, description="에러 목록")
    warnings: Optional[list] = Field(None, description="경고 목록")
    checked_files: Optional[list] = Field(None, description="체크된 파일 목록")
    message: Optional[str] = Field(None, description="메시지")
    validation_result: Optional[Dict[str, Any]] = Field(
        None, description="유효성 검사 결과"
    )
    create_dt: Optional[datetime] = Field(None, description="생성 일시")
    update_dt: Optional[datetime] = Field(None, description="수정 일시")
    completed_at: Optional[datetime] = Field(None, description="완료 일시")
    files: Optional[List[ProgramFileInfo]] = Field(
        None, description="프로그램 관련 파일 목록 (팝업 다운로드용)"
    )
    ladder_file_count: Optional[int] = Field(
        None, description="Logic 파일 개수"
    )
    comment_file_count: Optional[int] = Field(
        None, description="Comment 파일 개수"
    )

    class Config:
        from_attributes = True


class RegisterProgramResponse(BaseModel):
    """프로그램 등록 응답"""
    status: str = Field(..., description="응답 상태")
    message: str = Field(..., description="응답 메시지")
    data: Optional[ProgramInfo] = Field(
        None, description="프로그램 정보"
    )
    validation_result: Optional[ProgramValidationResult] = Field(
        None, description="유효성 검사 결과"
    )


class ProgramListItem(BaseModel):
    """프로그램 목록 항목"""
    program_id: str = Field(..., description="프로그램 ID (PGM ID)")
    program_name: str = Field(..., description="프로그램 제목")
    process_name: Optional[str] = Field(
        None, description="공정명 (PLC 매핑 시)"
    )
    ladder_file_count: int = Field(
        default=0, description="Ladder 파일 개수"
    )
    comment_file_count: int = Field(
        default=0, description="Comment 파일 개수"
    )
    status: str = Field(..., description="등록 상태")
    status_display: str = Field(..., description="등록 상태 표시명")
    processing_time: Optional[str] = Field(
        None, description="등록 소요시간 (예: '10 min', '-')"
    )
    create_user: str = Field(..., description="작성자")
    create_dt: datetime = Field(..., description="등록일시")

    class Config:
        from_attributes = True


class ProgramListResponse(BaseModel):
    """프로그램 목록 응답"""
    items: List[ProgramListItem] = Field(
        ..., description="프로그램 목록"
    )
    total_count: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지당 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")
