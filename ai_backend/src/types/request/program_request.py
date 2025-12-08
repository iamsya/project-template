# _*_ coding: utf-8 _*_
"""Program request models."""
from typing import List, Optional

from fastapi import UploadFile
from pydantic import BaseModel, Field


class ProgramRegisterRequest(BaseModel):
    """프로그램 등록 요청 모델 (파일 포함)
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Form 파라미터로 처리.
    """

    program_title: str = Field(
        ..., min_length=1, max_length=200, description="프로그램 제목"
    )
    process_id: str = Field(
        ..., min_length=1, max_length=50, description="공정 ID"
    )
    program_description: Optional[str] = Field(
        default=None, max_length=1000, description="프로그램 설명"
    )
    ladder_zip: UploadFile = Field(
        ..., description="PLC Ladder Logic ZIP 파일"
    )
    template_xlsx: UploadFile = Field(
        ..., description="템플릿 분류체계 데이터 XLSX 파일"
    )
    comment_csv: UploadFile = Field(
        ..., description="PLC Ladder Comment CSV 파일"
    )


class ProgramListRequest(BaseModel):
    """프로그램 목록 조회 요청
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Query 파라미터로 처리.
    """

    program_id: Optional[str] = Field(
        None, description="PGM ID로 부분 일치 검색", example="pgm001"
    )
    program_name: Optional[str] = Field(
        None, description="제목으로 부분 일치 검색", example="공정1"
    )
    process_id: Optional[str] = Field(
        None, description="공정 ID로 부분 일치 검색", example="process_001"
    )
    status: Optional[str] = Field(
        None,
        description=(
            "등록 상태로 정확 일치 검색 "
            "(preparing, preprocessing, indexing, completed, failed)"
        ),
        example="completed",
    )
    create_user: Optional[str] = Field(
        None, description="작성자로 부분 일치 검색", example="user001"
    )
    page: int = Field(1, ge=1, description="페이지 번호", example=1)
    page_size: int = Field(
        10,
        ge=1,
        le=10000,
        description=(
            "페이지당 항목 수 (페이지네이션 없이 모든 데이터를 가져오려면 "
            "큰 값 사용, 예: 10000)"
        ),
        example=10,
    )
    sort_by: str = Field(
        "create_dt",
        description="정렬 기준 (create_dt, program_id, program_name, status)",
        example="create_dt",
    )
    sort_order: str = Field(
        "desc", description="정렬 순서 (asc, desc)", example="desc"
    )


class ProgramDetailRequest(BaseModel):
    """프로그램 상세 조회 요청 (Path 파라미터 program_id 제외)
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Query 파라미터로 처리.
    """


class ProgramRetryRequest(BaseModel):
    """프로그램 재시도 요청 (Path 파라미터 program_id 제외)
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Query 파라미터로 처리.
    """

    retry_type: str = Field(
        default="all",
        description="재시도 타입 (preprocessing, document, all)",
        example="all",
    )


class ProgramFailureListRequest(BaseModel):
    """프로그램 실패 목록 조회 요청 (Path 파라미터 program_id 제외)
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Query 파라미터로 처리.
    """

    failure_type: Optional[str] = Field(
        None,
        description=(
            "실패 타입 필터 "
            "(preprocessing, document_storage, vector_indexing)"
        ),
        example="preprocessing",
    )


class ProgramDeleteRequest(BaseModel):
    """프로그램 삭제 요청
    
    Note: user_id는 클라이언트 요청 데이터가 아니므로 모델에 포함하지 않음.
    라우터에서 request.state.user_id 또는 Query 파라미터로 처리.
    """

    program_ids: List[str] = Field(
        ..., description="삭제할 프로그램 ID 리스트", min_items=1
    )
