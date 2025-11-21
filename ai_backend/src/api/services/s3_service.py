# _*_ coding: utf-8 _*_
"""S3 업로드/다운로드 통합 서비스"""
import io
import logging
import os
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile
from src.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """S3 업로드/다운로드 통합 서비스"""

    def __init__(
        self,
        s3_client=None,
        s3_bucket: str = None,
        s3_region: str = None,
    ):
        """
        Args:
            s3_client: S3 클라이언트 (boto3)
            s3_bucket: S3 버킷 이름 (없으면 settings에서 가져옴)
            s3_region: S3 리전 (없으면 settings에서 가져옴)
        """
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket or settings.get_s3_bucket_name()
        self.s3_region = s3_region or settings.aws_region

    # ==================== 업로드 기능 ====================

    async def upload_file(
        self,
        file: UploadFile,
        s3_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        파일을 S3에 업로드

        Args:
            file: 업로드할 파일 (UploadFile)
            s3_key: S3 객체 키 (경로)
            content_type: Content-Type (없으면 파일에서 추론)

        Returns:
            str: S3 경로 (s3://bucket/key 형식)

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
            Exception: 업로드 실패 시
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            # 파일 내용 읽기
            file.file.seek(0)
            file_content = file.file.read()
            file.file.seek(0)

            # Content-Type 결정
            if not content_type:
                content_type = file.content_type or "application/octet-stream"

            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
            )

            logger.info(
                "S3 파일 업로드 완료: s3_key=%s, size=%d bytes",
                s3_key,
                len(file_content),
            )
            return f"s3://{self.s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error("S3 파일 업로드 실패: s3_key=%s, error=%s", s3_key, str(e))
            raise

    async def upload_bytes(
        self,
        content: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        바이트 데이터를 S3에 업로드

        Args:
            content: 업로드할 바이트 데이터
            s3_key: S3 객체 키 (경로)
            content_type: Content-Type

        Returns:
            str: S3 경로 (s3://bucket/key 형식)

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
            Exception: 업로드 실패 시
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
            )

            logger.info(
                "S3 바이트 업로드 완료: s3_key=%s, size=%d bytes",
                s3_key,
                len(content),
            )
            return f"s3://{self.s3_bucket}/{s3_key}"

        except Exception as e:
            logger.error("S3 바이트 업로드 실패: s3_key=%s, error=%s", s3_key, str(e))
            raise

    async def upload_string(
        self,
        content: str,
        s3_key: str,
        encoding: str = "utf-8",
        content_type: str = "text/plain",
    ) -> str:
        """
        문자열을 S3에 업로드

        Args:
            content: 업로드할 문자열
            s3_key: S3 객체 키 (경로)
            encoding: 인코딩 (기본값: utf-8)
            content_type: Content-Type (기본값: text/plain)

        Returns:
            str: S3 경로 (s3://bucket/key 형식)

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
            Exception: 업로드 실패 시
        """
        try:
            content_bytes = content.encode(encoding)
            return await self.upload_bytes(content_bytes, s3_key, content_type)

        except Exception as e:
            logger.error("S3 문자열 업로드 실패: s3_key=%s, error=%s", s3_key, str(e))
            raise

    async def upload_zip_and_extract(
        self,
        zip_file: UploadFile,
        s3_prefix: str,
    ) -> List[str]:
        """
        ZIP 파일을 S3에 업로드하고 압축 해제하여 각 파일을 개별적으로 업로드

        Args:
            zip_file: ZIP 파일 (UploadFile)
            s3_prefix: 압축 해제된 파일들의 S3 경로 prefix

        Returns:
            List[str]: 업로드된 파일들의 S3 키 목록

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
            Exception: 업로드 실패 시
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            zip_file.file.seek(0)
            zip_content = zip_file.file.read()
            zip_file.file.seek(0)

            uploaded_files = []

            # 임시 디렉토리에 압축 해제
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                with zipfile.ZipFile(io.BytesIO(zip_content), "r") as zip_ref:
                    zip_ref.extractall(temp_path)

                    # 압축 해제된 파일들을 S3에 업로드
                    for root, _, files in os.walk(temp_path):
                        for file_name in files:
                            local_file_path = Path(root) / file_name
                            relative_path = local_file_path.relative_to(temp_path)
                            s3_key = (
                                f"{s3_prefix}{relative_path.as_posix()}"
                            )

                            # 파일 읽기
                            with open(local_file_path, "rb") as f:
                                file_content = f.read()

                            # Content-Type 추론
                            content_type = self._guess_content_type(file_name)

                            # S3에 업로드
                            self.s3_client.put_object(
                                Bucket=self.s3_bucket,
                                Key=s3_key,
                                Body=file_content,
                                ContentType=content_type,
                            )

                            uploaded_files.append(s3_key)
                            logger.debug(
                                "압축 해제 파일 S3 업로드: s3_key=%s", s3_key
                            )

            logger.info(
                "ZIP 압축 해제 및 업로드 완료: %d개 파일", len(uploaded_files)
            )
            return uploaded_files

        except Exception as e:
            logger.error("ZIP 압축 해제 및 업로드 실패: error=%s", str(e))
            raise

    async def upload_program_files(
        self,
        ladder_zip: UploadFile,
        template_xlsx: UploadFile,
        comment_csv: UploadFile,
        program_id: str,
    ) -> Dict[str, str]:
        """
        프로그램 등록 시 필요한 파일들을 S3에 업로드

        Args:
            ladder_zip: Logic 파일 ZIP
            template_xlsx: 템플릿 분류 체계 XLSX 파일
            comment_csv: Comment CSV 파일
            program_id: 프로그램 ID

        Returns:
            Dict[str, str]: 업로드된 파일들의 S3 경로 정보
                {
                    'ladder_zip_path': 's3://...',
                    'unzipped_base_path': '{s3_program_prefix}/{program_id}/unzipped/',
                    'unzipped_files': [...],
                    'template_xlsx_path': 's3://...',
                    'comment_csv_path': 's3://...'
                }
        """
        try:
            # S3 프로그램 경로 prefix 가져오기
            program_prefix = settings.s3_program_prefix.rstrip("/")
            
            # 원본 파일명 가져오기 (안전하게 처리)
            ladder_zip_filename = ladder_zip.filename or "ladder_logic.zip"
            template_xlsx_filename = template_xlsx.filename or "template.xlsx"
            comment_csv_filename = comment_csv.filename or "comment.csv"
            
            # 1. ZIP 파일 S3 업로드 (원본 파일명 사용)
            ladder_zip_path = await self.upload_file(
                file=ladder_zip,
                s3_key=f"{program_prefix}/{program_id}/{ladder_zip_filename}",
                content_type="application/zip",
            )

            # 2. ZIP 파일 압축 해제 및 개별 파일 업로드
            unzipped_files = await self.upload_zip_and_extract(
                zip_file=ladder_zip,
                s3_prefix=f"{program_prefix}/{program_id}/unzipped/",
            )

            # 3. XLSX 파일 S3 업로드 (원본 파일명 사용)
            template_xlsx_path = await self.upload_file(
                file=template_xlsx,
                s3_key=f"{program_prefix}/{program_id}/{template_xlsx_filename}",
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            # 4. CSV 파일 S3 업로드 (원본 파일명 사용)
            comment_csv_path = await self.upload_file(
                file=comment_csv,
                s3_key=f"{program_prefix}/{program_id}/{comment_csv_filename}",
                content_type="text/csv",
            )

            return {
                "ladder_zip_path": ladder_zip_path,
                "ladder_zip_filename": ladder_zip_filename,
                "unzipped_base_path": f"{program_prefix}/{program_id}/unzipped/",
                "unzipped_files": unzipped_files,
                "template_xlsx_path": template_xlsx_path,
                "template_xlsx_filename": template_xlsx_filename,
                "comment_csv_path": comment_csv_path,
                "comment_csv_filename": comment_csv_filename,
            }

        except Exception as e:
            logger.error(
                "프로그램 파일 업로드 실패: program_id=%s, error=%s",
                program_id,
                str(e),
            )
            raise

    def list_files(self, prefix: str) -> List[Dict[str, Any]]:
        """
        S3 prefix 하위의 파일 목록 조회
        
        Args:
            prefix: S3 prefix (예: "programs/{program_id}/")
            
        Returns:
            List[Dict]: 파일 정보 목록
                [
                    {
                        'key': 'programs/{program_id}/file.zip',
                        'filename': 'file.zip',
                        'size': 12345,
                        'last_modified': '2024-01-01T00:00:00Z'
                    },
                    ...
                ]
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")
            
            files = []
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)
            
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        # 디렉토리가 아닌 파일만 추가
                        if not key.endswith("/"):
                            filename = key.split("/")[-1]
                            files.append({
                                "key": key,
                                "filename": filename,
                                "size": obj.get("Size", 0),
                                "last_modified": obj.get("LastModified").isoformat() if obj.get("LastModified") else None,
                            })
            
            logger.info(f"S3 파일 목록 조회 완료: prefix={prefix}, count={len(files)}")
            return files
            
        except Exception as e:
            logger.error(f"S3 파일 목록 조회 실패: prefix={prefix}, error={str(e)}")
            raise

    # ==================== 다운로드 기능 ====================

    @staticmethod
    def _parse_s3_path(s3_path: str) -> Tuple[str, str]:
        """
        S3 경로에서 버킷과 키 추출
        
        Args:
            s3_path: S3 경로 (예: "s3://bucket-name/path/to/file")
            
        Returns:
            Tuple[str, str]: (bucket, key)
        """
        if not s3_path.startswith("s3://"):
            raise ValueError(f"유효하지 않은 S3 경로입니다: {s3_path}")
        
        # s3:// 제거
        path_without_protocol = s3_path[5:]
        # 첫 번째 / 기준으로 버킷과 키 분리
        parts = path_without_protocol.split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""
        
        return bucket, key

    def download_file(
        self, s3_key: str, filename: Optional[str] = None, bucket: Optional[str] = None
    ) -> Tuple[bytes, str, str]:
        """
        S3에서 파일 다운로드

        Args:
            s3_key: S3 객체 키 (경로)
            filename: 다운로드할 파일명 (없으면 s3_key에서 추출)
            bucket: S3 버킷 이름 (없으면 self.s3_bucket 사용)

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
            FileNotFoundError: 파일을 찾을 수 없는 경우
            Exception: 다운로드 실패 시
        """
        try:
            if not self.s3_client:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")
            
            # 버킷 결정 (파라미터 우선, 없으면 인스턴스 변수 사용)
            target_bucket = bucket or self.s3_bucket
            if not target_bucket:
                raise ValueError("S3 버킷이 지정되지 않았습니다.")

            # S3에서 파일 다운로드
            response = self.s3_client.get_object(Bucket=target_bucket, Key=s3_key)

            # 파일 내용 읽기
            file_content = response["Body"].read()

            # Content-Type 가져오기 (없으면 기본값 사용)
            content_type = response.get("ContentType", "application/octet-stream")

            # 파일명 추출
            if not filename:
                # Content-Disposition 헤더에서 파일명 추출 시도
                content_disposition = response.get("ContentDisposition", "")
                if content_disposition:
                    # Content-Disposition: attachment; filename="example.xlsx"
                    match = re.search(
                        r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)',
                        content_disposition,
                    )
                    if match:
                        filename = match.group(1).strip('"\'')
                # Content-Disposition이 없으면 s3_key에서 추출
                if not filename:
                    filename = s3_key.split("/")[-1]
                if not filename:
                    filename = "download"

            logger.info(
                "S3 파일 다운로드 완료: s3_key=%s, filename=%s", s3_key, filename
            )
            return file_content, filename, content_type

        except Exception as exc:
            # boto3 ClientError의 NoSuchKey 예외 처리
            try:
                from botocore.exceptions import ClientError

                if isinstance(exc, ClientError) and hasattr(exc, "response"):
                    error_code = exc.response.get("Error", {}).get("Code", "")
                    if error_code == "NoSuchKey":
                        logger.error(
                            "S3 파일을 찾을 수 없습니다: s3_key=%s", s3_key
                        )
                        raise FileNotFoundError(
                            f"S3 파일을 찾을 수 없습니다: {s3_key}"
                        ) from exc
            except ImportError:
                # botocore가 없는 경우 일반 예외로 처리
                pass

            # 다른 예외는 그대로 전파
            logger.error(
                "S3 파일 다운로드 실패: s3_key=%s, error=%s", s3_key, str(exc)
            )
            raise

    def download_program_file(
        self,
        file_type: str,
        program_id: Optional[str] = None,
        db_session=None,
    ) -> Tuple[bytes, str, str]:
        """
        프로그램 파일 다운로드 (file_type + program_id 방식)

        Args:
            file_type: 파일 타입
                - "program_classification": Program 분류 체계 엑셀 파일
                - "program_logic": Program Logic 파일 (ZIP)
                - "program_comment": Program Comment 파일 (CSV)
            program_id: Program ID (필수)
            db_session: 데이터베이스 세션 (필수)

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)

        Raises:
            ValueError: 필수 파라미터가 없는 경우
            FileNotFoundError: 문서를 찾을 수 없는 경우
            Exception: 다운로드 실패 시
        """
        try:
            if not program_id:
                raise ValueError(f"{file_type}은 program_id가 필요합니다.")
            if not db_session:
                raise ValueError(f"{file_type}은 데이터베이스 세션이 필요합니다.")

            from src.database.models.document_models import Document

            # file_type을 document_type으로 매핑
            document_type_map = {
                "program_logic": "ladder_logic_zip",
                "program_classification": "template",
                "program_comment": "comment",
            }

            document_type = document_type_map.get(file_type)
            if not document_type:
                raise ValueError(f"지원하지 않는 file_type입니다: {file_type}")

            # Program ID와 document_type으로 Document 조회
            document = (
                db_session.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.document_type == document_type)
                .filter(Document.is_deleted.is_(False))
                .first()
            )

            if not document:
                raise FileNotFoundError(
                    f"문서를 찾을 수 없습니다: program_id={program_id}, "
                    f"document_type={document_type}"
                )

            # S3 경로 추출 (upload_path 우선 사용)
            s3_key = None
            s3_bucket = None
            
            # 1순위: upload_path 사용 (전체 경로가 명확함)
            if document.upload_path and document.upload_path.startswith("s3://"):
                s3_bucket, s3_key = self._parse_s3_path(document.upload_path)
                logger.debug(
                    "upload_path에서 S3 경로 추출: bucket=%s, key=%s",
                    s3_bucket,
                    s3_key,
                )
            # 2순위: file_key 사용 (fallback, 하위 호환성)
            elif document.file_key:
                s3_key = document.file_key
                s3_bucket = self.s3_bucket  # 서비스 레벨 버킷 사용
                logger.debug(
                    "file_key 사용: bucket=%s, key=%s",
                    s3_bucket,
                    s3_key,
                )
            else:
                raise ValueError(
                    f"S3 경로를 찾을 수 없습니다: program_id={program_id}, "
                    f"upload_path={document.upload_path}, file_key={document.file_key}"
                )

            filename = document.original_filename
            content_type = document.file_type

            # S3에서 파일 다운로드
            file_content, _, _ = self.download_file(s3_key, filename, bucket=s3_bucket)

            return file_content, filename, content_type

        except Exception as e:
            logger.error(
                "프로그램 파일 다운로드 실패: file_type=%s, "
                "program_id=%s, error=%s",
                file_type,
                program_id,
                str(e),
            )
            raise

    def download_file_by_document_id(
        self,
        document_id: str,
        db_session,
    ) -> Tuple[bytes, str, str]:
        """
        Document ID로 파일 다운로드

        Args:
            document_id: Document ID
            db_session: 데이터베이스 세션

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)

        Raises:
            FileNotFoundError: 문서를 찾을 수 없는 경우
            Exception: 다운로드 실패 시
        """
        try:
            from src.database.models.document_models import Document

            # Document ID로 직접 조회
            document = (
                db_session.query(Document)
                .filter(Document.document_id == document_id)
                .filter(Document.is_deleted.is_(False))
                .first()
            )

            if not document:
                raise FileNotFoundError(
                    f"문서를 찾을 수 없습니다: document_id={document_id}"
                )

            # S3 경로 추출 (upload_path 우선 사용)
            s3_key = None
            s3_bucket = None
            
            # 1순위: upload_path 사용 (전체 경로가 명확함)
            if document.upload_path and document.upload_path.startswith("s3://"):
                s3_bucket, s3_key = self._parse_s3_path(document.upload_path)
                logger.debug(
                    "upload_path에서 S3 경로 추출: bucket=%s, key=%s",
                    s3_bucket,
                    s3_key,
                )
            # 2순위: file_key 사용 (fallback, 하위 호환성)
            elif document.file_key:
                s3_key = document.file_key
                s3_bucket = self.s3_bucket  # 서비스 레벨 버킷 사용
                logger.debug(
                    "file_key 사용: bucket=%s, key=%s",
                    s3_bucket,
                    s3_key,
                )
            else:
                raise ValueError(
                    f"S3 경로를 찾을 수 없습니다: document_id={document_id}, "
                    f"upload_path={document.upload_path}, file_key={document.file_key}"
                )

            filename = document.original_filename
            content_type = document.file_type

            # S3에서 파일 다운로드
            file_content, _, _ = self.download_file(s3_key, filename, bucket=s3_bucket)

            return file_content, filename, content_type

        except Exception as e:
            logger.error(
                "Document ID로 파일 다운로드 실패: document_id=%s, error=%s",
                document_id,
                str(e),
            )
            raise

    # ==================== 삭제 기능 ====================

    async def delete_file(self, s3_key: str) -> bool:
        """
        S3에서 파일 삭제

        Args:
            s3_key: S3 객체 키 (경로)

        Returns:
            bool: 삭제 성공 여부

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=s3_key)
            logger.info("S3 파일 삭제 완료: s3_key=%s", s3_key)
            return True

        except Exception as e:
            logger.error("S3 파일 삭제 실패: s3_key=%s, error=%s", s3_key, str(e))
            return False

    async def delete_files_by_prefix(self, prefix: str) -> int:
        """
        S3에서 특정 prefix를 가진 모든 파일 삭제

        Args:
            prefix: S3 경로 prefix

        Returns:
            int: 삭제된 파일 개수

        Raises:
            ValueError: S3 클라이언트가 초기화되지 않은 경우
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            deleted_count = 0

            # S3에서 해당 prefix의 모든 객체 조회
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix)

            for page in pages:
                if "Contents" in page:
                    objects_to_delete = [
                        {"Key": obj["Key"]} for obj in page["Contents"]
                    ]

                    if objects_to_delete:
                        # 1000개씩 나누어 삭제 (S3 제한)
                        for i in range(0, len(objects_to_delete), 1000):
                            chunk = objects_to_delete[i:i + 1000]
                            self.s3_client.delete_objects(
                                Bucket=self.s3_bucket,
                                Delete={"Objects": chunk, "Quiet": True},
                            )
                            deleted_count += len(chunk)

            logger.info(
                "S3 파일 일괄 삭제 완료: prefix=%s, deleted_count=%d",
                prefix,
                deleted_count,
            )
            return deleted_count

        except Exception as e:
            logger.error(
                "S3 파일 일괄 삭제 실패: prefix=%s, error=%s", prefix, str(e)
            )
            raise

    # ==================== 유틸리티 함수 ====================

    def _guess_content_type(self, filename: str) -> str:
        """
        파일명에서 Content-Type 추론

        Args:
            filename: 파일명

        Returns:
            str: Content-Type
        """
        extension = Path(filename).suffix.lower()
        content_type_map = {
            ".json": "application/json",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            ".xls": "application/vnd.ms-excel",
            ".zip": "application/zip",
            ".pdf": "application/pdf",
        }
        return content_type_map.get(extension, "application/octet-stream")

    def is_available(self) -> bool:
        """
        S3 서비스 사용 가능 여부 확인

        Returns:
            bool: 사용 가능 여부
        """
        return self.s3_client is not None and self.s3_bucket is not None
