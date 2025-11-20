# _*_ coding: utf-8 _*_
"""
KnowledgeReference 모델 정의
Knowledge Base 참조 정보 테이블 (매뉴얼, 용어집, PLC 레포)
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import false, true

from src.database.base import Base


class KnowledgeReference(Base):
    """Knowledge Base 참조 정보 테이블 (매뉴얼, 용어집, PLC/Ladder Logic)"""
    __tablename__ = "KNOWLEDGE_REFERENCES"
    
    # 기본 정보
    reference_id = Column('REFERENCE_ID', String(50), primary_key=True)
    # 기준정보 종류
    # 주의: DOCUMENTS.document_type과는 다른 용도
    #       - reference_type: 기준정보(Knowledge Reference)의 종류
    #         (manual, glossary, plc)
    #       - document_type: 모든 Document의 일반 분류 (common, type1, type2)
    reference_type = Column(
        'REFERENCE_TYPE',
        String(50),
        nullable=False,
        index=True,
        comment=(
            "기준정보 종류: "
            "manual(매뉴얼), glossary(용어집), "
            "plc(Ladder Logic - 프로그램 JSON 파일 벡터)"
        )
    )
    name = Column('NAME', String(255), nullable=False)
    version = Column('VERSION', String(50), nullable=True)
    is_latest = Column('IS_LATEST', Boolean, nullable=False, server_default=false())
    
    # 레포 내 데이터 삭제 여부
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false())
    
    # 레포 및 데이터소스 정보
    repo_id = Column(
        'REPO_ID', String(255), nullable=True, index=True
    )
    datasource_id = Column(
        'DATASOURCE_ID', String(255), nullable=True, index=True
    )

    # 설명 및 메타데이터
    description = Column('DESCRIPTION', Text, nullable=True)
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)

    # 처리 상태
    status = Column(
        'STATUS',
        String(50),
        nullable=False,
        default='preparing',
        server_default='preparing',
        index=True,
        comment="처리 상태: preparing, processing, completed, failed"
    )
    error_message = Column('ERROR_MESSAGE', Text, nullable=True)

    # 활성화 여부
    is_active = Column(
        'IS_ACTIVE', Boolean, nullable=False, server_default=true()
    )
    
    # 완료 시간
    completed_at = Column('COMPLETED_AT', DateTime, nullable=True)

    # 시간 정보
    created_at = Column(
        'CREATED_AT', DateTime, nullable=False, server_default=func.now()
    )
    created_by = Column('CREATED_BY', String(50), nullable=False)
    updated_at = Column(
        'UPDATED_AT',
        DateTime,
        nullable=True,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    updated_by = Column('UPDATED_BY', String(50), nullable=True)

    # reference_type 상수
    REFERENCE_TYPE_MANUAL = "manual"
    REFERENCE_TYPE_GLOSSARY = "glossary"
    REFERENCE_TYPE_PLC = "plc"  # Ladder Logic (프로그램 JSON 파일 벡터)

    # 상태 상수
    STATUS_PREPARING = "preparing"
    STATUS_PROCESSING = "processing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __repr__(self):
        return (
            f"<KnowledgeReference(reference_id='{self.reference_id}', "
            f"name='{self.name}', type='{self.reference_type}', "
            f"status='{self.status}')>"
        )

