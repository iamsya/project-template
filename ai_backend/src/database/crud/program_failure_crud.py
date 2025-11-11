# _*_ coding: utf-8 _*_
"""Program Failure CRUD operations with database.
ProcessingFailure 모델 관련 CRUD 작업
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.program_models import ProcessingFailure
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class ProcessingFailureCRUD:
    """ProcessingFailure 관련 CRUD  작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_failure(
        self,
        failure_id: str,
        source_type: str,
        source_id: str,
        failure_type: str,
        error_message: str,
        filename: Optional[str] = None,
        file_path: Optional[str] = None,
        file_index: Optional[int] = None,
        s3_path: Optional[str] = None,
        s3_key: Optional[str] = None,
        error_details: Optional[Dict] = None,
        retry_count: int = 0,
        max_retry_count: int = 3,
        status: str = "pending",
        metadata_json: Optional[Dict] = None,
    ) -> ProcessingFailure:
        """실패 정보 생성
        
        Args:
            source_type: 소스 타입 ('program', 'knowledge_reference' 등)
            source_id: 소스 ID (program_id, reference_id 등)
        """
        try:
            failure = ProcessingFailure(
                failure_id=failure_id,
                source_type=source_type,
                source_id=source_id,
                failure_type=failure_type,
                error_message=error_message,
                filename=filename,
                file_path=file_path,
                file_index=file_index,
                s3_path=s3_path,
                s3_key=s3_key,
                error_details=error_details,
                retry_count=retry_count,
                max_retry_count=max_retry_count,
                status=status,
                metadata_json=metadata_json,
            )
            self.db.add(failure)
            self.db.commit()
            self.db.refresh(failure)
            return failure
        except Exception as e:
            self.db.rollback()
            logger.error(f"실패 정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_failure(self, failure_id: str) -> Optional[ProcessingFailure]:
        """실패 정보 조회"""
        try:
            return (
                self.db.query(ProcessingFailure)
                .filter(ProcessingFailure.failure_id == failure_id)
                .first()
            )
        except Exception as e:
            logger.error(f"실패 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_source_failures(
        self,
        source_type: str,
        source_id: str,
        failure_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProcessingFailure]:
        """소스의 실패 정보 목록 조회 (다형성 관계)"""
        try:
            query = (
                self.db.query(ProcessingFailure)
                .filter(ProcessingFailure.source_type == source_type)
                .filter(ProcessingFailure.source_id == source_id)
            )
            if failure_type:
                query = query.filter(
                    ProcessingFailure.failure_type == failure_type
                )
            if status:
                query = query.filter(ProcessingFailure.status == status)
            return query.order_by(desc(ProcessingFailure.created_at)).all()
        except Exception as e:
            logger.error(f"소스 실패 정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_program_failures(
        self,
        program_id: str,
        failure_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProcessingFailure]:
        """프로그램의 실패 정보 목록 조회 (편의 메서드)"""
        return self.get_source_failures(
            source_type=ProcessingFailure.SOURCE_TYPE_PROGRAM,
            source_id=program_id,
            failure_type=failure_type,
            status=status,
        )

    def get_knowledge_reference_failures(
        self,
        reference_id: str,
        failure_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[ProcessingFailure]:
        """Knowledge Reference의 실패 정보 목록 조회 (편의 메서드)"""
        return self.get_source_failures(
            source_type=ProcessingFailure.SOURCE_TYPE_KNOWLEDGE_REFERENCE,
            source_id=reference_id,
            failure_type=failure_type,
            status=status,
        )

    def get_pending_failures(
        self,
        failure_type: Optional[str] = None,
        max_retry_count: Optional[int] = None,
    ) -> List[ProcessingFailure]:
        """재시도 대기 중인 실패 정보 조회"""
        try:
            query = self.db.query(ProcessingFailure).filter(
                ProcessingFailure.status == ProcessingFailure.STATUS_PENDING
            )
            if failure_type:
                query = query.filter(
                    ProcessingFailure.failure_type == failure_type
                )
            if max_retry_count is not None:
                query = query.filter(
                    ProcessingFailure.retry_count < max_retry_count
                )
            return query.order_by(ProcessingFailure.created_at).all()
        except Exception as e:
            logger.error(f"재시도 대기 실패 정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_failure_status(
        self,
        failure_id: str,
        status: str,
        error_message: Optional[str] = None,
        resolved_by: Optional[str] = None,
    ) -> bool:
        """실패 정보 상태 업데이트"""
        try:
            failure = self.get_failure(failure_id)
            if failure:
                failure.status = status
                if error_message:
                    failure.error_message = error_message
                if status == ProcessingFailure.STATUS_RESOLVED:
                    failure.resolved_at = datetime.now()
                    if resolved_by:
                        failure.resolved_by = resolved_by
                failure.updated_at = datetime.now()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"실패 정보 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def increment_retry_count(self, failure_id: str) -> bool:
        """재시도 횟수 증가"""
        try:
            failure = self.get_failure(failure_id)
            if failure:
                failure.retry_count += 1
                failure.last_retry_at = datetime.now()
                failure.updated_at = datetime.now()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"재시도 횟수 증가 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def mark_as_resolved(
        self, failure_id: str, resolved_by: str = "manual"
    ) -> bool:
        """실패 정보를 해결됨으로 표시"""
        try:
            return self.update_failure_status(
                failure_id,
                ProcessingFailure.STATUS_RESOLVED,
                resolved_by=resolved_by,
            )
        except Exception as e:
            logger.error(f"실패 정보 해결 처리 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_failure(self, failure_id: str) -> bool:
        """실패 정보 삭제"""
        try:
            failure = self.get_failure(failure_id)
            if failure:
                self.db.delete(failure)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"실패 정보 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
