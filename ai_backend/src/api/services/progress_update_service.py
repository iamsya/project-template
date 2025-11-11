# _*_ coding: utf-8 _*_
"""진행률 업데이트 서비스 (백그라운드 작업)"""
import logging
from datetime import datetime
from typing import Dict, Optional

import httpx
from sqlalchemy.orm import Session

from src.config.simple_settings import settings
from src.database.models.program_models import Program

logger = logging.getLogger(__name__)


class ProgressUpdateService:
    """진행률 업데이트 서비스 (백그라운드 작업용)"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_document_stats(self, program_id: str) -> Dict:
        """
        Program의 Document 통계 계산

        Returns:
            Dict: {
                "total_upload": int,  # 업로드 단계 전체 파일 수 (항상 3개)
                "total_processed": int,  # 전처리 후 전체 파일 수
                "uploaded": int,  # 업로드 완료 파일 수 (3개 타입 존재 여부)
                "processed": int,  # 전처리 완료 파일 수
                "embedded": int,  # is_embedded=True인 파일 수
            }
        """
        from shared_core.models import Document

        # 업로드 단계 전체 파일 수: 항상 3개 고정 (ladder_logic, comment, template)
        total_upload = 3

        # 업로드 완료: ladder_logic, comment, template 3개 타입이 모두 존재하는지 확인
        required_types = ["ladder_logic", "comment", "template"]
        uploaded_count = 0
        for file_type in required_types:
            exists = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.is_deleted.is_(False))
                .filter(Document.program_file_type == file_type)
                .first()
            )
            if exists:
                uploaded_count += 1

        # 전처리 후 전체 파일 수: template_data 테이블에서 program_id로 카운트
        # Template과 TemplateData를 조인하여 program_id로 조회
        from src.database.models.template_models import (
            Template,
            TemplateData,
        )

        total_processed = (
            self.db.query(TemplateData)
            .join(
                Template, TemplateData.template_id == Template.template_id
            )
            .filter(Template.program_id == program_id)
            .count()
        )

        # TemplateData가 없으면 에러 발생 (fallback 제거)
        if total_processed == 0:
            logger.error(
                "TemplateData가 없습니다: program_id=%s. "
                "프로그램 등록이 제대로 완료되지 않았을 수 있습니다.",
                program_id,
            )
            # 에러 로깅 후 0 반환 (시스템 중단 방지)
            # 필요시 예외를 발생시킬 수도 있음

        # Program.metadata_json에 total_expected 동기화 (참고용)
        program = (
            self.db.query(Program)
            .filter(Program.program_id == program_id)
            .first()
        )
        if program:
            current_metadata = program.metadata_json or {}
            if (
                current_metadata.get("total_expected", 0)
                != total_processed
            ):
                current_metadata["total_expected"] = total_processed
                program.metadata_json = current_metadata
                self.db.commit()
                logger.debug(
                    "Program.metadata_json.total_expected 동기화: "
                    "program_id=%s, total_expected=%d",
                    program_id,
                    total_processed,
                )

        # 전처리 완료 파일 수: program_file_type이 있고 status='completed'인 파일 수
        processed_docs = (
            self.db.query(Document)
            .filter(Document.program_id == program_id)
            .filter(Document.is_deleted.is_(False))
            .filter(Document.program_file_type.isnot(None))
            .filter(Document.status == "completed")
            .count()
        )

        # 임베딩 완료: is_embedded=True인 파일 수
        embedded_docs = (
            self.db.query(Document)
            .filter(Document.program_id == program_id)
            .filter(Document.is_deleted.is_(False))
            .filter(Document.is_embedded.is_(True))
            .count()
        )

        return {
            "total_upload": total_upload,
            "total_processed": total_processed,
            "uploaded": uploaded_count,
            "processed": processed_docs,
            "embedded": embedded_docs,
        }

    def update_program_progress(self, program_id: str) -> bool:
        """
        Program의 진행률 통계를 metadata_json에 업데이트
        (Document embedded 상태 동기화 포함)

        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            program = (
                self.db.query(Program)
                .filter(Program.program_id == program_id)
                .first()
            )

            if not program:
                logger.warning(
                    "Program을 찾을 수 없음: program_id=%s", program_id
                )
                return False

            # 1. REST API를 통해 Document embedded 상태 동기화
            sync_result = self.sync_document_embedded_status(program_id)
            if sync_result["updated"] > 0:
                logger.debug(
                    "Document embedded 상태 동기화 완료: "
                    "program_id=%s, updated=%d",
                    program_id,
                    sync_result["updated"],
                )

            # 2. Document 통계 계산 (업데이트된 상태 반영)
            stats = self.calculate_document_stats(program_id)

            # metadata_json 업데이트
            metadata = program.metadata_json or {}
            metadata["document_stats"] = stats
            metadata["document_stats_updated_at"] = (
                datetime.utcnow().isoformat()
            )
            # Logic/Comment 파일 개수는 프로그램 등록 시점에 저장된 값 유지
            # (전처리 완료 여부와 무관하게 전체 파일 개수 표시)

            program.metadata_json = metadata
            self.db.commit()

            logger.debug(
                "Program 진행률 통계 업데이트 완료: program_id=%s, "
                "stats=%s",
                program_id,
                stats,
            )
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(
                "Program 진행률 통계 업데이트 실패: program_id=%s, "
                "error=%s",
                program_id,
                str(e),
            )
            return False

    def update_all_active_programs(self) -> Dict:
        """
        진행 중인 모든 Program의 진행률 통계 업데이트

        Returns:
            Dict: {
                "total": int,
                "updated": int,
                "failed": int,
                "errors": list[dict]  # {"program_id": str, "error": str}
            }
        """
        try:
            # 진행 중인 Program 조회
            try:
                active_programs = (
                    self.db.query(Program)
                    .filter(
                        Program.status.in_(
                            ["uploading", "processing", "embedding"]
                        )
                    )
                    .filter(Program.is_used.is_(True))
                    .all()
                )
            except Exception as db_error:
                # 테이블이 아직 생성되지 않은 경우 (앱 시작 직후)
                error_str = str(db_error)
                if (
                    "does not exist" in error_str
                    or "UndefinedTable" in error_str
                ):
                    logger.debug(
                        "PROGRAMS 테이블이 아직 생성되지 않았습니다. "
                        "데이터베이스 초기화 대기 중..."
                    )
                    return {
                        "total": 0,
                        "updated": 0,
                        "failed": 0,
                        "errors": [],
                    }
                # 다른 데이터베이스 오류는 재발생
                raise

            total = len(active_programs)
            updated = 0
            failed = 0
            errors = []

            if total == 0:
                logger.debug("업데이트할 진행 중인 Program이 없습니다.")
                return {
                    "total": 0,
                    "updated": 0,
                    "failed": 0,
                    "errors": [],
                }

            logger.info(
                "진행 중인 Program 진행률 통계 업데이트 시작: total=%d",
                total,
            )

            for program in active_programs:
                try:
                    if self.update_program_progress(program.program_id):
                        updated += 1
                    else:
                        failed += 1
                        errors.append(
                            {
                                "program_id": program.program_id,
                                "error": "update_program_progress 실패",
                            }
                        )
                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append(
                        {
                            "program_id": program.program_id,
                            "error": error_msg,
                        }
                    )
                    logger.warning(
                        "Program 진행률 통계 업데이트 실패: "
                        "program_id=%s, error=%s",
                        program.program_id,
                        error_msg,
                    )

            logger.info(
                "전체 Program 진행률 통계 업데이트 완료: "
                "total=%d, updated=%d, failed=%d",
                total,
                updated,
                failed,
            )

            return {
                "total": total,
                "updated": updated,
                "failed": failed,
                "errors": errors,
            }

        except Exception as e:
            logger.error(
                "전체 Program 진행률 통계 업데이트 실패: error=%s", str(e)
            )
            return {
                "total": 0,
                "updated": 0,
                "failed": 0,
                "errors": [{"error": str(e)}],
            }

    def sync_document_embedded_status(
        self, program_id: str
    ) -> Dict:
        """
        REST API를 통해 Document의 embedded 상태 동기화

        GET {End Point}/api/v{API Version}/repos/{repo id}/
        documents/{document id}
        를 호출하여 document.file_id로 문서 상태를 확인하고,
        Document 테이블의 embedded 상태를 업데이트합니다.

        Returns:
            Dict: {
                "total": int,
                "updated": int,
                "failed": int,
                "errors": List[str]
            }
        """
        from shared_core.models import Document
        from src.database.models.knowledge_reference_models import (
            KnowledgeReference,
        )

        try:
            # Program의 모든 Document 조회
            documents = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.is_deleted.is_(False))
                .all()
            )

            if not documents:
                return {
                    "total": 0,
                    "updated": 0,
                    "failed": 0,
                    "errors": [],
                }

            total = len(documents)
            updated = 0
            failed = 0
            errors = []

            # Knowledge API 설정
            api_endpoint = settings.knowledge_api_endpoint
            api_version = settings.knowledge_api_version

            if not api_endpoint:
                logger.warning(
                    "KNOWLEDGE_API_ENDPOINT가 설정되지 않아 "
                    "embedded 상태 동기화를 건너뜁니다."
                )
                return {
                    "total": total,
                    "updated": 0,
                    "failed": 0,
                    "errors": ["KNOWLEDGE_API_ENDPOINT가 설정되지 않음"],
                }

            # HTTP 클라이언트 생성
            timeout = httpx.Timeout(10.0, connect=5.0)

            for document in documents:
                try:
                    # file_id가 없으면 건너뛰기
                    if not document.file_id:
                        continue

                    # repo_id 조회 (KnowledgeReference에서)
                    repo_id = None
                    if document.knowledge_reference_id:
                        knowledge_ref = (
                            self.db.query(KnowledgeReference)
                            .filter(
                                KnowledgeReference.reference_id
                                == document.knowledge_reference_id
                            )
                            .first()
                        )
                        if knowledge_ref:
                            repo_id = knowledge_ref.repo_id

                    if not repo_id:
                        # repo_id가 없으면 건너뛰기
                        logger.debug(
                            "document_id=%s: repo_id가 없어 건너뜁니다.",
                            document.document_id,
                        )
                        continue

                    # REST API 호출
                    # GET {End Point}/api/v{API Version}/repos/
                    # {repo id}/documents/{document id}
                    api_url = (
                        f"{api_endpoint}/api/v{api_version}/repos/"
                        f"{repo_id}/documents/{document.file_id}"
                    )

                    with httpx.Client(timeout=timeout) as client:
                        response = client.get(api_url)

                        if response.status_code == 200:
                            doc_data = response.json()

                            # 응답에서 embedded 상태 확인
                            # 응답 구조에 따라 필드명이 다를 수 있음
                            is_embedded_api = doc_data.get(
                                "is_embedded", False
                            )
                            vector_count_api = doc_data.get(
                                "vector_count", 0
                            )

                            # Document 테이블 업데이트
                            if (
                                document.is_embedded != is_embedded_api
                                or document.vector_count != vector_count_api
                            ):
                                document.is_embedded = is_embedded_api
                                document.vector_count = vector_count_api
                                updated += 1

                        elif response.status_code == 404:
                            # 문서가 없으면 embedded 상태를 False로 설정
                            if (
                                document.is_embedded
                                or document.vector_count > 0
                            ):
                                document.is_embedded = False
                                document.vector_count = 0
                                updated += 1
                        else:
                            # API 호출 실패
                            failed += 1
                            error_msg = (
                                f"API 호출 실패: status={response.status_code}, "
                                f"response={response.text[:200]}"
                            )
                            errors.append(
                                f"document_id={document.document_id}: "
                                f"{error_msg}"
                            )
                            logger.warning(
                                "Document embedded 상태 확인 실패: "
                                "document_id=%s, file_id=%s, error=%s",
                                document.document_id,
                                document.file_id,
                                error_msg,
                            )

                except httpx.TimeoutException as e:
                    failed += 1
                    error_msg = f"API 호출 타임아웃: {str(e)}"
                    errors.append(
                        f"document_id={document.document_id}: {error_msg}"
                    )
                    logger.warning(
                        "Document embedded 상태 확인 타임아웃: "
                        "document_id=%s, file_id=%s",
                        document.document_id,
                        document.file_id,
                    )
                except Exception as e:
                    failed += 1
                    error_msg = str(e)
                    errors.append(
                        f"document_id={document.document_id}: {error_msg}"
                    )
                    logger.warning(
                        "Document embedded 상태 확인 실패: "
                        "document_id=%s, file_id=%s, error=%s",
                        document.document_id,
                        document.file_id,
                        error_msg,
                    )

            self.db.commit()

            logger.info(
                "Document embedded 상태 동기화 완료: program_id=%s, "
                "total=%d, updated=%d, failed=%d",
                program_id,
                total,
                updated,
                failed,
            )

            return {
                "total": total,
                "updated": updated,
                "failed": failed,
                "errors": errors,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(
                "Document embedded 상태 동기화 실패: program_id=%s, "
                "error=%s",
                program_id,
                str(e),
            )
            return {
                "total": 0,
                "updated": 0,
                "failed": 0,
                "errors": [str(e)],
            }

    def calculate_progress_percentage(
        self, program: Program, stats: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Program의 진행률 퍼센트 계산

        Args:
            program: Program 객체
            stats: Document 통계 (없으면 metadata에서 가져옴)

        Returns:
            int: 진행률 퍼센트 (0-100), None: 계산 불가
        """
        if program.status not in ["uploading", "processing", "embedding"]:
            return None

        # 통계 가져오기
        metadata = program.metadata_json or {}
        if stats is None:
            stats = metadata.get("document_stats", {})

        if not stats:
            return None

        # 단계별 진행률 계산
        if program.status == "uploading":
            # 업로드 중: 전체 파일 수는 항상 3개
            total_upload = stats.get("total_upload", 3)
            uploaded = stats.get("uploaded", 0)
            if total_upload > 0:
                return round((uploaded / total_upload) * 30)
            return 0

        elif program.status == "processing":
            # 처리 중: 전처리 후 전체 파일 수 사용
            total_processed = stats.get("total_processed", 0)
            processed = stats.get("processed", 0)
            if total_processed > 0:
                return 31 + round((processed / total_processed) * 30)
            return 31

        elif program.status == "embedding":
            # 임베딩 중: 전처리 후 전체 파일 수 사용
            total_processed = stats.get("total_processed", 0)
            embedded = stats.get("embedded", 0)
            if total_processed > 0:
                return 61 + round((embedded / total_processed) * 39)
            return 61

        return None
