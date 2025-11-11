# _*_ coding: utf-8 _*_
"""Template CRUD operations with database."""
import logging
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.template_models import Template, TemplateData
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class TemplateCRUD:
    """Template 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_template(
        self,
        template_id: str,
        document_id: str,
        created_by: str,
        program_id: Optional[str] = None,
        metadata_json: Optional[Dict] = None,
    ) -> Template:
        """템플릿 생성"""
        try:
            template = Template(
                template_id=template_id,
                document_id=document_id,
                program_id=program_id,
                metadata_json=metadata_json,
                created_by=created_by,
            )
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            return template
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_template(self, template_id: str) -> Optional[Template]:
        """템플릿 조회"""
        try:
            return (
                self.db.query(Template)
                .filter(Template.template_id == template_id)
                .first()
            )
        except Exception as e:
            logger.error(f"템플릿 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_templates_by_program(
        self, program_id: str
    ) -> List[Template]:
        """프로그램별 템플릿 목록 조회"""
        try:
            return (
                self.db.query(Template)
                .filter(Template.program_id == program_id)
                .order_by(desc(Template.created_at))
                .all()
            )
        except Exception as e:
            logger.error(f"프로그램별 템플릿 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_template(
        self, template_id: str, **kwargs
    ) -> bool:
        """템플릿 정보 업데이트"""
        try:
            template = self.get_template(template_id)
            if template:
                for key, value in kwargs.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_template(self, template_id: str) -> bool:
        """템플릿 삭제"""
        try:
            template = self.get_template(template_id)
            if template:
                self.db.delete(template)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)


class TemplateDataCRUD:
    """TemplateData 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_template_data(
        self,
        template_data_id: str,
        template_id: str,
        logic_id: str,
        logic_name: str,
        row_index: int,
        folder_id: Optional[str] = None,
        folder_name: Optional[str] = None,
        sub_folder_name: Optional[str] = None,
        document_id: Optional[str] = None,
        metadata_json: Optional[Dict] = None,
    ) -> TemplateData:
        """템플릿 데이터 생성"""
        try:
            template_data = TemplateData(
                template_data_id=template_data_id,
                template_id=template_id,
                folder_id=folder_id,
                folder_name=folder_name,
                sub_folder_name=sub_folder_name,
                logic_id=logic_id,
                logic_name=logic_name,
                document_id=document_id,
                row_index=row_index,
                metadata_json=metadata_json,
            )
            self.db.add(template_data)
            self.db.commit()
            self.db.refresh(template_data)
            return template_data
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 데이터 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_template_data(
        self, template_data_id: str
    ) -> Optional[TemplateData]:
        """템플릿 데이터 조회"""
        try:
            return (
                self.db.query(TemplateData)
                .filter(TemplateData.template_data_id == template_data_id)
                .first()
            )
        except Exception as e:
            logger.error(f"템플릿 데이터 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_template_data_by_template(
        self, template_id: str
    ) -> List[TemplateData]:
        """템플릿별 데이터 목록 조회"""
        try:
            return (
                self.db.query(TemplateData)
                .filter(TemplateData.template_id == template_id)
                .order_by(TemplateData.row_index)
                .all()
            )
        except Exception as e:
            logger.error(f"템플릿별 데이터 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def count_template_data_by_program(
        self, program_id: str
    ) -> int:
        """프로그램별 템플릿 데이터 개수 조회"""
        try:
            return (
                self.db.query(TemplateData)
                .join(Template, TemplateData.template_id == Template.template_id)
                .filter(Template.program_id == program_id)
                .count()
            )
        except Exception as e:
            logger.error(
                f"프로그램별 템플릿 데이터 개수 조회 실패: {str(e)}"
            )
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_template_data(
        self, template_data_id: str, **kwargs
    ) -> bool:
        """템플릿 데이터 업데이트"""
        try:
            template_data = self.get_template_data(template_data_id)
            if template_data:
                for key, value in kwargs.items():
                    if hasattr(template_data, key):
                        setattr(template_data, key, value)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 데이터 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_template_data(self, template_data_id: str) -> bool:
        """템플릿 데이터 삭제"""
        try:
            template_data = self.get_template_data(template_data_id)
            if template_data:
                self.db.delete(template_data)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"템플릿 데이터 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

