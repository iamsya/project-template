# _*_ coding: utf-8 _*_
"""Knowledge 상태 확인 서비스"""
import logging
from typing import Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from src.config import settings
from src.database.models.document_models import Document

logger = logging.getLogger(__name__)


class KnowledgeStatusService:
    """Knowledge Base 상태 확인 서비스"""

    def __init__(self, db: Session):
        self.db = db
        # 외부 Knowledge API 엔드포인트 (환경변수에서 가져오기)
        self.knowledge_api_endpoint = settings.knowledge_api_endpoint
        self.knowledge_api_version = settings.knowledge_api_version

    async def get_repo_documents(
        self, repo_id: str
    ) -> Optional[List[Dict]]:
        """
        Knowledge Repo의 문서 목록 조회

        Args:
            repo_id: Knowledge Repo ID

        Returns:
            List[Dict]: 문서 목록 (document_name, conversion_status 등 포함)
            None: API 호출 실패 시
        """
        try:
            url = (
                f"{self.knowledge_api_endpoint}/api/"
                f"{self.knowledge_api_version}/repos/{repo_id}/documents"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url)

                if response.status_code == 200:
                    data = response.json()
                    # 응답 형식에 따라 조정 필요
                    # 예: {"documents": [...]} 또는 [...]
                    if isinstance(data, dict) and "documents" in data:
                        return data["documents"]
                    elif isinstance(data, list):
                        return data
                    else:
                        logger.warning(
                            "예상하지 못한 응답 형식: repo_id=%s, "
                            "response=%s",
                            repo_id,
                            data,
                        )
                        return []
                else:
                    logger.error(
                        "Knowledge API 호출 실패: repo_id=%s, "
                        "status_code=%s, response=%s",
                        repo_id,
                        response.status_code,
                        response.text,
                    )
                    return None

        except httpx.TimeoutException:
            logger.error(
                "Knowledge API 호출 타임아웃: repo_id=%s", repo_id
            )
            return None
        except Exception as e:
            logger.error(
                "Knowledge API 호출 중 오류: repo_id=%s, error=%s",
                repo_id,
                str(e),
            )
            return None

    async def sync_document_status(
        self, program_id: str
    ) -> Dict[str, any]:  # noqa: ANN401
        """
        Program의 Knowledge Reference 문서 상태 동기화

        Args:
            program_id: Program ID

        Returns:
            Dict: 동기화 결과
                {
                    "synced": True/False,
                    "total_documents": int,
                    "updated_documents": int,
                    "errors": List[str]
                }
        """
        try:
            from src.database.models.knowledge_reference_models import (
                KnowledgeReference,
            )
            from src.database.models.document_models import Document

            # Program과 연결된 Document를 통해 KnowledgeReference 조회
            # Document가 program_id와 knowledge_reference_id를 모두 가지고 있음
            documents_with_ref = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.is_deleted.is_(False))
                .filter(Document.knowledge_reference_id.isnot(None))
                .all()
            )

            if not documents_with_ref:
                logger.info(
                    "Knowledge Reference를 찾을 수 없음: "
                    "program_id=%s",
                    program_id,
                )
                return {
                    "synced": False,
                    "total_documents": 0,
                    "updated_documents": 0,
                    "errors": ["Knowledge Reference를 찾을 수 없습니다."],
                }

            # Document의 knowledge_reference_id로 KnowledgeReference 조회
            knowledge_ref_ids = {
                doc.knowledge_reference_id
                for doc in documents_with_ref
                if doc.knowledge_reference_id
            }

            knowledge_refs = (
                self.db.query(KnowledgeReference)
                .filter(KnowledgeReference.reference_id.in_(knowledge_ref_ids))
                .filter(KnowledgeReference.is_deleted.is_(False))
                .filter(KnowledgeReference.is_active.is_(True))
                .all()
            )

            if not knowledge_refs:
                logger.info(
                    "활성화된 Knowledge Reference를 찾을 수 없음: "
                    "program_id=%s",
                    program_id,
                )
                return {
                    "synced": False,
                    "total_documents": 0,
                    "updated_documents": 0,
                    "errors": ["활성화된 Knowledge Reference를 찾을 수 없습니다."],
                }

            total_updated = 0
            errors = []

            for knowledge_ref in knowledge_refs:
                repo_id = knowledge_ref.repo_id
                if not repo_id:
                    errors.append(
                        f"Knowledge Reference {knowledge_ref.reference_id}에 "
                        "repo_id가 없습니다."
                    )
                    continue

                # 외부 API로 문서 목록 조회
                documents = await self.get_repo_documents(repo_id)
                if documents is None:
                    errors.append(
                        f"repo_id={repo_id}의 문서 목록 조회 실패"
                    )
                    continue

                # Document 테이블의 file_id와 매칭하여 상태 업데이트
                for doc_info in documents:
                    file_id = doc_info.get("file_id") or doc_info.get("id")
                    conversion_status = (
                        doc_info.get("conversion_status")
                        or doc_info.get("status")
                    )

                    if not file_id:
                        continue

                    # Document 테이블에서 file_id로 조회
                    document = (
                        self.db.query(Document)
                        .filter(Document.file_id == file_id)
                        .filter(Document.program_id == program_id)
                        .filter(Document.is_deleted.is_(False))
                        .first()
                    )

                    if document:
                        # conversion_status에 따라 Document 상태 업데이트
                        # 예: "completed" -> status=Document.STATUS_COMPLETED
                        if conversion_status == "completed":
                            if document.status != Document.STATUS_COMPLETED:
                                document.status = Document.STATUS_COMPLETED
                                total_updated += 1
                        elif conversion_status == "failed":
                            if document.status != Document.STATUS_FAILED:
                                document.status = Document.STATUS_FAILED
                                document.error_message = doc_info.get(
                                    "error_message", "변환 실패"
                                )
                                total_updated += 1
                        # 기타 상태는 그대로 유지

            self.db.commit()

            return {
                "synced": True,
                "total_documents": len(documents) if documents else 0,
                "updated_documents": total_updated,
                "errors": errors,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                "Document 상태 동기화 실패: program_id=%s, error=%s",
                program_id,
                str(e),
            )
            return {
                "synced": False,
                "total_documents": 0,
                "updated_documents": 0,
                "errors": [str(e)],
            }

