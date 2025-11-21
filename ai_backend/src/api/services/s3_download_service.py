# _*_ coding: utf-8 _*_
"""S3 파일 다운로드 서비스"""
import logging
import re
from typing import Optional, Tuple

from src.config import settings

logger = logging.getLogger(__name__)


class S3DownloadService:
    """S3 파일 다운로드 서비스"""

    def __init__(self, s3_client=None, s3_bucket: str = None):
        """
        Args:
            s3_client: S3 클라이언트 (boto3 등)
            s3_bucket: S3 버킷 이름 (없으면 settings에서 가져옴, fallback용)
        """
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket or settings.get_s3_bucket_name()

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
        """
        try:
            if not self.s3_client:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")
            
            # 버킷 결정 (파라미터 우선, 없으면 인스턴스 변수 사용)
            target_bucket = bucket or self.s3_bucket
            if not target_bucket:
                raise ValueError("S3 버킷이 지정되지 않았습니다.")

            # S3에서 파일 다운로드
            response = self.s3_client.get_object(
                Bucket=target_bucket, Key=s3_key
            )

            # 파일 내용 읽기
            file_content = response["Body"].read()

            # Content-Type 가져오기 (없으면 기본값 사용)
            content_type = response.get(
                "ContentType", "application/octet-stream"
            )

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

            logger.info("S3 파일 다운로드 완료: s3_key=%s", s3_key)
            return file_content, filename, content_type

        except Exception as exc:
            # boto3 ClientError의 NoSuchKey 예외 처리
            try:
                from botocore.exceptions import ClientError

                if isinstance(exc, ClientError):
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
                "S3 파일 다운로드 실패: s3_key=%s, error=%s",
                s3_key,
                str(exc),
            )
            raise

    def download_program_file(
        self,
        file_type: str,
        program_id: Optional[str] = None,
        db_session=None,
    ) -> Tuple[bytes, str, str]:
        """
        프로그램 파일 다운로드 (program_id 기반)

        Args:
            file_type: 파일 타입
                - "program_logic": Program Logic 파일 (program_id 필수)
                - "program_classification": Program 분류체계 (program_id 필수)
                - "program_comment": Program Comment 파일 (program_id 필수)
            program_id: Program ID (필수)
            db_session: 데이터베이스 세션 (필수)

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)
        """
        try:
            # 모든 파일 타입은 program_id와 db_session 필수
            if not program_id:
                raise ValueError(
                    f"{file_type}은 program_id가 필요합니다."
                )
            if not db_session:
                raise ValueError(
                    f"{file_type}은 데이터베이스 세션이 필요합니다."
                )

            from src.database.models.document_models import Document

            # file_type을 document_type으로 매핑
            document_type_map = {
                "program_logic": "ladder_logic_zip",
                "program_classification": "template",
                "program_comment": "comment",
            }

            document_type = document_type_map.get(file_type)
            if not document_type:
                raise ValueError(
                    f"지원하지 않는 file_type입니다: {file_type}"
                )

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
                "파일 다운로드 실패: file_type=%s, program_id=%s, error=%s",
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
        Document ID로 파일 다운로드 (더 간단하고 직접적인 방법)

        Args:
            document_id: Document ID
            db_session: 데이터베이스 세션

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)
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
                "파일 다운로드 실패: document_id=%s, error=%s",
                document_id,
                str(e),
            )
            raise

