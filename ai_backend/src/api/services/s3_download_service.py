# _*_ coding: utf-8 _*_
"""S3 파일 다운로드 서비스"""
import logging
import re
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class S3DownloadService:
    """S3 파일 다운로드 서비스"""

    def __init__(self, s3_client=None, s3_bucket: str = None):
        """
        Args:
            s3_client: S3 클라이언트 (boto3 등)
            s3_bucket: S3 버킷 이름
        """
        self.s3_client = s3_client
        self.s3_bucket = s3_bucket

    def download_file(
        self, s3_key: str, filename: Optional[str] = None
    ) -> Tuple[bytes, str, str]:
        """
        S3에서 파일 다운로드

        Args:
            s3_key: S3 객체 키 (경로)
            filename: 다운로드할 파일명 (없으면 s3_key에서 추출)

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)
        """
        try:
            if not self.s3_client or not self.s3_bucket:
                raise ValueError("S3 클라이언트가 초기화되지 않았습니다.")

            # S3에서 파일 다운로드
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket, Key=s3_key
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
        범용 파일 다운로드 (정적 템플릿 또는 Program 파일)

        Args:
            file_type: 파일 타입
                - "template": 정적 템플릿 (program_template)
                - "logic_file": 로직 파일 (program_id 필수)
                - "logic_classification": Logic 분류체계 (program_id 필수)
                - "plc_ladder_comment": PLC Ladder Comment (program_id 필수)
            program_id: Program ID (동적 파일인 경우 필수)
            db_session: 데이터베이스 세션 (동적 파일인 경우 필수)

        Returns:
            Tuple[bytes, str, str]: (파일 내용, 파일명, Content-Type)
        """
        try:
            # 정적 템플릿인 경우
            if file_type == "template":
                s3_key = "templates/program_template.xlsx"
                filename = "program_template.xlsx"
                return self.download_file(s3_key, filename)

            # 동적 파일인 경우 program_id와 db_session 필수
            if not program_id:
                raise ValueError(
                    f"{file_type}은 program_id가 필요합니다."
                )
            if not db_session:
                raise ValueError(
                    f"{file_type}은 데이터베이스 세션이 필요합니다."
                )

            from shared_core.models import Document

            # file_type을 program_file_type으로 매핑
            program_file_type_map = {
                "logic_file": "ladder_logic",
                "logic_classification": "template",
                "plc_ladder_comment": "comment",
            }

            program_file_type = program_file_type_map.get(file_type)
            if not program_file_type:
                raise ValueError(
                    f"지원하지 않는 file_type입니다: {file_type}"
                )

            # Program ID와 program_file_type으로 Document 조회
            document = (
                db_session.query(Document)
                .filter(Document.program_id == program_id)
                .filter(Document.program_file_type == program_file_type)
                .filter(Document.is_deleted.is_(False))
                .first()
            )

            if not document:
                raise FileNotFoundError(
                    f"문서를 찾을 수 없습니다: program_id={program_id}, "
                    f"program_file_type={program_file_type}"
                )

            # S3 키 사용 (file_key 또는 upload_path에서 추출)
            s3_key = document.file_key
            if not s3_key:
                # upload_path가 S3 경로인 경우
                if document.upload_path.startswith("s3://"):
                    s3_key = document.upload_path.replace(
                        f"s3://{self.s3_bucket}/", ""
                    )
                else:
                    raise ValueError(
                        f"S3 경로를 찾을 수 없습니다: program_id={program_id}"
                    )

            filename = document.original_filename
            content_type = document.file_type

            # S3에서 파일 다운로드
            file_content, _, _ = self.download_file(s3_key, filename)

            return file_content, filename, content_type

        except Exception as e:
            logger.error(
                "파일 다운로드 실패: file_type=%s, program_id=%s, error=%s",
                file_type,
                program_id,
                str(e),
            )
            raise

