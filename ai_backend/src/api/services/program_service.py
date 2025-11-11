# _*_ coding: utf-8 _*_
"""Program Service for handling program registration and management."""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session
from shared_core.models import Document
from src.api.services.program_uploader import ProgramUploader
from src.api.services.program_validator import ProgramValidator
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen

logger = logging.getLogger(__name__)


class ProgramService:
    """프로그램 관리 서비스"""

    def __init__(self, db: Session, uploader: ProgramUploader = None):
        """
        Args:
            db: 데이터베이스 세션
            uploader: ProgramUploader 인스턴스
        """
        self.db = db
        self.validator = ProgramValidator()
        self.uploader = uploader or ProgramUploader()
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
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
    ) -> Dict:
        """
        프로그램 등록 (유효성 검사 + 비동기 처리)

        Returns:
            Dict: 프로그램 등록 결과
        """
        try:
            program_id = gen()

            # 1. 유효성 검사
            validation_result = self._validate_program_files(
                program_id=program_id,
                ladder_zip=ladder_zip,
                classification_xlsx=classification_xlsx,
                device_comment_csv=device_comment_csv,
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
                    ladder_zip=ladder_zip,
                    classification_xlsx=classification_xlsx,
                    device_comment_csv=device_comment_csv,
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
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
    ) -> Dict:
        """프로그램 파일 유효성 검사"""
        logger.info(f"프로그램 유효성 검사 시작: program_id={program_id}")
        is_valid, errors, warnings, checked_files = self.validator.validate_files(
            ladder_zip=ladder_zip,
            classification_xlsx=classification_xlsx,
            device_comment_csv=device_comment_csv,
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
    ):
        """프로그램 메타데이터 저장"""
        logger.info(f"프로그램 메타데이터 저장 시작: program_id={program_id}")
        from src.database.models.program_models import Program

        self.program_crud.create_program(
            program_id=program_id,
            program_name=program_title,
            create_user=user_id,
            description=program_description,
            status=Program.STATUS_PROCESSING,
            metadata_json=None,
        )
        self.db.commit()
        logger.info(f"프로그램 메타데이터 저장 완료: program_id={program_id}")

    def _create_templates_and_data(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        classification_xlsx: UploadFile,
    ) -> Dict:
        """템플릿 및 템플릿데이터 생성"""
        logger.info(f"템플릿 및 템플릿데이터 생성 시작: program_id={program_id}")
        from src.database.crud.template_crud import TemplateCRUD, TemplateDataCRUD
        from src.database.crud.document_crud import DocumentCRUD
        import pandas as pd
        import io

        template_crud = TemplateCRUD(self.db)
        template_data_crud = TemplateDataCRUD(self.db)
        document_crud = DocumentCRUD(self.db)

        # classification_xlsx 파일 읽기
        classification_xlsx.file.seek(0)
        xlsx_content = classification_xlsx.file.read()
        classification_xlsx.file.seek(0)
        df = pd.read_excel(io.BytesIO(xlsx_content))

        # 템플릿 Document 생성
        template_document_id = gen()
        document_crud.create_document(
            document_id=template_document_id,
            document_name=f"{program_title}_template",
            original_filename="classification.xlsx",
            file_key=None,
            file_size=len(xlsx_content),
            file_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            file_extension="xlsx",
            user_id=user_id,
            upload_path=None,
            status="processing",
            document_type="common",
            program_id=program_id,
            program_file_type="template",
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        # 템플릿 생성
        template_id = gen()
        template_crud.create_template(
            template_id=template_id,
            document_id=template_document_id,
            created_by=user_id,
            program_id=program_id,
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        # 템플릿데이터 생성
        template_data_list = self._create_template_data_rows(
            df=df,
            template_id=template_id,
            program_id=program_id,
            template_data_crud=template_data_crud,
        )

        self.db.commit()
        total_expected = len(template_data_list)
        logger.info(
            f"템플릿 및 템플릿데이터 생성 완료: program_id={program_id}, "
            f"template_id={template_id}, template_data_count={total_expected}"
        )

        return {
            "template_document_id": template_document_id,
            "template_data_list": template_data_list,
            "total_expected": total_expected,
        }

    def _create_template_data_rows(
        self,
        df,
        template_id: str,
        program_id: str,
        template_data_crud,
    ) -> List[Dict]:
        """템플릿데이터 행 생성"""
        template_data_list = []
        for idx, row in df.iterrows():
            template_data_id = gen()

            # 엑셀 컬럼에서 직접 값 추출
            logic_id = str(
                row.get("LOGIC_ID", row.get("로직파일명", f"logic_{idx}"))
            ).strip()
            logic_name = str(
                row.get("LOGIC_NAME", row.get("로직파일명", logic_id))
            ).strip()
            folder_id = str(row.get("FOLDER_ID", "")).strip() or None
            folder_name = str(row.get("FOLDER_NAME", "")).strip() or None
            sub_folder_name = str(row.get("SUB_FOLDER_NAME", "")).strip() or None

            # 기존 형식 호환성
            classification = str(row.get("분류", "")).strip()
            template_name = str(row.get("템플릿명", "")).strip()

            template_data_crud.create_template_data(
                template_data_id=template_data_id,
                template_id=template_id,
                logic_id=logic_id,
                logic_name=logic_name,
                row_index=idx,
                folder_id=folder_id,
                folder_name=folder_name,
                sub_folder_name=sub_folder_name,
                document_id=None,
                metadata_json={
                    "program_id": program_id,
                    "classification": classification if classification else None,
                    "template_name": template_name if template_name else None,
                },
            )
            template_data_list.append({
                "template_data_id": template_data_id,
                "logic_id": logic_id,
                "logic_name": logic_name,
            })

        return template_data_list

    def _create_program_documents(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        ladder_zip: UploadFile,
        device_comment_csv: UploadFile,
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
            status="processing",
            document_type="common",
            program_id=program_id,
            program_file_type="ladder_logic",
            metadata_json={
                "program_id": program_id,
                "program_title": program_title,
            },
        )

        # device_comment_csv Document 생성
        comment_document_id = gen()
        device_comment_csv.file.seek(0)
        comment_csv_size = len(device_comment_csv.file.read())
        device_comment_csv.file.seek(0)

        document_crud.create_document(
            document_id=comment_document_id,
            document_name=f"{program_title}_device_comment",
            original_filename=device_comment_csv.filename or "device_comment.csv",
            file_key=None,
            file_size=comment_csv_size,
            file_type="text/csv",
            file_extension="csv",
            user_id=user_id,
            upload_path=None,
            status="processing",
            document_type="common",
            program_id=program_id,
            program_file_type="comment",
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
        self, program_id: str, total_expected: int
    ):
        """Program.metadata_json 업데이트

        프로그램 등록 시점에 파일 개수 메타정보 저장
        - total_expected: 전처리 예상 파일 수 (TemplateData 개수)
        - ladder_file_count: Logic 파일 개수 (전체 파일 개수)
        - comment_file_count: Comment 파일 개수 (항상 1개)
        """
        self.program_crud.update_program(
            program_id=program_id,
            metadata_json={
                "total_expected": total_expected,
                "ladder_file_count": total_expected,  # Logic 파일 개수
                "comment_file_count": 1,  # Comment 파일 개수 (항상 1개)
            },
        )
        self.db.commit()

    async def _complete_program_registration_async(
        self,
        program_id: str,
        program_title: str,
        program_description: Optional[str],
        user_id: str,
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
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
            )

            # 2. 템플릿 및 템플릿데이터 생성
            template_result = self._create_templates_and_data(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                classification_xlsx=classification_xlsx,
            )
            template_document_id = template_result["template_document_id"]
            template_data_list = template_result["template_data_list"]
            total_expected = template_result["total_expected"]

            # 3. Document 생성 (ladder_logic, comment, template)
            document_ids = self._create_program_documents(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                ladder_zip=ladder_zip,
                device_comment_csv=device_comment_csv,
                template_document_id=template_document_id,
            )

            # 4. Program.metadata_json 업데이트
            self._update_program_metadata(
                program_id=program_id, total_expected=total_expected
            )

            # 5. S3 업로드 및 전처리 시작
            await self._process_program_async(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                ladder_zip=ladder_zip,
                classification_xlsx=classification_xlsx,
                device_comment_csv=device_comment_csv,
                ladder_document_id=document_ids["ladder_document_id"],
                comment_document_id=document_ids["comment_document_id"],
                template_document_id=document_ids["template_document_id"],
                template_data_list=template_data_list,
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
            "status": "processing",
            "is_valid": True,
            "errors": [],
            "warnings": warnings,
            "checked_files": checked_files,
            "message": "파일 등록 요청하였습니다.",
        }

    async def _process_program_async(
        self,
        program_id: str,
        program_title: str,
        user_id: str,
        ladder_zip: UploadFile,
        classification_xlsx: UploadFile,
        device_comment_csv: UploadFile,
        ladder_document_id: str,
        comment_document_id: str,
        template_document_id: str,
        template_data_list: list,
    ):
        """
        비동기로 프로그램 처리 (S3 업로드, DB 저장, Vector DB 인덱싱)
        """
        try:
            logger.info(f"비동기 프로그램 처리 시작: program_id={program_id}")

            # 1. S3에 파일 업로드 및 ZIP 압축 해제 (비동기)
            logger.info(f"S3 업로드 시작: program_id={program_id}")
            s3_paths = await self.uploader.upload_and_unzip(
                ladder_zip=ladder_zip,
                classification_xlsx=classification_xlsx,
                device_comment_csv=device_comment_csv,
                program_id=program_id,
                user_id=user_id,
            )
            logger.info(f"S3 업로드 완료: program_id={program_id}")

            # 2. Document에 S3 경로 업데이트 (비동기)
            logger.info(f"Document S3 경로 업데이트 시작: program_id={program_id}")
            from src.database.crud.document_crud import DocumentCRUD
            document_crud = DocumentCRUD(self.db)

            # ladder_document 업데이트
            if ladder_document_id and s3_paths.get("ladder_zip_path"):
                document_crud.update_document(
                    document_id=ladder_document_id,
                    file_key=f"programs/{program_id}/ladder_logic.zip",
                    upload_path=s3_paths.get("ladder_zip_path"),
                )

            # comment_document 업데이트
            if comment_document_id and s3_paths.get("device_comment_csv_path"):
                document_crud.update_document(
                    document_id=comment_document_id,
                    file_key=f"programs/{program_id}/device_comment.csv",
                    upload_path=s3_paths.get("device_comment_csv_path"),
                )

            # template_document 업데이트
            if template_document_id and s3_paths.get("classification_xlsx_path"):
                document_crud.update_document(
                    document_id=template_document_id,
                    file_key=f"programs/{program_id}/classification.xlsx",
                    upload_path=s3_paths.get("classification_xlsx_path"),
                )

            self.db.commit()
            logger.info(f"Document S3 경로 업데이트 완료: program_id={program_id}")

            # 3. 전처리: ZIP 압축 해제 파일들로 JSON 생성, S3 업로드 및 Document 저장
            logger.info(f"전처리 시작: program_id={program_id}")
            unzipped_files = s3_paths.get("unzipped_files", [])

            # CRUD 인스턴스 생성
            from src.database.crud.document_crud import DocumentCRUD
            from src.database.crud.program_failure_crud import ProcessingFailureCRUD
            from src.database.crud.template_crud import TemplateDataCRUD

            document_crud = DocumentCRUD(self.db)
            failure_crud = ProcessingFailureCRUD(self.db)
            template_data_crud = TemplateDataCRUD(self.db)

            # template_data_list를 logic_id로 매핑 (빠른 조회를 위해)
            template_data_map = {
                td["logic_id"]: td for td in template_data_list
            }

            # 전처리 수행 (각 파일마다 즉시 Document 저장)
            preprocess_result = await self.uploader.preprocess_and_create_json(
                program_id=program_id,
                program_title=program_title,
                user_id=user_id,
                unzipped_files=unzipped_files,
                classification_xlsx_path=s3_paths.get("classification_xlsx_path"),
                device_comment_csv_path=s3_paths.get("device_comment_csv_path"),
                db_session=self.db,
                document_crud=document_crud,
                template_data_crud=template_data_crud,
                failure_crud=failure_crud,
                template_data_map=template_data_map,
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
                "total_expected": len(unzipped_files),
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
                        program_id=program_id, status=Program.STATUS_INDEXING_FAILED
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
        """프로그램 정보 조회"""
        try:
            program = self.program_crud.get_program(program_id)
            if not program:
                raise HandledException(ResponseCode.PROGRAM_NOT_FOUND)

            # 사용자 권한 확인
            if program.user_id != user_id:
                raise HandledException(
                    ResponseCode.CHAT_ACCESS_DENIED,
                    msg="프로그램에 접근할 권한이 없습니다.",
                )

            return {
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
                            document_type="common",
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
            # metadata_json에서 S3 경로 정보 추출
            metadata = program.metadata_json or {}
            s3_paths = metadata.get("s3_paths", {})

            if not s3_paths and not self.uploader.s3_client:
                logger.warning(
                    "S3 클라이언트가 없거나 경로 정보가 없습니다."
                )
                return

            # S3 클라이언트가 있는 경우
            if self.uploader.s3_client and self.uploader.s3_bucket:
                # programs/{program_id}/ 디렉토리 전체 삭제
                prefix = f"programs/{program_id}/"

                try:
                    # S3에서 해당 prefix의 모든 객체 삭제
                    paginator = self.uploader.s3_client.get_paginator(
                        "list_objects_v2"
                    )
                    pages = paginator.paginate(
                        Bucket=self.uploader.s3_bucket, Prefix=prefix
                    )

                    objects_to_delete = []
                    for page in pages:
                        if "Contents" in page:
                            for obj in page["Contents"]:
                                objects_to_delete.append({"Key": obj["Key"]})

                    if objects_to_delete:
                        # 1000개씩 나누어 삭제 (S3 제한)
                        for i in range(0, len(objects_to_delete), 1000):
                            chunk = objects_to_delete[i:i + 1000]
                            self.uploader.s3_client.delete_objects(
                                Bucket=self.uploader.s3_bucket,
                                Delete={"Objects": chunk},
                            )
                        logger.info(
                            f"S3 파일 삭제 완료: {len(objects_to_delete)}개 파일"
                        )
                    else:
                        logger.info(f"S3에 삭제할 파일이 없습니다: {prefix}")

                except Exception as e:
                    logger.error(f"S3 파일 삭제 중 오류: {str(e)}")
                    raise
            else:
                logger.warning(
                    "S3 클라이언트가 초기화되지 않아 파일 삭제를 건너뜁니다."
                )

        except Exception as e:
            logger.error(f"S3 파일 삭제 실패: {str(e)}")
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
            from shared_core.models import Document

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
