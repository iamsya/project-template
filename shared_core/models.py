# _*_ coding: utf-8 _*_
"""
공통 문서 모델 정의
Backend와 Prefect 프로젝트에서 공통으로 사용하는 SQLAlchemy 모델들
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import false, true

# SQLAlchemy Base
Base = declarative_base()

class Document(Base):
    """통합 문서 테이블 (Backend + Prefect 공통)"""
    __tablename__ = "DOCUMENTS"
    
    # 문서 타입 상수
    # Program 파일 타입
    TYPE_LADDER_LOGIC_ZIP = 'ladder_logic_zip'
    TYPE_LADDER_LOGIC_JSON = 'ladder_logic_json'
    TYPE_COMMENT = 'comment'
    TYPE_TEMPLATE = 'template'
    Knowledge Reference 파일 타입
    TYPE_MANUAL = 'manual'
    TYPE_GLOSSARY = 'glossary'
    TYPE_PLC = 'plc'
    일반 문서 타입
    TYPE_COMMON = 'common'
    TYPE_TYPE1 = 'type1'
    TYPE_TYPE2 = 'type2'
    VALID_DOCUMENT_TYPES = [
        # Program 파일
        TYPE_LADDER_LOGIC_ZIP,
        TYPE_LADDER_LOGIC_JSON,
        TYPE_COMMENT,
        TYPE_TEMPLATE,
        # Knowledge Reference 파일
        TYPE_MANUAL,
        TYPE_GLOSSARY,
        TYPE_PLC,
        # 일반 문서
        TYPE_COMMON,
        TYPE_TYPE1,
        TYPE_TYPE2,
    ]
    
    # 처리 상태 상수
    # JSON 파일 전용
    STATUS_PREPROCESSED = 'preprocessed'  # 전처리 완료 (임베딩 대기)
    # JSON 파일 및 Knowledge Reference 파일 공통
    STATUS_EMBEDDING = 'embedding'  # 임베딩 진행 중
    STATUS_EMBEDDED = 'embedded'  # 임베딩 완료
    STATUS_FAILED = 'failed'  # 전처리 또는 임베딩 실패
    # Knowledge Reference 파일 전용
    STATUS_COMPLETED = 'completed'  # 완료
    
    VALID_STATUSES = [
        STATUS_PREPROCESSED,
        STATUS_EMBEDDING,
        STATUS_EMBEDDED,
        STATUS_FAILED,
        STATUS_COMPLETED,
    ]
    
    # 기본 정보
    document_id = Column('DOCUMENT_ID', String(50), primary_key=True)
    document_name = Column('DOCUMENT_NAME', String(255), nullable=False)
    original_filename = Column('ORIGINAL_FILENAME', String(255), nullable=True)
    
    # 파일 정보
    file_key = Column('FILE_KEY', String(255), nullable=True)
    file_size = Column('FILE_SIZE', Integer, nullable=True)
    file_type = Column('FILE_TYPE', String(100), nullable=True)  # MIME 타입
    file_extension = Column('FILE_EXTENSION', String(10), nullable=False)
    upload_path = Column('UPLOAD_PATH', String(500), nullable=True)
    file_hash = Column('FILE_HASH', String(64), nullable=True)  # 중복 방지
    
    # 사용자 정보
    user_id = Column('USER_ID', String(50), nullable=False)
    is_public = Column('IS_PUBLIC', Boolean, nullable=False, server_default=false())
    
    # 문서 타입 (통합 관리)
    # Program 파일: ladder_logic_zip, ladder_logic_json, comment, template
    # Knowledge Reference 파일: manual, glossary, plc
    # 일반 문서: common, type1, type2
    document_type = Column(
        'DOCUMENT_TYPE',
        String(50),
        nullable=True,
        index=True,
        comment=(
            "문서 타입 (통합): "
            "ladder_logic_zip, ladder_logic_json, comment, template "
            "(Program 파일), "
            "manual, glossary, plc "
            "(Knowledge Reference 파일), "
            "common, type1, type2 "
            "(일반 문서)"
        )
    )
    
    # 처리 상태
    # 주의: status는 전처리 및 벡터 임베딩 대상 파일만 사용
    #       - JSON 파일 (document_type='ladder_logic_json'):
    #         STATUS_PREPROCESSED, STATUS_EMBEDDING, STATUS_EMBEDDED, STATUS_FAILED
    #       - Knowledge Reference 파일 (document_type='manual', 'glossary', 'plc'):
    #         STATUS_EMBEDDING, STATUS_EMBEDDED, STATUS_FAILED, STATUS_COMPLETED
    #         (전처리 없이 바로 임베딩)
    #       - 다른 파일(ladder_logic_zip, comment, template): None
    status = Column(
        'STATUS',
        String(20),
        nullable=True,
        comment=(
            "전처리 및 벡터 임베딩 상태: "
            "preprocessed (JSON만), embedding, embedded, failed, completed "
            "(JSON 파일 및 Knowledge Reference 파일만 사용)"
        )
    )
    total_pages = Column('TOTAL_PAGES', Integer, default=0, nullable=True)
    processed_pages = Column('PROCESSED_PAGES', Integer, default=0, nullable=True)
    error_message = Column('ERROR_MESSAGE', Text, nullable=True)
    
    # 벡터화 정보
    milvus_collection_name = Column('MILVUS_COLLECTION_NAME', String(255), nullable=True)
    vector_count = Column('VECTOR_COUNT', Integer, default=0, nullable=True)
    
    # 문서 메타데이터
    language = Column('LANGUAGE', String(10), nullable=True)
    author = Column('AUTHOR', String(255), nullable=True)
    subject = Column('SUBJECT', String(500), nullable=True)
    
    # JSON 필드
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    processing_config = Column('PROCESSING_CONFIG', JSON, nullable=True)
    permissions = Column('PERMISSIONS', JSON, nullable=True)  # 권한 리스트 (string array)
    
    # 시간 정보
    create_dt = Column('CREATE_DT', DateTime, nullable=False, server_default=func.now())
    updated_at = Column('UPDATED_AT', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    processed_at = Column('PROCESSED_AT', DateTime, nullable=True)
    
    # 삭제 플래그
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false())

    # Program 관련 필드
    # Foreign Key 제약조건은 데이터베이스 레벨에서 수동으로 생성
    # (다른 Base의 테이블을 참조하므로 SQLAlchemy가 자동으로 생성하지 못함)
    program_id = Column('PROGRAM_ID', String(50), nullable=True, index=True)
    source_document_id = Column('SOURCE_DOCUMENT_ID', String(50), nullable=True, index=True)  # ForeignKey('DOCUMENTS.DOCUMENT_ID') - DB 레벨에서 수동 생성
    # Knowledge Reference 관련 필드
    knowledge_reference_id = Column('KNOWLEDGE_REFERENCE_ID', String(50), nullable=True, index=True)  # ForeignKey('KNOWLEDGE_REFERENCES.REFERENCE_ID') - DB 레벨에서 수동 생성
    file_id = Column('FILE_ID', String(255), nullable=True)

    def __repr__(self):
        return f"<Document(document_id='{self.document_id}', name='{self.document_name}', status='{self.status}')>"
    
    @classmethod
    def get_valid_document_types(cls) -> list:
        """유효한 문서 타입 목록 반환"""
        return cls.VALID_DOCUMENT_TYPES.copy()
    
    def has_permission(self, required_permission: str) -> bool:
        """특정 권한 보유 여부 확인"""
        if not self.permissions:
            return False
        return required_permission in self.permissions
    
    def has_permissions(self, required_permissions: list, require_all: bool = False) -> bool:
        """여러 권한 보유 여부 확인"""
        if not self.permissions:
            return False
        
        if require_all:
            return all(perm in self.permissions for perm in required_permissions)
        else:
            return any(perm in self.permissions for perm in required_permissions)


class DocumentChunk(Base):
    """문서 청크 정보 테이블"""
    __tablename__ = "DOCUMENT_CHUNKS"
    
    # 기본 필드
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(String(255), unique=True, nullable=False)  # 고유한 청크 ID
    doc_id = Column(String(255), nullable=False)  # 참조하는 문서 ID (Document.document_id와 연결)
    
    # 청크 정보
    page_number = Column(Integer, nullable=False)
    chunk_type = Column(String(50), nullable=False)  # text, image, combined
    content = Column(Text)                           # 텍스트 내용
    image_description = Column(Text)                 # 이미지 설명
    image_path = Column(String(500))                 # 이미지 파일 경로
    
    # 벡터 정보
    milvus_id = Column(String(255))          # Milvus에서의 ID
    embedding_model = Column(String(100))    # 사용된 임베딩 모델
    vector_dimension = Column(Integer)       # 벡터 차원
    
    # 메타데이터
    char_count = Column(Integer)             # 텍스트 길이
    word_count = Column(Integer)             # 단어 수
    language = Column(String(10))            # 언어
    
    # 추가 정보
    metadata_json = Column(JSON)             # 기타 메타데이터
    
    # 시간 정보
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DocumentChunk(chunk_id='{self.chunk_id}', doc_id='{self.doc_id}', type='{self.chunk_type}')>"


class ProcessingJob(Base):
    """처리 작업 로그 테이블"""
    __tablename__ = "PROCESSING_JOBS"
    
    # 기본 필드
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), unique=True, nullable=False)
    doc_id = Column(String(255), nullable=False)  # 처리하는 문서 ID
    
    # 작업 정보
    job_type = Column(String(50), nullable=False)  # embedding, processing, etc.
    status = Column(String(20), nullable=False, default='running')  # running, completed, failed
    flow_run_id = Column(String(255), nullable=True)  # Prefect Flow Run ID
    
    # 진행 상황
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    current_step = Column(String(255), nullable=True)
    
    # 결과 정보
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Program 참조 (ERD에 추가됨)
    program_id = Column("PROGRAM_ID", String(50), ForeignKey("PROGRAMS.PROGRAM_ID"), nullable=True, index=True)
    
    # 시간 정보
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ProcessingJob(job_id='{self.job_id}', doc_id='{self.doc_id}', status='{self.status}')>"


# 기존 코드와의 호환성을 위한 별칭들
DocumentMetadata = Document
