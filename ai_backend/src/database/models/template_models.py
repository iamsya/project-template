# _*_ coding: utf-8 _*_
"""
Template, TemplateData 모델 정의
템플릿 및 템플릿 데이터 테이블
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, func

from src.database.base import Base


class Template(Base):
    """템플릿 테이블"""
    __tablename__ = "TEMPLATES"
    
    # 기본 정보
    template_id = Column('TEMPLATE_ID', String(50), primary_key=True)
    document_id = Column('DOCUMENT_ID', String(50), ForeignKey('DOCUMENTS.DOCUMENT_ID'), nullable=False, index=True)
    program_id = Column('PROGRAM_ID', String(50), ForeignKey('PROGRAMS.PROGRAM_ID'), nullable=True, index=True)
    
    # 메타데이터
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 시간 정보
    created_at = Column('CREATED_AT', DateTime, nullable=False, server_default=func.now())
    created_by = Column('CREATED_BY', String(50), nullable=False)

    def __repr__(self):
        return f"<Template(template_id='{self.template_id}', document_id='{self.document_id}')>"


class TemplateData(Base):
    """템플릿 데이터 테이블"""
    __tablename__ = "TEMPLATE_DATA"
    
    # 기본 정보
    template_data_id = Column('TEMPLATE_DATA_ID', String(50), primary_key=True)
    template_id = Column('TEMPLATE_ID', String(50), ForeignKey('TEMPLATES.TEMPLATE_ID'), nullable=False, index=True)
    
    # 폴더 정보
    folder_id = Column('FOLDER_ID', String(100), nullable=True, index=True)
    folder_name = Column('FOLDER_NAME', String(200), nullable=True)
    sub_folder_name = Column('SUB_FOLDER_NAME', String(200), nullable=True)
    
    # 로직 정보
    logic_id = Column('LOGIC_ID', String(100), nullable=False, index=True)
    logic_name = Column('LOGIC_NAME', String(200), nullable=False)
    
    # 문서 참조
    document_id = Column('DOCUMENT_ID', String(50), ForeignKey('DOCUMENTS.DOCUMENT_ID'), nullable=True, index=True)
    row_index = Column('ROW_INDEX', Integer, nullable=False)
    
    # 메타데이터
    metadata_json = Column('METADATA_JSON', JSON, nullable=True)
    
    # 시간 정보
    created_at = Column('CREATED_AT', DateTime, nullable=False, server_default=func.now())

    def __repr__(self):
        return f"<TemplateData(template_data_id='{self.template_data_id}', template_id='{self.template_id}', logic_id='{self.logic_id}')>"

