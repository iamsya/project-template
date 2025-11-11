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
    """Knowledge Base 참조 정보 테이블 (매뉴얼, 용어집, PLC 레포)"""
    __tablename__ = "KNOWLEDGE_REFERENCES"
    
    # 기본 정보
    reference_id = Column('REFERENCE_ID', String(50), primary_key=True)
    reference_type = Column('REFERENCE_TYPE', String(50), nullable=False, index=True)  # manual, glossary, plc
    name = Column('NAME', String(255), nullable=False)
    version = Column('VERSION', String(50), nullable=True)
    is_latest = Column('IS_LATEST', Boolean, nullable=False, server_default=false())
    
    # 레포 내 데이터 삭제 여부
    is_deleted = Column('IS_DELETED', Boolean, nullable=False, server_default=false())
    
    # 레포 및 데이터소스 정보
    repo_id = Column(
        'REPO_ID', String(255), nullable=False, index=True
    )
    datasource_id = Column(
        'DATASOURCE_ID', String(255), nullable=False, index=True
    )

    # 설명 및 메타데이터
    description = Column('DESCRIPTION', Text, nullable=True)
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)

    # 활성화 여부
    is_active = Column(
        'IS_ACTIVE', Boolean, nullable=False, server_default=true()
    )

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

    def __repr__(self):
        return f"<KnowledgeReference(reference_id='{self.reference_id}', name='{self.name}', type='{self.reference_type}')>"

