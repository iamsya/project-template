# _*_ coding: utf-8 _*_
"""Program Service for handling program registration and management."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session
from src.database.models.document_models import Document
from src.api.services.program_uploader import ProgramUploader
from src.api.services.program_validator import ProgramValidator
from src.api.services.s3_service import S3Service
from src.config import settings
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen, gen_program_id

logger = logging.getLogger(__name__)


class ProgramService:
    """프로그램 관리 서비스"""

    def __init__(self, db: Session, uploader: ProgramUploader = None, s3_service: S3Service = None):
        """
        Args:
            db: 데이터베이스 세션
            uploader: ProgramUploader 인스턴스
            s3_service: S3Service 인스턴스
        """
        self.db = db
        self.validator = ProgramValidator()
        self.uploader = uploader or ProgramUploader()
        self.s3_service = s3_service
        from src.database.crud.program_crud import ProgramCRUD

        self.program_crud = ProgramCRUD(db)

    def get_program_id_from_plc_id(self, plc_id: str) -> Optional[str]:
        """PLC ID로 매핑된 program_id 조회"""
        if not plc_id:
            return None

        try:
            from src.database.crud.plc_crud import PLCCRUD

            plc_crud = PLCCRUD(self.db)
            plc = plc_crud.get_plc_by_plc_id(plc_id)
            if plc and plc.program_id:
                program_id = plc.program_id
                logger.info("PLC %s의 program_id 조회: %s", plc_id, program_id)
                return program_id
            else:
                logger.warning(
                    "PLC %s를 찾을 수 없거나 program_id가 없습니다.",
                    plc_id,
                )
                return None
        except Exception as e:
            logger.error("PLC %s의 program_id 조회 실패: %s", plc_id, str(e))
            return None

    async def register_program(
        self,
        program_title: str,
        program_description: Optional[str],
        user_id: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        comment_csv: UploadFile,
        process_id: str,
    ) -> Dict:
        """
        프로그램 등록 (유효성 검사 + 비동기 처리)

        Args:
            process_id: 공정 ID (필수)

        Returns:
            Dict: 프로그램 등록 결과
        """
        try:
            # program_id 생성: pgm_{process_id}_{타임스탬프(10자리)}
            program_id = gen_program_id(process_id)

            # 1. 유효성 검사
            validation_result = self._validate_program_files(
                program_id=program_id,
                ladder_zip=ladder_zip,
                template_xlsx=template_xlsx,
                comment_csv=comment_csv,
            )

            # 2. 유효성 검사 직후 응답 반환
            if not validation_result["is_valid"]:
                return validation_result

            # 3. 성공 시 즉시 응답 반환 (나머지는 비동기로 처리)
            response = self._build_success_response(
                program_id=program_id,
                program_title=program_title,
                warnings=validation_result["warnings"],
                checked_files=validation_result["checked_files"],
            )

            # 4. 나머지 작업은 비동기로 처리 (DB 저장, 템플릿 생성 등)
            asyncio.create_task(
                self._complete_program_registration_async(
                    program_id=program_id,
                    program_title=program_title,
                    program_description=program_description,
                    user_id=user_id,
                    process_id=process_id,
                    ladder_zip=ladder_zip,
                    template_xlsx=template_xlsx,
                    comment_csv=comment_csv,
                )
            )

            return response

        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 등록 중 오류: {str(e)}")
            raise HandledException(ResponseCode.PROGRAM_REGISTRATION_ERROR, e=e)

    def _validate_program_files(
        self,
        program_id: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        comment_csv: UploadFile,
    ) -> Dict:
        """프로그램 파일 유효성 검사"""
        logger.info(f"프로그램 유효성 검사 시작: program_id={program_id}")
        is_valid, errors, warnings, checked_files = self.validator.validate_files(
            ladder_zip=ladder_zip,
            template_xlsx=template_xlsx,
            comment_csv=comment_csv,
        )

        if not is_valid:
            # 에러를 섹션별로 그룹화
            error_sections = self._group_errors_by_section(errors)

            return {
                "program_id": program_id,
                "status": "validation_failed",
                "is_valid": False,
                "errors": errors,
                "error_sections": error_sections,  # 섹션별 그룹화된 에러
                "warnings": warnings,
                "checked_files": checked_files,
                "message": "유효성 검사를 통과하지 못했습니다.",
            }

        return {
            "is_valid": True,
            "errors": errors,
            "warnings": warnings,
            "checked_files": checked_files,
        }

    def _group_errors_by_section(self, errors: List[str]) -> Dict[str, List[str]]:
        """에러를 섹션별로 그룹화"""
        error_sections = {
            "분류체계 데이터 유효성 검사": [],
            "PLC Ladder 파일 유효성 검사": [],
            "기타": [],
        }

        for error in errors:
            # XLSX 관련 에러
            if any(
                keyword in error
                for keyword in [
                    "XLSX",
                    "분류체계",
                    "로직파일명",
                    "Login ID",
                    "Logic Name",
                    "행의",
                ]
            ):
                error_sections["분류체계 데이터 유효성 검사"].append(error)
            # ZIP/교차 검증 관련 에러
            elif any(
                keyword in error
                for keyword in [
                    "ZIP",
                    "PLC Ladder",
                    "파일이 존재하지 않습니다",
                    "파일이 없습니다",
                ]
            ):
                error_sections["PLC Ladder 파일 유효성 검사"].append(error)
            else:
                error_sections["기타"].append(error)

        # 빈 섹션 제거
        return {
            section: section_errors
            for section, section_errors in error_sections.items()
            if section_errors
        }

    def _create_program_metadata(
        self,
        program_id: str,
        program_title: str,
        program_description: Optional[str],
        user_id: str,
        process_id: str,
    ):
        """프로그램 메타데이터 저장"""
        logger.info(f"프로그램 메타데이터 저장 시작: program_id={program_id}")
        from src.database.models.program_models import Program

        self.program_crud.create_program(
            program_id=program_id,
            program_name=program_title,
            create_user=user_id,
            description=program_description,
            process_id=process_id,
            status=Program.STATUS_PREPROCESSING,
            metadata_json=None,
        )
        self.db.commit()
        logger.info(f"프로그램 메타데이터 저장 완료: program_id={program_id}")

    def _create_template_document(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        template_xlsx: UploadFile,
    ) -> Dict:
        """템플릿 파일을 DOCUMENTS 테이블에만 저장"""
        logger.info(f"템플릿 Document 생성 시작: program_id={program_id}")
        from src.database.crud.document_crud import DocumentCRUD

        document_crud = DocumentCRUD(self.db)

        # template_xlsx 파일 읽기
        template_xlsx.file.seek(0)
        xlsx_content = template_xlsx.file.read()
        template_xlsx.file.seek(0)

        # 템플릿 Document 생성 (DOCUMENTS 테이블에만 저장)
        template_document_id = gen()
        document_crud.create_document(
            document_id=template_document_id,
            document_name=f"{program_title}_template",
            original_filename=template_xlsx.filename or "template.xlsx",
            file_key=None,
            file_size=len(xlsx_content),
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_extension="xlsx",
            user_id=user_id,
            upload_path=None,
            status=None,  # JSON 파일이 아니므로 status 사용 안 함
            document_type=Document.TYPE_TEMPLATE,
            program_id=program_id,
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        self.db.commit()
        logger.info(
            f"템플릿 Document 생성 완료: program_id={program_id}, "
            f"template_document_id={template_document_id}"
        )

        return {
            "template_document_id": template_document_id,
        }

    def _create_program_documents(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        ladder_zip: UploadFile,
        comment_csv: UploadFile,
        template_document_id: str,
    ) -> Dict[str, str]:
        """프로그램 관련 Document 생성"""
        from src.database.crud.document_crud import DocumentCRUD

        document_crud = DocumentCRUD(self.db)

        # ladder_zip Document 생성
        ladder_document_id = gen()
        ladder_zip.file.seek(0)
        ladder_zip_size = len(ladder_zip.file.read())
        ladder_zip.file.seek(0)

        document_crud.create_document(
            document_id=ladder_document_id,
            document_name=f"{program_title}_ladder_logic",
            original_filename=ladder_zip.filename or "ladder_logic.zip",
            file_key=None,
            file_size=ladder_zip_size,
            file_type="application/zip",
            file_extension="zip",
            user_id=user_id,
            upload_path=None,
            status=None,  # JSON 파일이 아니므로 status 사용 안 함
            document_type=Document.TYPE_LADDER_LOGIC_ZIP,
            program_id=program_id,
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        # comment_csv Document 생성
        comment_document_id = gen()
        comment_csv.file.seek(0)
        comment_csv_size = len(comment_csv.file.read())
        comment_csv.file.seek(0)

        document_crud.create_document(
            document_id=comment_document_id,
            document_name=f"{program_title}_comment",
            original_filename=comment_csv.filename or "comment.csv",
            file_key=None,
            file_size=comment_csv_size,
            file_type="text/csv",
            file_extension="csv",
            user_id=user_id,
            upload_path=None,
            status=None,  # JSON 파일이 아니므로 status 사용 안 함
            document_type=Document.TYPE_COMMENT,
            program_id=program_id,
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        self.db.commit()
        logger.info(
            f"Document 생성 완료: program_id={program_id}, "
            f"ladder_document_id={ladder_document_id}, "
            f"comment_document_id={comment_document_id}, "
            f"template_document_id={template_document_id}"
        )

        return {
            "ladder_document_id": ladder_document_id,
            "comment_document_id": comment_document_id,
            "template_document_id": template_document_id,
        }

    def _update_program_metadata(
        self, program_id: str, total_expected: Optional[int] = None
    ):
        """Program.metadata_json 업데이트

        프로그램 등록 시점에 파일 개수 메타정보 저장
        - total_expected: 전처리 예상 파일 수 (전처리 단계에서 계산됨)
        - comment_file_count: Comment 파일 개수 (항상 1개)
        """
        metadata = {
            "comment_file_count": 1,  # Comment 파일 개수 (항상 1개)
        }
        if total_expected is not None:
            metadata["total_expected"] = total_expected
            metadata["ladder_file_count"] = total_expected  # Logic 파일 개수
        
        self.program_crud.update_program(
            program_id=program_id,
            metadata_json=metadata,
        )
        self.db.commit()

    async def _complete_program_registration_async(
        self,
        program_id: str,
        program_title: str,
        program_description: Optional[str],
        user_id: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        comment_csv: UploadFile,
        process_id: str,
    ):
        """프로그램 등록 완료 처리 (비동기)
        
        - 프로그램 메타데이터 저장
        - 템플릿 및 템플릿데이터 생성
        - Document 생성
        - S3 업로드 및 전처리 시작
        """
        try:
            # 1. 프로그램 메타데이터 저장
            self._create_program_metadata(
                program_id=program_id,
                program_title=program_title,
                program_description=program_description,
                user_id=user_id,
                process_id=process_id,
            )

            # 2. 템플릿 Document 생성 (DOCUMENTS 테이블에만 저장)
            template_result = self._create_template_document(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                template_xlsx=template_xlsx,
            )
            template_document_id = template_result["template_document_id"]

            # 3. Document 생성 (ladder_logic, comment, template)
            document_ids = self._create_program_documents(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                ladder_zip=ladder_zip,
                comment_csv=comment_csv,
                template_document_id=template_document_id,
            )

            # 4. Program.metadata_json 업데이트 (초기값만 설정)
            # total_expected는 전처리 단계에서 계산되어 업데이트됨
            self._update_program_metadata(
                program_id=program_id
            )

            # 5. S3에 파일 업로드 (단위 함수 재사용)
            logger.info(f"S3 파일 업로드 시작: program_id={program_id}")
            s3_paths = {}
            
            # ZIP 파일 업로드
            ladder_zip_result = await self._upload_file_to_s3(
                file=ladder_zip,
                program_id=program_id,
            )
            s3_paths["ladder_zip_path"] = ladder_zip_result["s3_path"]
            s3_paths["ladder_zip_filename"] = ladder_zip_result["filename"]
            
            # XLSX 파일 업로드
            template_xlsx_result = await self._upload_file_to_s3(
                file=template_xlsx,
                program_id=program_id,
            )
            s3_paths["template_xlsx_path"] = template_xlsx_result["s3_path"]
            s3_paths["template_xlsx_filename"] = template_xlsx_result["filename"]
            
            # CSV 파일 업로드
            comment_csv_result = await self._upload_file_to_s3(
                file=comment_csv,
                program_id=program_id,
            )
            s3_paths["comment_csv_path"] = comment_csv_result["s3_path"]
            s3_paths["comment_csv_filename"] = comment_csv_result["filename"]
            
            logger.info(f"S3 파일 업로드 완료: program_id={program_id}")

            # 6. Document에 S3 경로 업데이트
            logger.info(f"Document S3 경로 업데이트 시작: program_id={program_id}")
            from src.database.crud.document_crud import DocumentCRUD
            document_crud = DocumentCRUD(self.db)

            # S3 프로그램 경로 prefix 가져오기
            program_prefix = settings.s3_program_prefix.rstrip("/")
            
            # ladder_document 업데이트
            if document_ids.get("ladder_document_id") and s3_paths.get("ladder_zip_path"):
                document_crud.update_document(
                    document_id=document_ids["ladder_document_id"],
                    file_key=f"{program_prefix}/{program_id}/{s3_paths['ladder_zip_filename']}",
                    upload_path=s3_paths.get("ladder_zip_path"),
                )

            # comment_document 업데이트
            if document_ids.get("comment_document_id") and s3_paths.get("comment_csv_path"):
                document_crud.update_document(
                    document_id=document_ids["comment_document_id"],
                    file_key=f"{program_prefix}/{program_id}/{s3_paths['comment_csv_filename']}",
                    upload_path=s3_paths.get("comment_csv_path"),
                )

            # template_document 업데이트
            if document_ids.get("template_document_id") and s3_paths.get("template_xlsx_path"):
                document_crud.update_document(
                    document_id=document_ids["template_document_id"],
                    file_key=f"{program_prefix}/{program_id}/{s3_paths['template_xlsx_filename']}",
                    upload_path=s3_paths.get("template_xlsx_path"),
                )

            self.db.commit()
            logger.info(f"Document S3 경로 업데이트 완료: program_id={program_id}")

            # 7. 전처리 및 Vector DB 인덱싱 시작 (기존 로직 유지)
            await self._process_program_async(
                    program_id=program_id,
                    program_title=program_title,
                    user_id=user_id,
                    ladder_zip=ladder_zip,
                    template_xlsx=template_xlsx,
                    comment_csv=comment_csv,
                ladder_document_id=document_ids.get("ladder_document_id"),
                comment_document_id=document_ids.get("comment_document_id"),
                template_document_id=document_ids.get("template_document_id"),
                s3_paths=s3_paths,
            )

        except Exception as e:
            logger.error(
                f"프로그램 등록 완료 처리 중 오류: program_id={program_id}, error={str(e)}"
            )
            from src.database.models.program_models import Program

            self.program_crud.update_program_status(
                program_id=program_id,
                status=Program.STATUS_FAILED,
                error_message=str(e),
            )
            self.db.commit()

    async def _upload_file_to_s3(
        self,
        file: UploadFile,
        program_id: str,
        filename: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        파일을 S3에 업로드하는 단위 함수 (재사용 가능)
        
        Args:
            file: 업로드할 파일
            program_id: 프로그램 ID
            filename: 파일명 (없으면 원본 파일명 사용)
            
        Returns:
            Dict: {
                's3_path': 's3://bucket/key',
                's3_key': 'programs/{program_id}/filename',
                'filename': 'filename'
            }
        """
        if not self.s3_service:
            raise HandledException(
                ResponseCode.DATABASE_QUERY_ERROR,
                msg="S3 서비스가 초기화되지 않았습니다.",
            )
        
        # S3 프로그램 경로 prefix 가져오기
        program_prefix = settings.s3_program_prefix.rstrip("/")
        
        # 파일명 결정
        original_filename = filename or file.filename
        if not original_filename:
            raise ValueError("파일명을 확인할 수 없습니다.")
        
        # S3 키 생성
        s3_key = f"{program_prefix}/{program_id}/{original_filename}"
        
        # Content-Type 결정
        content_type = file.content_type
        if not content_type:
            if original_filename.endswith('.zip'):
                content_type = "application/zip"
            elif original_filename.endswith('.xlsx'):
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif original_filename.endswith('.csv'):
                content_type = "text/csv"
            else:
                content_type = "application/octet-stream"
        
        # S3 업로드
        s3_path = await self.s3_service.upload_file(
            file=file,
            s3_key=s3_key,
            content_type=content_type,
        )
        
        return {
            "s3_path": s3_path,
            "s3_key": s3_key,
            "filename": original_filename,
        }

    def _build_success_response(
        self,
        program_id: str,
        program_title: str,
        warnings: List[str],
        checked_files: List[str],
    ) -> Dict:
        """성공 응답 생성"""
        return {
            "program_id": program_id,
            "program_title": program_title,
            "status": "preprocessing",
            "is_valid": True,
            "errors": [],
            "warnings": warnings,
            "checked_files": checked_files,
            "message": "파일 유효성 검사 성공",
        }

    async def _process_program_async(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        comment_csv: UploadFile,
        ladder_document_id: str,
        comment_document_id: str,
        template_document_id: str,
        s3_paths: Dict[str, str],
    ):
        """
        비동기로 프로그램 처리 (전처리, Vector DB 인덱싱)
        S3 업로드는 이미 완료된 상태
        """
        try:
            logger.info(f"비동기 프로그램 처리 시작: program_id={program_id}")

            # 1. 전처리: ZIP 파일에서 JSON 생성, S3 업로드 및 Document 저장
            logger.info(f"전처리 시작: program_id={program_id}")
            # unzip 제거: ZIP 파일을 직접 사용하여 전처리 수행

            # CRUD 인스턴스 생성
            from src.database.crud.document_crud import DocumentCRUD
            from src.database.crud.program_failure_crud import ProcessingFailureCRUD

            document_crud = DocumentCRUD(self.db)
            failure_crud = ProcessingFailureCRUD(self.db)

            # 전처리 수행 (ZIP 파일에서 직접 처리)
            # unzipped_files 대신 ladder_zip 파일을 직접 사용
            preprocess_result = await self.uploader.preprocess_and_create_json(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                unzipped_files=[],  # unzip 제거로 빈 리스트 전달 (ZIP 파일 직접 처리)
                template_xlsx_path=s3_paths.get("template_xlsx_path"),
                comment_csv_path=s3_paths.get("comment_csv_path"),
                ladder_document_id=ladder_document_id,
                db_session=self.db,
                document_crud=document_crud,
                failure_crud=failure_crud,
                chunk_commit_size=50,
            )

            preprocess_summary = preprocess_result.get("summary", {})
            created_documents = preprocess_result.get("created_documents", [])
            failed_files = preprocess_result.get("failed_files", [])

            logger.info(
                f"전처리 완료: {preprocess_summary.get('success', 0)}개 성공, "
                f"{preprocess_summary.get('failed', 0)}개 실패"
            )

            # 부분 실패가 있는 경우 경고 로깅
            has_partial_failure = len(failed_files) > 0

            if has_partial_failure:
                logger.warning(
                    f"부분 실패 발생: program_id={program_id}, "
                    f"전처리 실패: {len(failed_files)}개"
                )

            # 실패 정보 요약을 Program.metadata_json에 저장 (통계용)
            processing_metadata = {
                "total_expected": preprocess_summary.get("total", 0),  # 전처리 결과 기준
                "total_successful_documents": len(created_documents),
                "has_partial_failure": has_partial_failure,
                "preprocessing_summary": preprocess_summary,
                # 실제 실패 정보는 ProcessingFailure 테이블에서 조회
            }

            # Program.metadata_json 업데이트 (통계만)
            from src.database.models.program_models import Program

            program = self.program_crud.get_program(program_id)
            if program:
                current_metadata = program.metadata_json or {}
                current_metadata.update(processing_metadata)
                self.program_crud.update_program(
                    program_id=program_id, metadata_json=current_metadata
                )
                self.db.commit()
                logger.info(f"처리 메타데이터 저장 완료: program_id={program_id}")

            # 5. Vector DB 인덱싱 요청 (비동기)
            logger.info(f"Vector DB 인덱싱 요청 시작: program_id={program_id}")

            # ProcessingJob 테이블에 인덱싱 작업 생성
            from shared_core import ProcessingJobCRUD

            job_crud = ProcessingJobCRUD(self.db)
            job_id = (
                f"vector_indexing_{program_id}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            # 인덱싱 작업 생성
            job_crud.create_job(
                job_id=job_id,
                doc_id=program_id,  # program_id를 doc_id로 사용
                job_type="vector_indexing",
                total_steps=1,
            )
            
            # 프로그램 상태를 indexing으로 변경
            self.program_crud.update_program_status(
                program_id=program_id, status=Program.STATUS_INDEXING
            )
            self.db.commit()
            logger.info(f"Vector DB 인덱싱 작업 생성: job_id={job_id}")

            try:
                # Vector DB 인덱싱 요청
                indexing_success = await self.uploader.request_vector_indexing(
                    program_id=program_id, s3_paths=s3_paths
                )

                if indexing_success:
                    # 인덱싱 작업 성공 처리
                    job_crud.update_job_status(
                        job_id=job_id,
                        status="completed",
                        completed_steps=1,
                        current_step="Vector DB 인덱싱 완료",
                        result_data={"program_id": program_id, "status": "completed"},
                    )

                    # 프로그램 상태 업데이트
                    self.program_crud.update_program_status(
                        program_id=program_id, status=Program.STATUS_COMPLETED
                    )
                    self.program_crud.update_program_vector_info(
                        program_id=program_id, vector_indexed=True
                    )
                    self.db.commit()
                    logger.info(f"프로그램 처리 완료: program_id={program_id}")
                else:
                    # 인덱싱 작업 실패 처리
                    job_crud.update_job_status(
                        job_id=job_id,
                        status="failed",
                        completed_steps=0,
                        current_step="Vector DB 인덱싱 실패",
                        error_message="Vector DB 인덱싱 요청 실패",
                    )

                    # 프로그램 상태 업데이트
                    self.program_crud.update_program_status(
                        program_id=program_id, status=Program.STATUS_FAILED
                    )
                    self.db.commit()
                    logger.warning(f"Vector DB 인덱싱 실패: program_id={program_id}")

            except Exception as indexing_error:
                # 인덱싱 중 예외 발생 처리
                error_msg = str(indexing_error)
                job_crud.update_job_status(
                    job_id=job_id,
                    status="failed",
                    completed_steps=0,
                    current_step="Vector DB 인덱싱 오류",
                    error_message=error_msg,
                )

                self.program_crud.update_program_status(
                    program_id=program_id, status=Program.STATUS_INDEXING_FAILED
                )
                self.db.commit()
                logger.error(
                    f"Vector DB 인덱싱 중 오류: program_id={program_id}, error={error_msg}"
                )
                raise

        except Exception as e:
            logger.error(
                f"비동기 프로그램 처리 중 오류: program_id={program_id}, error={str(e)}"
            )
            from src.database.models.program_models import Program

            self.program_crud.update_program_status(
                program_id=program_id,
                status=Program.STATUS_FAILED,
                error_message=str(e),
            )
            self.db.commit()

    async def get_program(self, program_id: str, user_id: str) -> Dict:
        """프로그램 정보 조회 (팝업 상세 조회용)

        팝업에서 파일 다운로드를 위해 관련 Document 정보 포함
        """
        try:
            from src.database.models.master_models import ProcessMaster
            
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 권한 확인: 사용자가 접근 가능한 공정인지 확인
            if program.process_id:
                accessible_process_ids = (
                    self.program_crud.get_accessible_process_ids(user_id)
                )
                if accessible_process_ids is not None:  # None이면 모든 공정 접근 가능
                    if program.process_id not in accessible_process_ids:
                        raise HandledException(
                            ResponseCode.CHAT_ACCESS_DENIED,
                            msg="프로그램에 접근할 권한이 없습니다.",
                        )

            # 공정명 조회
            process_name = None
            if program.process_id:
                process = (
                    self.db.query(ProcessMaster)
                    .filter(ProcessMaster.process_id == program.process_id)
                    .filter(ProcessMaster.is_active.is_(True))
                    .first()
                )
                if process:
                    process_name = process.process_name

            # 관련 파일 정보 조회 (팝업에서 다운로드 링크 생성용)
            # 원본 파일만 조회 (ZIP, comment, template)
            from src.database.models.document_models import Document

            files = []
            file_types = [
                Document.TYPE_LADDER_LOGIC_ZIP,
                Document.TYPE_COMMENT,
                Document.TYPE_TEMPLATE,
            ]
            documents = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.is_deleted.is_(False))
                .filter(Document.document_type.in_(file_types))
                .all()
            )

            # file_type을 download_file_type으로 매핑
            download_file_type_map = {
                Document.TYPE_TEMPLATE: "program_classification",
                Document.TYPE_LADDER_LOGIC_ZIP: "program_logic",
                Document.TYPE_COMMENT: "program_comment",
            }

            for doc in documents:
                file_info = {
                    "file_type": doc.document_type,
                    "original_filename": doc.original_filename or "unknown",
                    "file_size": doc.file_size or 0,
                    "file_extension": doc.file_extension or "",
                    "download_file_type": download_file_type_map.get(
                        doc.document_type, doc.document_type
                    ),
                }
                files.append(file_info)

            # metadata_json에서 추가 정보 추출
            metadata = program.metadata_json or {}

            return {
                "program_id": program.program_id,
                "program_title": program.program_name,  # program_name 사용
                "program_description": program.description,
                "process_id": program.process_id,
                "process_name": process_name,
                "user_id": program.create_user,  # create_user 사용
                "status": program.status,
                "error_message": program.error_message,
                "create_dt": program.create_dt,
                "update_dt": program.update_dt,
                "completed_at": program.completed_at,
                "files": files,  # 팝업에서 다운로드 링크 생성용
                "ladder_file_count": metadata.get("ladder_file_count", 0),
                "comment_file_count": metadata.get("comment_file_count", 0),
            }
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def get_user_programs(self, user_id: str) -> List[Dict]:
        """사용자의 프로그램 목록 조회"""
        try:
            programs = self.program_crud.get_user_programs(user_id)
            return [
                {
                    "program_id": program.program_id,
                    "program_title": program.program_title,
                    "program_description": program.program_description,
                    "user_id": program.user_id,
                    "status": program.status,
                    "s3_paths": program.s3_paths,
                    "vector_indexed": program.vector_indexed,
                    "vector_collection_name": program.vector_collection_name,
                    "error_message": program.error_message,
                    "created_at": program.created_at,
                    "updated_at": program.updated_at,
                    "processed_at": program.processed_at,
                }
                for program in programs
            ]
        except Exception as e:
            logger.error(f"사용자 프로그램 목록 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def retry_failed_files(
        self, program_id: str, user_id: str, retry_type: str = "all"
    ) -> Dict:
        """
        실패한 파일 재시도

        Args:
            program_id: 프로그램 ID
            user_id: 사용자 ID
            retry_type: 재시도 타입 ("preprocessing", "document", "all")

        Returns:
            Dict: 재시도 결과
        """
        try:
            # 프로그램 정보 조회
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            # 실패 정보 조회 (ProcessingFailure 테이블에서)
            from src.database.crud.program_failure_crud import ProcessingFailureCRUD

            from src.database.models.program_models import ProcessingFailure

            failure_crud = ProcessingFailureCRUD(self.db)

            # 재시도 대상 실패 정보 조회
            failure_type_filter = None
            if retry_type == "preprocessing":
                failure_type_filter = ProcessingFailure.FAILURE_TYPE_PREPROCESSING
            elif retry_type == "document":
                failure_type_filter = ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE

            pending_failures = failure_crud.get_program_failures(
                program_id=program_id,
                failure_type=failure_type_filter,
                status=ProcessingFailure.STATUS_PENDING,
            )

            retry_results = {
                "preprocessing": {"retried": 0, "success": 0, "failed": 0},
                "document": {"retried": 0, "success": 0, "failed": 0},
            }

            # 실패 파일 재시도
            for failure in pending_failures:
                try:
                    # 재시도 횟수 증가
                    failure_crud.increment_retry_count(failure.failure_id)
                    failure_crud.update_failure_status(
                        failure_id=failure.failure_id,
                        status=ProcessingFailure.STATUS_RETRYING,
                    )

                    if (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_PREPROCESSING
                    ):
                        retry_results["preprocessing"]["retried"] += 1
                        # TODO: 전처리 재시도 로직 구현
                        # 재시도 성공 시
                        # failure_crud.mark_as_resolved(
                        #     failure_id=failure.failure_id, resolved_by="manual"
                        # )
                        # retry_results["preprocessing"]["success"] += 1

                    elif (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE
                    ):
                        retry_results["document"]["retried"] += 1

                        # Document 재생성
                        from src.database.crud.document_crud import DocumentCRUD
                        from src.utils.uuid_gen import gen

                        document_crud = DocumentCRUD(self.db)
                        document_id = gen()

                        document_crud.create_document(
                            document_id=document_id,
                            document_name=f"{program.program_title}_{failure.filename}",
                            original_filename=failure.filename,
                            file_key=failure.s3_key,
                            file_size=0,
                            file_type="application/json",
                            file_extension="json",
                            user_id=user_id,
                            upload_path=failure.s3_path,
                            status="processing",
                            document_type=Document.TYPE_COMMON,
                            metadata_json={
                                "program_id": program_id,
                                "program_title": program.program_title,
                                "processing_stage": "preprocessed",
                                "retry_count": failure.retry_count,
                                "is_retry": True,
                                "failure_id": failure.failure_id,
                            },
                        )
                        self.db.commit()

                        # 재시도 성공
                        failure_crud.mark_as_resolved(
                            failure_id=failure.failure_id, resolved_by="manual"
                        )
                        retry_results["document"]["success"] += 1
                        logger.info(
                            f"Document 재생성 성공: failure_id={failure.failure_id}, "
                            f"filename={failure.filename}"
                        )

                except Exception as e:
                    # 재시도 실패
                    if (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_PREPROCESSING
                    ):
                        retry_results["preprocessing"]["failed"] += 1
                    elif (
                        failure.failure_type
                        == ProcessingFailure.FAILURE_TYPE_DOCUMENT_STORAGE
                    ):
                        retry_results["document"]["failed"] += 1

                    failure_crud.update_failure_status(
                        failure_id=failure.failure_id,
                        status=ProcessingFailure.STATUS_PENDING,
                        error_message=str(e),
                    )
                    self.db.rollback()
                    logger.error(
                        f"재시도 실패: failure_id={failure.failure_id}, "
                        f"error: {str(e)}"
                    )
                    continue

            # 재시도 이력 저장 (통계용)
            if (
                retry_results["preprocessing"]["retried"] > 0
                or retry_results["document"]["retried"] > 0
            ):
                program = self.program_crud.get_program(program_id)
                if program:
                    current_metadata = program.metadata_json or {}
                    retry_history = current_metadata.get("retry_history", [])
                    retry_history.append(
                        {
                            "retry_type": retry_type,
                            "timestamp": datetime.now().isoformat(),
                            "results": retry_results,
                        }
                    )
                    current_metadata["retry_history"] = retry_history
                    self.program_crud.update_program(
                        program_id=program_id, metadata_json=current_metadata
                    )
                    self.db.commit()

            return {
                "program_id": program_id,
                "retry_type": retry_type,
                "results": retry_results,
                "message": "재시도 완료",
            }

        except HandledException:
            raise
        except Exception as e:
            logger.error(f"재시도 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def get_program_failures(
        self, program_id: str, user_id: str, failure_type: Optional[str] = None
    ) -> List[Dict]:
        """프로그램의 실패 정보 목록 조회"""
        try:
            # 프로그램 정보 조회
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            # 실패 정보 조회
            from src.database.crud.program_failure_crud import ProcessingFailureCRUD
            from src.database.models.program_models import ProcessingFailure

            failure_crud = ProcessingFailureCRUD(self.db)
            failures = failure_crud.get_program_failures(
                program_id=program_id, failure_type=failure_type
            )

            return [
                {
                    "failure_id": failure.failure_id,
                    "source_type": failure.source_type,
                    "source_id": failure.source_id,
                    "program_id": (
                        failure.source_id
                        if failure.source_type
                        == ProcessingFailure.SOURCE_TYPE_PROGRAM
                        else None
                    ),  # 호환성을 위해 유지
                    "failure_type": failure.failure_type,
                    "file_path": failure.file_path,
                    "file_index": failure.file_index,
                    "filename": failure.filename,
                    "s3_path": failure.s3_path,
                    "s3_key": failure.s3_key,
                    "error_message": failure.error_message,
                    "error_details": failure.error_details,
                    "retry_count": failure.retry_count,
                    "max_retry_count": failure.max_retry_count,
                    "status": failure.status,
                    "resolved_at": (
                        failure.resolved_at.isoformat() if failure.resolved_at else None
                    ),
                    "last_retry_at": (
                        failure.last_retry_at.isoformat()
                        if failure.last_retry_at
                        else None
                    ),
                    "resolved_by": failure.resolved_by,
                    "created_at": failure.created_at.isoformat(),
                    "updated_at": (
                        failure.updated_at.isoformat() if failure.updated_at else None
                    ),
                }
                for failure in failures
            ]
        except HandledException:
            raise
        except Exception as e:
            logger.error(f"실패 정보 조회 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def delete_program(
        self, program_id: str, user_id: Optional[str] = None
    ) -> Dict:
        """
        프로그램 삭제 (S3 파일, Documents, Knowledge, 관련 테이블 메타정보 처리)

        Args:
            program_id: 삭제할 프로그램 ID
            user_id: 사용자 ID (권한 확인용, 선택)

        Returns:
            Dict: 삭제 결과
        """
        try:
            # 프로그램 정보 조회
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인 (user_id가 제공된 경우)
            if user_id and program.create_user != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램을 삭제할 권한이 없습니다.",
                )

            logger.info(f"프로그램 삭제 시작: program_id={program_id}")

            # 병렬로 실행할 작업들
            tasks = []

            # 1. S3 파일 삭제 (비동기)
            async def delete_s3_files():
                try:
                    await self._delete_s3_files(program_id, program)
                    return {"s3_deleted": True}
                except Exception as e:
                    logger.error(f"S3 파일 삭제 실패: {str(e)}")
                    return {"s3_deleted": False, "error": str(e)}

            # 2. Documents 및 Knowledge 삭제 (비동기)
            async def delete_documents_and_knowledge():
                try:
                    result = await self._delete_documents_and_knowledge(
                        program_id
                    )
                    return result
                except Exception as e:
                    logger.error(f"Documents/Knowledge 삭제 실패: {str(e)}")
                    return {"deleted": False, "error": str(e)}

            # 병렬 실행
            tasks.append(delete_s3_files())
            tasks.append(delete_documents_and_knowledge())

            results = await asyncio.gather(*tasks, return_exceptions=True)

            s3_result = results[0] if not isinstance(results[0], Exception) else {}
            docs_result = (
                results[1] if not isinstance(results[1], Exception) else {}
            )

            # 3. 관련 테이블 메타정보 업데이트
            try:
                self._update_related_tables_metadata(program_id)
            except Exception as e:
                logger.error(f"관련 테이블 메타정보 업데이트 실패: {str(e)}")

            # 4. Program 삭제 (소프트 삭제)
            success = self.program_crud.delete_program(program_id)

            if not success:
                raise HandledException(
                    ResponseCode.DATABASE_QUERY_ERROR,
                    msg="프로그램 삭제에 실패했습니다.",
                )

            logger.info(f"프로그램 삭제 완료: program_id={program_id}")

            return {
                "program_id": program_id,
                "deleted": True,
                "s3_deletion": s3_result,
                "documents_deletion": docs_result,
                "message": "프로그램이 삭제되었습니다.",
            }

        except HandledException:
            raise
        except Exception as e:
            logger.error(f"프로그램 삭제 중 오류: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    async def _delete_s3_files(self, program_id: str, program):
        """S3 파일 삭제"""
        try:
            if not self.s3_service:
                logger.warning("S3 서비스가 초기화되지 않아 파일 삭제를 건너뜁니다.")
                return

            # S3 프로그램 경로 prefix 가져오기
            program_prefix = settings.s3_program_prefix.rstrip("/")
            # {program_prefix}/{program_id}/ 디렉토리 전체 삭제
            prefix = f"{program_prefix}/{program_id}/"

            try:
                # S3Service의 delete_files_by_prefix 사용
                deleted_count = await self.s3_service.delete_files_by_prefix(prefix=prefix)
                
                if deleted_count > 0:
                    logger.info(
                        f"S3 파일 삭제 완료: program_id={program_id}, "
                        f"deleted_count={deleted_count}"
                    )
                else:
                    logger.info(
                        f"S3에 삭제할 파일이 없습니다: program_id={program_id}, "
                        f"prefix={prefix}"
                    )

            except Exception as e:
                logger.error(f"S3 파일 삭제 중 오류: program_id={program_id}, error={str(e)}")
                raise

        except Exception as e:
            logger.error(f"S3 파일 삭제 실패: program_id={program_id}, error={str(e)}")
            raise

    async def _delete_documents_and_knowledge(self, program_id: str) -> Dict:
        """Documents 및 Knowledge (Milvus 벡터) 삭제"""
        try:
            # program_id로 Documents 조회
            documents = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.is_deleted.is_(False))
                .all()
            )

            deleted_count = 0
            vector_deleted_count = 0
            errors = []

            for document in documents:
                try:
                    # Milvus 벡터 삭제
                    if document.milvus_collection_name:
                        try:
                            await self._delete_milvus_vectors(
                                document.document_id,
                                document.milvus_collection_name,
                            )
                            vector_deleted_count += 1
                        except Exception as e:
                            logger.warning(
                                f"Milvus 벡터 삭제 실패: "
                                f"document_id={document.document_id}, "
                                f"error={str(e)}"
                            )
                            errors.append(
                                {
                                    "document_id": document.document_id,
                                    "error": f"Milvus 삭제 실패: {str(e)}",
                                }
                            )

                    # Document 소프트 삭제
                    document.is_deleted = True
                    document.updated_at = datetime.now()
                    deleted_count += 1

                except Exception as e:
                    logger.error(
                        f"Document 삭제 실패: document_id={document.document_id}, "
                        f"error={str(e)}"
                    )
                    errors.append(
                        {
                            "document_id": document.document_id,
                            "error": str(e),
                        }
                    )

            # DB 커밋
            self.db.commit()

            return {
                "deleted": True,
                "documents_deleted": deleted_count,
                "vectors_deleted": vector_deleted_count,
                "total_documents": len(documents),
                "errors": errors,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Documents/Knowledge 삭제 실패: {str(e)}")
            raise

    async def _delete_milvus_vectors(
        self, document_id: str, collection_name: str
    ):
        """Milvus에서 벡터 삭제"""
        try:
            from pymilvus import Collection, connections, utility

            # Milvus 연결 설정 (환경변수에서 가져오기)
            import os

            milvus_uri = os.getenv("MILVUS_URI", "./milvus_lite.db")
            connections.connect("default", uri=milvus_uri)

            # 컬렉션이 존재하는지 확인
            if not utility.has_collection(collection_name):
                logger.warning(
                    f"Milvus 컬렉션이 없습니다: {collection_name}"
                )
                return

            # 컬렉션 로드
            collection = Collection(collection_name)
            collection.load()

            # document_path로 벡터 삭제
            # Document의 upload_path나 file_key를 사용하여 삭제
            # document_path 필드에 document_id나 file_key가 저장되어 있을 것으로 예상
            expr = f'document_path like "%{document_id}%"'

            try:
                collection.delete(expr=expr)
                collection.flush()
                logger.info(
                    f"Milvus 벡터 삭제 완료: document_id={document_id}, "
                    f"collection={collection_name}"
                )
            except Exception as e:
                logger.warning(
                    f"Milvus 벡터 삭제 실패: document_id={document_id}, "
                    f"error={str(e)}"
                )
                # 삭제 실패해도 계속 진행

        except Exception as e:
            logger.error(f"Milvus 벡터 삭제 중 오류: {str(e)}")
            # Milvus 삭제 실패해도 전체 프로세스는 계속 진행

    def _update_related_tables_metadata(self, program_id: str):
        """관련 테이블 메타정보 업데이트"""
        try:
            from src.database.models.plc_models import PLC

            # 1. PLC 테이블: program_id 매핑 해제 및 is_active = False
            plcs = (
                self.db.query(PLC)
                .filter(PLC.program_id == program_id)
                .filter(PLC.is_active.is_(True))
                .all()
            )

            for plc in plcs:
                plc.program_id = None
                plc.is_active = False
                plc.update_dt = datetime.now()
                plc.update_user = "system"  # 시스템 삭제

            # 2. ProcessingFailure: status를 'deleted'로 업데이트
            from src.database.models.program_models import ProcessingFailure

            failures = (
                self.db.query(ProcessingFailure)
                .filter(
                    ProcessingFailure.source_type
                    == ProcessingFailure.SOURCE_TYPE_PROGRAM
                )
                .filter(ProcessingFailure.source_id == program_id)
                .filter(ProcessingFailure.status != "deleted")
                .all()
            )

            for failure in failures:
                failure.status = "deleted"
                failure.updated_at = datetime.now()

            # 3. ProgramLLMDataChunk: 삭제 (또는 is_deleted 플래그가 있다면 사용)
            from src.database.models.program_models import ProgramLLMDataChunk

            chunks = (
                self.db.query(ProgramLLMDataChunk)
                .filter(ProgramLLMDataChunk.program_id == program_id)
                .all()
            )

            # ProgramLLMDataChunk에는 is_deleted가 없으므로 실제 삭제
            for chunk in chunks:
                self.db.delete(chunk)

            # 4. KnowledgeReference: Document를 통해 연결된 것들 삭제
            from src.database.models.knowledge_reference_models import (
                KnowledgeReference,
            )
            from src.database.models.document_models import Document

            # Program과 연결된 Document를 통해 KnowledgeReference 조회
            documents_with_ref = (
                self.db.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.knowledge_reference_id.isnot(None))
                .all()
            )

            knowledge_ref_ids = {
                doc.knowledge_reference_id
                for doc in documents_with_ref
                if doc.knowledge_reference_id
            }

            knowledge_refs = []
            if knowledge_ref_ids:
                knowledge_refs = (
                    self.db.query(KnowledgeReference)
                    .filter(
                        KnowledgeReference.reference_id.in_(knowledge_ref_ids)
                    )
                    .all()
                )

                for ref in knowledge_refs:
                    # is_deleted가 있다면 사용, 없으면 실제 삭제
                    if hasattr(ref, "is_deleted"):
                        ref.is_deleted = True
                    else:
                        self.db.delete(ref)

            # DB 커밋
            self.db.commit()

            logger.info(
                f"관련 테이블 메타정보 업데이트 완료: "
                f"PLC={len(plcs)}, "
                f"ProcessingFailure={len(failures)}, "
                f"ProgramLLMDataChunk={len(chunks)}, "
                f"KnowledgeReference={len(knowledge_refs)}"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"관련 테이블 메타정보 업데이트 실패: {str(e)}")
            raise
