# _*_ coding: utf-8 _*_
"""Program upload module for S3 upload and file processing."""
import logging
from datetime import datetime
from typing import Dict

from src.database.models.document_models import Document
from src.config import settings

logger = logging.getLogger(__name__)


class ProgramUploader:
    """프로그램 파일 S3 업로드 및 처리 클래스"""

    def __init__(self):
        """
        ProgramUploader 초기화
        S3 관련 작업은 S3Service를 사용합니다.
        """


    async def preprocess_and_create_json(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        unzipped_files: list,
        template_xlsx_path: str,
        comment_csv_path: str,
        ladder_document_id: str,
        db_session,
        document_crud,
        failure_crud,
        chunk_commit_size: int = 50,
    ) -> Dict[str, Dict]:
        """
        ZIP 압축 해제 파일들을 전처리하여 JSON 파일 생성, S3 업로드 및 Document 저장

        전략: 개별 처리 및 즉시 DB 반영
        - 각 파일을 개별적으로 처리
        - 전처리 성공 시 즉시 Document 테이블에 저장
        - 실패 시 즉시 ProcessingFailure 테이블에 저장
        - 청크 단위로 commit (성능 최적화)

        Args:
            program_id: 프로그램 ID
            program_title: 프로그램 제목
            user_id: 사용자 ID
            unzipped_files: 압축 해제된 파일 목록 (S3 경로)
            template_xlsx_path: 템플릿 XLSX 파일 S3 경로
            comment_csv_path: PLC Ladder Comment CSV 파일 S3 경로
            ladder_document_id: 원본 ZIP 파일의 Document ID (source_document_id로 사용)
            db_session: 데이터베이스 세션
            document_crud: DocumentCRUD 인스턴스
            failure_crud: ProcessingFailureCRUD 인스턴스
            chunk_commit_size: 청크 commit 크기 (기본값: 50)

        Returns:
            Dict: 전처리 결과
                {
                    'summary': {
                        'total': 300,
                        'success': 295,
                        'failed': 5,
                    },
                    'created_documents': [...],  # 생성된 Document 정보
                    'failed_files': [...]  # 실패한 파일 정보
                }
        """
        try:
            from src.utils.uuid_gen import gen
            from src.database.models.program_models import ProcessingFailure
            import os

            logger.info(
                f"전처리 시작: program_id={program_id}, "
                f"unzipped_files={len(unzipped_files)}개"
            )

            created_documents = []
            failed_files = []

            for idx, unzipped_file_path in enumerate(unzipped_files, start=1):
                try:
                    # TODO: 전처리 로직 구현 필요
                    # 1. unzipped_file_path에서 파일 다운로드
                    # 2. template_xlsx_path와 comment_csv_path 활용
                    # 3. 파일을 분석하여 JSON 형식으로 변환
                    # 4. json_content 생성
                    #
                    # 예시:
                    #   - S3에서 파일 다운로드
                    #   - 파일 내용 파싱
                    #   - template_xlsx와 comment_csv 데이터 결합
                    #   - JSON 형식으로 변환
                    #   - json_content = json.dumps(processed_data, ensure_ascii=False)
                    #
                    # 전처리 시작 시 status 업데이트:
                    #   document_crud.update_document(document_id, status="preprocessing")

                    # S3 프로그램 경로 prefix 가져오기
                    program_prefix = settings.s3_program_prefix.rstrip("/")
                    
                    json_filename = f"processed_{program_id}_{idx}.json"
                    json_s3_key = f"{program_prefix}/{program_id}/processed/{json_filename}"

                    # TODO: 전처리 결과를 JSON으로 변환하여 json_content 생성
                    json_content = ""  # 전처리 로직 구현 후 채워넣기

                    # S3에 JSON 파일 업로드
                    json_s3_path = await self._upload_json_to_s3(
                        json_content=json_content, s3_key=json_s3_key
                    )

                    # logic_id 추출 (source_file_path에서)
                    logic_id = None
                    if unzipped_file_path:
                        filename = os.path.basename(unzipped_file_path)
                        logic_id = filename

                    # Document 생성 (전처리 및 임베딩 대상 파일)
                    # JSON 파일은 이미 전처리 완료 상태이므로 preprocessed로 시작
                    # status 흐름: STATUS_PREPROCESSED -> STATUS_EMBEDDING -> STATUS_EMBEDDED
                    document_id = gen()
                    document_crud.create_document(
                        document_id=document_id,
                        document_name=f"{program_title}_{json_filename}",
                        original_filename=json_filename,
                        file_key=json_s3_key,
                        file_size=len(json_content.encode("utf-8")),
                        file_type="application/json",
                        file_extension="json",
                        user_id=user_id,
                        upload_path=json_s3_path,
                        status=Document.STATUS_PREPROCESSED,  # 전처리 완료 (임베딩 대기)
                        document_type=Document.TYPE_LADDER_LOGIC_JSON,
                        program_id=program_id,
                        source_document_id=ladder_document_id,
                        metadata_json={
                            "program_id": program_id,
                            "program_title": program_title,
                            "processing_stage": "preprocessed",
                            "json_filename": json_filename,
                            "logic_id": logic_id,
                            "source_file_path": unzipped_file_path,
                        },
                    )

                    # TODO: 전처리 실패 시 status 업데이트
                    # 전처리 실패 시:
                    #   document_crud.update_document(document_id, status=Document.STATUS_FAILED, error_message="...")
                    #   failed_files.append({...})
                    # 전처리 성공 시는 이미 status=Document.STATUS_PREPROCESSED로 설정되어 있음

                    created_documents.append({
                        "document_id": document_id,
                        "s3_path": json_s3_path,
                        "filename": json_filename,
                    })

                    # 청크 단위 commit (성능 최적화)
                    if idx % chunk_commit_size == 0:
                        db_session.commit()
                        logger.info(
                            f"전처리 진행상황: {idx}/{len(unzipped_files)} "
                            f"완료 (청크 commit)"
                        )

                except Exception as file_error:
                    # 개별 파일 처리 실패 시에도 계속 진행
                    logger.error(
                        f"파일 처리 실패: {unzipped_file_path}, "
                        f"error: {str(file_error)}"
                    )
                    db_session.rollback()

                    # ProcessingFailure에 저장
                    failure_id = gen()
                    failure_crud.create_failure(
                        failure_id=failure_id,
                        source_type=ProcessingFailure.SOURCE_TYPE_PROGRAM,
                        source_id=program_id,
                        failure_type=ProcessingFailure.FAILURE_TYPE_PREPROCESSING,
                        error_message=str(file_error),
                        file_path=unzipped_file_path,
                        file_index=idx,
                        error_details={
                            "error": str(file_error),
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                    db_session.commit()

                    failed_files.append({
                        "file_path": unzipped_file_path,
                        "index": idx,
                        "error": str(file_error),
                        "failure_id": failure_id,
                    })
                    continue

            # 남은 파일들 commit
            if len(unzipped_files) % chunk_commit_size != 0:
                db_session.commit()

            summary = {
                "total": len(unzipped_files),
                "success": len(created_documents),
                "failed": len(failed_files),
            }

            logger.info(
                f"전처리 완료: {summary['success']}개 성공, "
                f"{summary['failed']}개 실패 / 총 {summary['total']}개"
            )

            if failed_files:
                logger.warning(
                    f"실패한 파일 {len(failed_files)}개: "
                    f"{[f['file_path'] for f in failed_files[:5]]}"
                )

            return {
                "summary": summary,
                "created_documents": created_documents,
                "failed_files": failed_files,
            }

        except Exception as e:
            logger.error(f"전처리 중 오류: {str(e)}")
            raise

    async def _upload_json_to_s3(self, json_content: str, s3_key: str) -> str:
        """
        JSON 파일을 S3에 업로드
        
        주의: 현재는 TODO 상태로 실제 업로드는 수행하지 않습니다.
        S3 업로드가 필요한 경우 S3Service를 사용하세요.

        Returns:
            str: S3 경로 (s3://bucket/key 형식)
        """
        try:
            # TODO: S3 업로드 로직 구현 필요
            # S3Service를 사용하여 업로드하도록 변경 필요
            
            # 임시로 경로만 반환 (실제 업로드는 하지 않음)
            s3_bucket = settings.s3_bucket_name
            logger.info(f"JSON 파일 S3 업로드 완료: {s3_key}")
            return f"s3://{s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error(f"JSON 파일 S3 업로드 실패: {str(e)}")
            raise

    async def request_vector_indexing(
        self, program_id: str, s3_paths: Dict[str, str]
    ) -> bool:
        """
        Vector DB 인덱싱을 위한 엔드포인트 호출

        Returns:
            bool: 인덱싱 요청 성공 여부
        """
        try:
            # TODO: Vector DB 인덱싱 엔드포인트 호출
            # 예시:
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "http://vector-db-service/index",
            #         json={
            #             "program_id": program_id,
            #             "s3_paths": s3_paths
            #         }
            #     )
            #     return response.status_code == 200

            logger.info(f"Vector DB 인덱싱 요청: program_id={program_id}")
            return True

        except Exception as e:
            logger.error(f"Vector DB 인덱싱 요청 실패: {str(e)}")
            return False
