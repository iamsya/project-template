# _*_ coding: utf-8 _*_
"""
Program 관련 모델 정의
프로그램 마스터, 처리 실패, LLM 데이터 청크 테이블
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import false, true

from src.database.base import Base


class Program(Base):
    """프로그램 마스터 테이블"""

    __tablename__ = "PROGRAMS"

    # 기본 정보
    program_id = Column("PROGRAM_ID", String(50), primary_key=True)
    program_name = Column("PROGRAM_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)
    
    # 공정 정보 (화면에서 드롭다운으로 선택)
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=True,
        index=True,
        comment="공정 ID (화면에서 드롭다운 선택, 선택사항)"
    )

    # 상태 정보
    status = Column(
        "STATUS",
        String(50),
        nullable=False,
        default="preparing",
        server_default="preparing",
    )
    error_message = Column("ERROR_MESSAGE", Text, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)
    completed_at = Column("COMPLETED_AT", DateTime, nullable=True)

    # 사용 여부
    is_used = Column("IS_USED", Boolean, nullable=False, server_default=true())

    # 삭제 관리
    is_deleted = Column(
        "IS_DELETED",
        Boolean,
        nullable=False,
        server_default=false(),
        index=True,
        comment="삭제 여부 (소프트 삭제)"
    )
    deleted_at = Column(
        "DELETED_AT",
        DateTime,
        nullable=True,
        comment="삭제 일시"
    )
    deleted_by = Column(
        "DELETED_BY",
        String(50),
        nullable=True,
        comment="삭제자"
    )

    # 상태 상수
    STATUS_PREPARING = "preparing"
    STATUS_PREPROCESSING = "preprocessing"
    STATUS_INDEXING = "indexing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __repr__(self):
        return (
            f"<Program(program_id='{self.program_id}', "
            f"name='{self.program_name}', "
            f"status='{self.status}')>"
        )


class ProcessingFailure(Base):
    """처리 실패 정보 및 재시도 관리 테이블"""

    __tablename__ = "PROCESSING_FAILURES"

    # 기본 정보
    failure_id = Column("FAILURE_ID", String(50), primary_key=True)
    
    # 다형성 관계: source_type과 source_id로 다양한 엔티티 참조
    source_type = Column(
        "SOURCE_TYPE",
        String(50),
        nullable=False,
        index=True,
        comment="참조 엔티티 타입: 'program', 'knowledge_reference' 등",
    )
    source_id = Column(
        "SOURCE_ID",
        String(50),
        nullable=False,
        index=True,
        comment="참조 엔티티 ID (program_id, reference_id 등)",
    )

    # 실패 정보
    failure_type = Column("FAILURE_TYPE", String(50), nullable=False, index=True)
    file_path = Column("FILE_PATH", String(500), nullable=True)
    file_index = Column("FILE_INDEX", Integer, nullable=True)
    filename = Column("FILENAME", String(255), nullable=True)
    s3_path = Column("S3_PATH", String(500), nullable=True)
    s3_key = Column("S3_KEY", String(500), nullable=True)

    # 에러 정보
    error_message = Column("ERROR_MESSAGE", Text, nullable=False)
    error_details = Column("ERROR_DETAILS", JSON, nullable=True)

    # 재시도 정보
    retry_count = Column("RETRY_COUNT", Integer, nullable=False, server_default="0")
    max_retry_count = Column(
        "MAX_RETRY_COUNT", Integer, nullable=False, server_default="3"
    )
    status = Column(
        "STATUS",
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
    )

    # 해결 정보
    resolved_at = Column("RESOLVED_AT", DateTime, nullable=True)
    last_retry_at = Column("LAST_RETRY_AT", DateTime, nullable=True)
    resolved_by = Column("RESOLVED_BY", String(50), nullable=True)

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    created_at = Column(
        "CREATED_AT", DateTime, nullable=False, server_default=func.now()
    )
    updated_at = Column(
        "UPDATED_AT",
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # 소스 타입 상수
    SOURCE_TYPE_PROGRAM = "program"
    SOURCE_TYPE_KNOWLEDGE_REFERENCE = "knowledge_reference"
    
    # 실패 타입 상수
    FAILURE_TYPE_PREPROCESSING = "preprocessing"
    FAILURE_TYPE_DOCUMENT_STORAGE = "document_storage"
    FAILURE_TYPE_VECTOR_INDEXING = "vector_indexing"

    # 상태 상수
    STATUS_PENDING = "pending"
    STATUS_RETRYING = "retrying"
    STATUS_RESOLVED = "resolved"
    STATUS_FAILED = "failed"

    def __repr__(self):
        return (
            f"<ProcessingFailure(failure_id='{self.failure_id}', "
            f"source_type='{self.source_type}', "
            f"source_id='{self.source_id}', "
            f"failure_type='{self.failure_type}', "
            f"status='{self.status}')>"
        )


class ProgramLLMDataChunk(Base):
    """프로그램 LLM 데이터 청크 테이블"""

    __tablename__ = "PROGRAM_LLM_DATA_CHUNKS"

    # 기본 정보
    chunk_id = Column("CHUNK_ID", String(50), primary_key=True)
    program_id = Column(
        "PROGRAM_ID",
        String(50),
        ForeignKey("PROGRAMS.PROGRAM_ID"),
        nullable=False,
        index=True,
    )
    data_type = Column("DATA_TYPE", String(50), nullable=False, index=True)
    data_version = Column("DATA_VERSION", String(50), nullable=True, index=True)

    # 청크 정보
    chunk_index = Column("CHUNK_INDEX", Integer, nullable=False)
    total_chunks = Column("TOTAL_CHUNKS", Integer, nullable=False)
    chunk_size = Column("CHUNK_SIZE", Integer, nullable=False)
    total_size = Column("TOTAL_SIZE", Integer, nullable=True)

    # S3 정보
    s3_bucket = Column("S3_BUCKET", String(255), nullable=True)
    s3_key = Column("S3_KEY", String(500), nullable=False)
    s3_url = Column("S3_URL", String(1000), nullable=True)

    # 체크섬 정보
    file_hash = Column("FILE_HASH", String(64), nullable=True)
    checksum = Column("CHECKSUM", String(64), nullable=True)

    # 설명 및 메타데이터
    description = Column("DESCRIPTION", Text, nullable=True)
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<ProgramLLMDataChunk(chunk_id='{self.chunk_id}', "
            f"program_id='{self.program_id}', "
            f"data_type='{self.data_type}')>"
        )
