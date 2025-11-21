# _*_ coding: utf-8 _*_
"""Document CRUD operations with database."""
import logging
from datetime import datetime
from typing import List, Optional

from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from sqlalchemy.orm import Session

# 공통 모듈 사용
from shared_core import DocumentCRUD as BaseDocumentCRUD
# ai_backend의 Document 모델 사용 (Foreign Key 제약조건 포함)
from src.database.models.document_models import Document

logger = logging.getLogger(__name__)


class DocumentCRUD(BaseDocumentCRUD):
    """Document 관련 CRUD 작업을 처리하는 클래스 (FastAPI 전용 확장)
    
    shared_core의 DocumentCRUD를 상속받되, ai_backend의 Document 모델을 사용합니다.
    이를 통해 Foreign Key 제약조건이 작동합니다.
    
    주의: 이 클래스는 shared_core.crud 모듈의 Document 참조를 ai_backend의 Document로
    교체합니다. ai_backend 내에서만 사용해야 합니다.
    """
    
    def __init__(self, db: Session):
        # shared_core.crud 모듈의 Document 참조를 ai_backend의 Document로 교체
        # 이를 통해 부모 클래스의 모든 메서드가 ai_backend의 Document를 사용하게 됩니다.
        import shared_core.crud as shared_crud_module
        shared_crud_module.Document = Document
        super().__init__(db)
    
    # 모든 메서드는 부모 클래스에서 상속받되, 예외 처리만 FastAPI 전용으로 오버라이드
    # create_document는 ai_backend의 Document 모델을 사용하도록 오버라이드
    
    def create_document(
        self,
        document_id: str,
        document_name: str,
        file_extension: str,
        user_id: str,
        original_filename: Optional[str] = None,
        upload_path: Optional[str] = None,
        file_key: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        is_public: bool = False,
        status: str = 'processing',
        error_message: str = None,
        file_hash: str = None,
        total_pages: int = None,
        processed_pages: int = None,
        milvus_collection_name: str = None,
        vector_count: int = None,
        language: str = None,
        author: str = None,
        subject: str = None,
        metadata_json: dict = None,
        processing_config: dict = None,
        processed_at: datetime = None,
        permissions: List[str] = None,
        document_type: str = 'common',
        program_id: str = None,
        source_document_id: str = None,
        knowledge_reference_id: str = None,
    ) -> Document:
        """문서 생성 (ai_backend의 Document 모델 사용, FastAPI 예외 처리)"""
        try:
            # ai_backend의 Document 모델 사용 (Foreign Key 제약조건 포함)
            document = Document(
                document_id=document_id,
                document_name=document_name,
                original_filename=original_filename,
                file_key=file_key,
                file_size=file_size,
                file_type=file_type,
                file_extension=file_extension,
                user_id=user_id,
                upload_path=upload_path,
                status=status,
                error_message=error_message,
                is_public=is_public,
                file_hash=file_hash,
                total_pages=total_pages,
                processed_pages=processed_pages,
                milvus_collection_name=milvus_collection_name,
                vector_count=vector_count,
                language=language,
                author=author,
                subject=subject,
                metadata_json=metadata_json,
                processing_config=processing_config,
                processed_at=processed_at,
                permissions=permissions,
                document_type=document_type,
                program_id=program_id,
                source_document_id=source_document_id,
                knowledge_reference_id=knowledge_reference_id,
                create_dt=datetime.now()
            )
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            return document
        except Exception as e:
            self.db.rollback()
            logger.error(f"문서 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_document(self, document_id: str):
        """문서 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_document(document_id)
        except Exception as e:
            logger.error(f"문서 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_user_documents(self, user_id: str):
        """사용자의 문서 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_user_documents(user_id)
        except Exception as e:
            logger.error(f"사용자 문서 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def search_documents(self, user_id: str, search_term: str):
        """문서 검색 (FastAPI 예외 처리)"""
        try:
            return super().search_documents(user_id, search_term)
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_document(self, document_id: str, **kwargs):
        """문서 정보 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_document(document_id, **kwargs)
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_document_status(self, document_id: str, status: str, error_message: str = None):
        """문서 상태 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_document_status(document_id, status, error_message)
        except Exception as e:
            logger.error(f"문서 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_processing_info(self, document_id: str, **kwargs):
        """문서 처리 정보 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_processing_info(document_id, **kwargs)
        except Exception as e:
            logger.error(f"문서 처리 정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def find_document_by_hash(self, file_hash: str, status_filter: str = None):
        """파일 해시를 기반으로 기존 문서 검색 (FastAPI 예외 처리)"""
        try:
            return super().find_document_by_hash(file_hash, status_filter)
        except Exception as e:
            logger.error(f"해시 기반 문서 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def find_completed_document_by_hash(self, file_hash: str):
        """완료된 상태의 기존 문서 검색 (FastAPI 예외 처리)"""
        try:
            return super().find_completed_document_by_hash(file_hash)
        except Exception as e:
            logger.error(f"완료된 문서 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def check_document_permission(self, document_id: str, required_permission: str):
        """문서의 특정 권한 체크 (FastAPI 예외 처리)"""
        try:
            return super().check_document_permission(document_id, required_permission)
        except Exception as e:
            logger.error(f"문서 권한 체크 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def check_document_permissions(self, document_id: str, required_permissions, require_all: bool = False):
        """문서의 여러 권한 체크 (FastAPI 예외 처리)"""
        try:
            return super().check_document_permissions(document_id, required_permissions, require_all)
        except Exception as e:
            logger.error(f"문서 권한들 체크 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_document_permissions(self, document_id: str, permissions):
        """문서 권한 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_document_permissions(document_id, permissions)
        except Exception as e:
            logger.error(f"문서 권한 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def add_document_permission(self, document_id: str, permission: str):
        """문서에 권한 추가 (FastAPI 예외 처리)"""
        try:
            return super().add_document_permission(document_id, permission)
        except Exception as e:
            logger.error(f"문서 권한 추가 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def remove_document_permission(self, document_id: str, permission: str):
        """문서에서 권한 제거 (FastAPI 예외 처리)"""
        try:
            return super().remove_document_permission(document_id, permission)
        except Exception as e:
            logger.error(f"문서 권한 제거 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_documents_with_permission(self, user_id: str, required_permission: str):
        """특정 권한을 가진 사용자 문서 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_documents_with_permission(user_id, required_permission)
        except Exception as e:
            logger.error(f"권한별 문서 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_documents_by_type(self, user_id: str, document_type: str):
        """특정 문서 타입의 사용자 문서 목록 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_documents_by_type(user_id, document_type)
        except Exception as e:
            logger.error(f"타입별 문서 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def update_document_type(self, document_id: str, document_type: str):
        """문서 타입 업데이트 (FastAPI 예외 처리)"""
        try:
            return super().update_document_type(document_id, document_type)
        except ValueError as e:
            logger.error(f"문서 타입 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, msg=str(e))
        except Exception as e:
            logger.error(f"문서 타입 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_document_type_stats(self, user_id: str):
        """사용자의 문서 타입별 통계 조회 (FastAPI 예외 처리)"""
        try:
            return super().get_document_type_stats(user_id)
        except Exception as e:
            logger.error(f"문서 타입별 통계 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def delete_document(self, document_id: str):
        """문서 삭제 (FastAPI 예외 처리)"""
        try:
            return super().delete_document(document_id)
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)