# _*_ coding: utf-8 _*_
"""KnowledgeReference CRUD operations with database."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.knowledge_reference_models import KnowledgeReference
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class KnowledgeReferenceCRUD:
    """KnowledgeReference 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_reference(
        self,
        reference_id: str,
        reference_type: str,
        name: str,
        repo_id: str,
        datasource_id: str,
        created_by: str,
        version: Optional[str] = None,
        description: Optional[str] = None,
        file_id: Optional[str] = None,
        is_latest: bool = False,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> KnowledgeReference:
        """Knowledge 참조 정보 생성"""
        try:
            reference = KnowledgeReference(
                reference_id=reference_id,
                reference_type=reference_type,
                name=name,
                version=version,
                repo_id=repo_id,
                datasource_id=datasource_id,
                file_id=file_id,
                description=description,
                is_latest=is_latest,
                is_active=is_active,
                metadata_json=metadata_json,
                created_by=created_by,
            )
            self.db.add(reference)
            self.db.commit()
            self.db.refresh(reference)
            return reference
        except Exception as e:
            self.db.rollback()
            logger.error(f"Knowledge 참조 정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_reference(self, reference_id: str) -> Optional[KnowledgeReference]:
        """Knowledge 참조 정보 조회"""
        try:
            return (
                self.db.query(KnowledgeReference)
                .filter(KnowledgeReference.reference_id == reference_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Knowledge 참조 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_latest_reference(
        self, reference_type: str
    ) -> Optional[KnowledgeReference]:
        """최신 버전 조회"""
        try:
            return (
                self.db.query(KnowledgeReference)
                .filter(KnowledgeReference.reference_type == reference_type)
                .filter(KnowledgeReference.is_latest.is_(True))
                .filter(KnowledgeReference.is_active.is_(True))
                .order_by(desc(KnowledgeReference.created_at))
                .first()
            )
        except Exception as e:
            logger.error(f"최신 Knowledge 참조 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_references_by_type(
        self, reference_type: str, include_inactive: bool = False
    ) -> List[KnowledgeReference]:
        """타입별 참조 정보 목록 조회"""
        try:
            query = self.db.query(KnowledgeReference).filter(
                KnowledgeReference.reference_type == reference_type
            )
            if not include_inactive:
                query = query.filter(KnowledgeReference.is_active.is_(True))
            return query.order_by(desc(KnowledgeReference.created_at)).all()
        except Exception as e:
            logger.error(f"타입별 참조 정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_reference(
        self, reference_id: str, updated_by: Optional[str] = None, **kwargs
    ) -> bool:
        """Knowledge 참조 정보 업데이트"""
        try:
            reference = self.get_reference(reference_id)
            if reference:
                for key, value in kwargs.items():
                    if hasattr(reference, key):
                        setattr(reference, key, value)
                reference.updated_at = datetime.now()
                if updated_by:
                    reference.updated_by = updated_by
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Knowledge 참조 정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def set_as_latest(
        self, reference_id: str, update_by: Optional[str] = None
    ) -> bool:
        """최신 버전 설정"""
        try:
            reference = self.get_reference(reference_id)
            if reference:
                # 같은 타입의 다른 레퍼런스들의 is_latest를 False로 설정
                self.db.query(KnowledgeReference).filter(
                    KnowledgeReference.reference_type == reference.reference_type
                ).filter(
                    KnowledgeReference.reference_id != reference_id
                ).update({"is_latest": False})
                # 현재 레퍼런스를 최신으로 설정
                reference.is_latest = True
                reference.updated_at = datetime.now()
                if update_by:
                    reference.updated_by = update_by
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"최신 버전 설정 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_reference(self, reference_id: str) -> bool:
        """Knowledge 참조 정보 삭제 (소프트 삭제: is_active=False)"""
        try:
            reference = self.get_reference(reference_id)
            if reference:
                reference.is_active = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Knowledge 참조 정보 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
