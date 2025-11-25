# _*_ coding: utf-8 _*_
"""Document Service for handling file uploads and management."""
import hashlib
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.config.simple_settings import settings
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.database.models.document_models import Document
from src.database.crud.document_crud import DocumentCRUD
from shared_core import ProcessingJobService

logger = logging.getLogger(__name__)


class DocumentService:
    """문서 관리 서비스 (ai_backend 전용)
    
    shared_core의 DocumentCRUD를 래핑한 DocumentCRUD를 사용합니다.
    shared_core의 Document 모델을 사용하며, programs-document 외래키는 없습니다.
    """
    
    def __init__(self, db: Session, upload_base_path: str = None):
        self.db = db
        # 환경변수에서 업로드 경로 가져오기 (k8s 환경 대응)
        upload_path = upload_base_path or settings.upload_base_path
        self.upload_base_path = Path(upload_path)
        self.upload_base_path.mkdir(parents=True, exist_ok=True)
        # ai_backend의 DocumentCRUD 사용
        self.document_crud = DocumentCRUD(db)
    
    def _get_file_extension(self, filename: str) -> str:
        """파일 확장자 추출 (. 제거)"""
        return Path(filename).suffix.lower().lstrip('.')
    
    def _get_mime_type(self, filename: str) -> str:
        """MIME 타입 추출"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
    
    def _calculate_file_hash(self, file_content: bytes) -> str:
        """파일 해시값 계산 (MD5, 4096 바이트 청크 단위)"""
        hash_md5 = hashlib.md5()
        # 4096 바이트씩 청크 단위로 해시 계산
        for i in range(0, len(file_content), 4096):
            chunk = file_content[i:i+4096]
            hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _generate_file_key(self, user_id: str, filename: str = None) -> str:
        """파일 키 생성 (저장 경로)"""
        # 폴더 구조: uploads/user_id/filename
        return f"{user_id}/{filename}"
    
    def _get_upload_path(self, file_key: str) -> Path:
        """실제 업로드 경로 생성"""
        return self.upload_base_path / file_key
    
    def _document_to_dict(self, document: Document, is_duplicate: bool = False) -> Dict:
        """Document 객체를 딕셔너리로 변환"""
        return {
            "document_id": document.document_id,
            "document_name": document.document_name,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "file_type": document.file_type,
            "file_extension": document.file_extension,
            "file_hash": document.file_hash,
            "upload_path": document.upload_path,
            "is_public": document.is_public,
            "status": document.status,
            "total_pages": document.total_pages,
            "processed_pages": document.processed_pages,
            "vector_count": document.vector_count,
            "milvus_collection_name": document.milvus_collection_name,
            "language": document.language,
            "author": document.author,
            "subject": document.subject,
            "metadata_json": document.metadata_json,
            "processing_config": document.processing_config,
            "permissions": document.permissions or [],
            "document_type": document.document_type or 'common',
            "create_dt": document.create_dt.isoformat() if document.create_dt else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "is_duplicate": is_duplicate
        }
    
    def create_document_from_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = Document.TYPE_COMMON,
        **additional_metadata
    ) -> Dict:
        """파일 내용으로부터 문서 생성"""
        try:
            # 파일 정보 추출
            file_extension = self._get_file_extension(filename)
            file_type = self._get_mime_type(filename)
            file_size = len(file_content)
            file_hash = self._calculate_file_hash(file_content)
            
            # 중복 파일 체크
            existing_doc = self.document_crud.find_document_by_hash(file_hash)
            if existing_doc and existing_doc.status == 'completed':
                logger.info(f"📋 완료된 기존 문서 발견: {existing_doc.document_id}")
                return self._document_to_dict(existing_doc, is_duplicate=True)
            
            # 고유한 문서 ID 생성
            if existing_doc and existing_doc.status in ['processing', 'failed']:
                document_id = existing_doc.document_id
                logger.info(f"🔄 기존 문서 재처리: {document_id}")
            else:
                document_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_hash[:8]}"
            
            # 파일 저장
            file_key = self._generate_file_key(user_id, filename)
            upload_path = self._get_upload_path(file_key)
            
            # 디렉토리 생성
            upload_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 파일 저장
            with open(upload_path, "wb") as f:
                f.write(file_content)
            
            # DB에 메타데이터 저장
            if existing_doc and existing_doc.status in ['failed', 'processing']:
                # 기존 문서 업데이트
                self.document_crud.update_document(
                    document_id,
                    document_name=filename,
                    original_filename=filename,
                    file_key=file_key,
                    file_size=file_size,
                    file_type=file_type,
                    file_extension=file_extension,
                    user_id=user_id,
                    upload_path=str(upload_path),
                    is_public=is_public,
                    status='processing',
                    permissions=permissions,
                    document_type=document_type,
                    **additional_metadata
                )
                document = self.document_crud.get_document(document_id)
            else:
                # 새 문서 생성
                document = self.document_crud.create_document(
                    document_id=document_id,
                    document_name=filename,
                    original_filename=filename,
                    file_key=file_key,
                    file_size=file_size,
                    file_type=file_type,
                    file_extension=file_extension,
                    user_id=user_id,
                    upload_path=str(upload_path),
                    is_public=is_public,
                    file_hash=file_hash,
                    status='processing',
                    permissions=permissions,
                    document_type=document_type,
                    **additional_metadata
                )
            
            return self._document_to_dict(document)
                
        except Exception as e:
            logger.error(f"문서 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def upload_document(
        self,
        file: UploadFile,
        user_id: str,
        is_public: bool = False,
        permissions: List[str] = None,
        document_type: str = Document.TYPE_COMMON
    ) -> Dict:
        """문서 업로드 (FastAPI UploadFile 전용)"""
        try:
            # 문서 타입 검증
            if document_type not in Document.VALID_DOCUMENT_TYPES:
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"유효하지 않은 문서 타입: {document_type}. 허용된 타입: {', '.join(Document.VALID_DOCUMENT_TYPES)}")
            
            # 파일 정보 추출
            original_filename = file.filename
            file_extension = self._get_file_extension(original_filename)
            
            # 파일 크기 확인 (환경변수에서 설정값 가져오기)
            file_content = file.file.read()
            file_size = len(file_content)
            max_size = settings.upload_max_size
            
            if file_size > max_size:
                max_size_mb = settings.get_upload_max_size_mb()
                raise HandledException(ResponseCode.DOCUMENT_FILE_TOO_LARGE, 
                                     msg=f"파일 크기가 너무 큽니다. (최대 {max_size_mb:.1f}MB)")
            
            # 허용된 파일 타입 확인 (환경변수에서 설정값 가져오기)
            allowed_extensions = settings.get_upload_allowed_types()
            
            if file_extension not in allowed_extensions:
                allowed_types_str = ', '.join(allowed_extensions)
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"지원하지 않는 파일 형식입니다. 허용된 형식: {allowed_types_str}")
            
            # 파일 내용으로부터 문서 생성
            result = self.create_document_from_file(
                file_content=file_content,
                filename=original_filename,
                user_id=user_id,
                is_public=is_public,
                permissions=permissions,
                document_type=document_type
            )
            
            return result
                
        except HandledException:
            raise  # HandledException은 그대로 전파
        except Exception as e:
            raise HandledException(ResponseCode.DOCUMENT_UPLOAD_ERROR, e=e)
    
    def get_document(self, document_id: str, user_id: str = None) -> Optional[Dict]:
        """문서 정보 조회"""
        try:
            document = self.document_crud.get_document(document_id)
            
            if not document or document.is_deleted:
                return None
            
            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id and not document.is_public:
                return None
            
            return self._document_to_dict(document)
                
        except Exception as e:
            logger.error(f"문서 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def get_user_documents(self, user_id: str) -> List[Dict]:
        """사용자의 문서 목록 조회"""
        try:
            documents = self.document_crud.get_user_documents(user_id)
            return [self._document_to_dict(doc) for doc in documents]
                
        except Exception as e:
            logger.error(f"사용자 문서 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def search_documents(self, user_id: str, search_term: str) -> List[Dict]:
        """문서 검색"""
        try:
            documents = self.document_crud.search_documents(user_id, search_term)
            return [self._document_to_dict(doc) for doc in documents]
                
        except Exception as e:
            logger.error(f"문서 검색 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def download_document(self, document_id: str, user_id: str = None) -> tuple[bytes, str, str]:
        """문서 다운로드"""
        try:
            document = self.document_crud.get_document(document_id)
            
            if not document or document.is_deleted:
                raise FileNotFoundError("문서를 찾을 수 없습니다.")
            
            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id and not document.is_public:
                raise PermissionError("문서에 접근할 권한이 없습니다.")
            
            # 파일 읽기
            upload_path = Path(document.upload_path)
            if not upload_path.exists():
                raise FileNotFoundError("파일이 존재하지 않습니다.")
            
            with open(upload_path, "rb") as f:
                file_content = f.read()
            
            return file_content, document.original_filename, document.file_type
                
        except FileNotFoundError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="파일이 존재하지 않습니다.")
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"문서 다운로드 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_DOWNLOAD_ERROR, e=e)
    
    def delete_document(self, document_id: str, user_id: str = None) -> bool:
        """문서 삭제"""
        try:
            document = self.document_crud.get_document(document_id)
            
            if not document:
                return False
            
            # 사용자 권한 체크 (user_id가 제공된 경우)
            if user_id and document.user_id != user_id:
                raise PermissionError("문서를 삭제할 권한이 없습니다.")
            
            # DB에서 소프트 삭제
            success = self.document_crud.delete_document(document_id)
            
            # 실제 파일도 삭제 (선택사항)
            if success and document.upload_path:
                upload_path = Path(document.upload_path)
                if upload_path.exists():
                    upload_path.unlink()
            
            return success
                
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"문서 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DOCUMENT_DELETE_ERROR, e=e)
    
    def update_document_processing_status(
        self,
        document_id: str,
        status: str,
        user_id: str = None,
        **processing_info
    ) -> bool:
        """문서 처리 상태 및 정보 업데이트"""
        try:
            # 권한 확인 (user_id가 제공된 경우)
            if user_id:
                document = self.document_crud.get_document(document_id)
                if not document or document.user_id != user_id:
                    raise PermissionError("문서를 수정할 권한이 없습니다.")
            
            # 상태 업데이트
            self.document_crud.update_document_status(document_id, status)
            
            # 추가 처리 정보 업데이트
            if processing_info:
                self.document_crud.update_processing_info(document_id, **processing_info)
            
            return True
            
        except PermissionError:
            raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"문서 처리 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_processing_stats(self, user_id: str) -> Dict:
        """사용자 문서 처리 통계 조회"""
        try:
            documents = self.document_crud.get_user_documents(user_id)
            
            stats = {
                'total_documents': len(documents),
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'total_pages': 0,
                'processed_pages': 0,
                'total_vectors': 0
            }
            
            for doc in documents:
                if doc.status == 'processing':
                    stats['processing'] += 1
                elif doc.status == 'completed':
                    stats['completed'] += 1
                elif doc.status == 'failed':
                    stats['failed'] += 1
                
                if doc.total_pages:
                    stats['total_pages'] += doc.total_pages
                if doc.processed_pages:
                    stats['processed_pages'] += doc.processed_pages
                if doc.vector_count:
                    stats['total_vectors'] += doc.vector_count
            
            # 처리 진행률 계산
            if stats['total_pages'] > 0:
                stats['processing_progress'] = round((stats['processed_pages'] / stats['total_pages']) * 100, 2)
            else:
                stats['processing_progress'] = 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"문서 처리 통계 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    # 권한 관련 메서드들 (기존 인터페이스 유지)
    def check_document_permission(self, document_id: str, user_id: str, required_permission: str) -> bool:
        """문서 권한 체크"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return document.has_permission(required_permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def check_document_permissions(self, document_id: str, user_id: str, required_permissions: List[str], require_all: bool = False) -> bool:
        """문서 여러 권한 체크"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return document.has_permissions(required_permissions, require_all)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def update_document_permissions(self, document_id: str, user_id: str, permissions: List[str]) -> bool:
        """문서 권한 업데이트"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.update_document_permissions(document_id, permissions)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def add_document_permission(self, document_id: str, user_id: str, permission: str) -> bool:
        """문서에 권한 추가"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.add_document_permission(document_id, permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def remove_document_permission(self, document_id: str, user_id: str, permission: str) -> bool:
        """문서에서 권한 제거"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.remove_document_permission(document_id, permission)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_documents_with_permission(self, user_id: str, required_permission: str) -> List[Dict]:
        """특정 권한을 가진 문서 목록 조회"""
        try:
            documents = self.document_crud.get_documents_with_permission(user_id, required_permission)
            return [self._document_to_dict(doc) for doc in documents]
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_documents_by_type(self, user_id: str, document_type: str) -> List[Dict]:
        """특정 문서 타입의 사용자 문서 목록 조회"""
        try:
            # 유효한 타입 검증
            if document_type not in Document.VALID_DOCUMENT_TYPES:
                raise HandledException(ResponseCode.DOCUMENT_INVALID_FILE_TYPE, 
                                     msg=f"유효하지 않은 문서 타입: {document_type}. 허용된 타입: {', '.join(Document.VALID_DOCUMENT_TYPES)}")
            
            documents = self.document_crud.get_documents_by_type(user_id, document_type)
            return [self._document_to_dict(doc) for doc in documents]
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def update_document_type(self, document_id: str, user_id: str, document_type: str) -> bool:
        """문서 타입 업데이트"""
        try:
            document = self.document_crud.get_document(document_id)
            if not document or document.user_id != user_id:
                raise HandledException(ResponseCode.DOCUMENT_NOT_FOUND, msg="문서를 찾을 수 없습니다.")
            
            return self.document_crud.update_document_type(document_id, document_type)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_type_stats(self, user_id: str) -> Dict[str, int]:
        """사용자의 문서 타입별 통계 조회"""
        try:
            return self.document_crud.get_document_type_stats(user_id)
            
        except HandledException:
            raise
        except Exception as e:
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_document_processing_jobs(self, document_id: str) -> List[Dict]:
        """문서의 모든 처리 작업 조회"""
        try:
            job_service = ProcessingJobService(self.db)
            return job_service.get_document_jobs(document_id)
            
        except Exception as e:
            logger.error(f"문서 처리 작업 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
    
    def get_processing_job_progress(self, job_id: str) -> Dict:
        """처리 작업의 실시간 진행률 조회"""
        try:
            job_service = ProcessingJobService(self.db)
            from shared_core.crud import ProcessingJobCRUD
            job_crud = ProcessingJobCRUD(self.db)
            
            job = job_crud.get_job(job_id)
            if not job:
                return None
                
            return job_service._job_to_dict(job)
            
        except Exception as e:
            logger.error(f"처리 작업 진행률 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.UNDEFINED_ERROR, e=e)
