# _*_ coding: utf-8 _*_
"""Knowledge Reference Management API endpoints."""
import logging
import io
import urllib.parse

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from src.core.dependencies import get_db, get_s3_download_service
from src.api.services.s3_download_service import S3DownloadService
from src.database.crud.knowledge_reference_crud import KnowledgeReferenceCRUD

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge", tags=["knowledge-management"])


@router.get(
    "/{reference_id}/download",
    summary="기준정보 파일 다운로드",
    description="""
    S3에 저장된 기준정보(Knowledge Reference) 파일을 다운로드합니다.
    
    **화면 용도:** 기준정보 관리 화면에서 미쯔비시 매뉴얼, 용어집 파일 다운로드
    
    **기준정보 종류:**
    - `manual`: 미쯔비시 매뉴얼
    - `glossary`: 용어집
    
    **사용 방법:**
    1. 기준정보 목록 조회 API에서 `reference_id` 확인
    2. 다운로드 링크 생성: `/knowledge/{reference_id}/download`
    
    **예시:**
    ```
    GET /v1/knowledge/REF_MITSUBISHI_001/download
    GET /v1/knowledge/REF_GLOSSARY_001/download
    ```
    
    **보안:**
    - reference_id로 KnowledgeReference 조회
    - 활성화된(is_active=True) 기준정보만 다운로드 가능
    - 삭제되지 않은(is_deleted=False) 기준정보만 다운로드 가능
    
    **응답:**
    - 파일 다운로드 스트림 (Content-Disposition 헤더 포함)
    - 원본 파일명으로 다운로드됨
    """,
)
def download_knowledge_file(
    reference_id: str = Path(..., description="Reference ID", example="REF_MITSUBISHI_001"),
    db: Session = Depends(get_db),
    s3_download_service: S3DownloadService = Depends(get_s3_download_service),
):
    """
    기준정보 파일 다운로드 API

    Args:
        reference_id: Knowledge Reference ID
        db: 데이터베이스 세션
        s3_download_service: S3 다운로드 서비스

    Returns:
        StreamingResponse: 파일 다운로드 응답
    """
    try:
        knowledge_crud = KnowledgeReferenceCRUD(db)
        
        # 1. KnowledgeReference 존재 확인
        reference = knowledge_crud.get_reference(reference_id)
        if not reference:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"기준정보를 찾을 수 없습니다: {reference_id}",
            )
        
        # 2. 활성화 및 삭제 여부 확인
        if not reference.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="비활성화된 기준정보입니다.",
            )
        
        if reference.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="삭제된 기준정보입니다.",
            )
        
        # 3. Document 조회 (knowledge_reference_id로 연결된 Document)
        from shared_core.models import Document
        
        document = (
            db.query(Document)
            .filter(Document.knowledge_reference_id == reference_id)
            .filter(Document.is_deleted.is_(False))
            .order_by(Document.create_dt.desc())  # 최신 파일 우선
            .first()
        )
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"기준정보 파일을 찾을 수 없습니다: {reference_id}",
            )
        
        # 4. 파일 다운로드
        file_content, filename, content_type = (
            s3_download_service.download_file_by_document_id(
                document_id=document.document_id,
                db_session=db,
            )
        )
        
        # 한글 파일명 처리를 위한 URL 인코딩
        encoded_filename = urllib.parse.quote(filename.encode("utf-8"))
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=content_type,
            headers={
                "Content-Disposition": (
                    f"attachment; filename*=UTF-8''{encoded_filename}"
                )
            },
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    except Exception as e:
        logger.error(
            "기준정보 파일 다운로드 실패: reference_id=%s, error=%s",
            reference_id,
            str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 다운로드 중 오류가 발생했습니다: {str(e)}",
        ) from e

