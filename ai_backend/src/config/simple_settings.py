# _*_ coding: utf-8 _*_
"""Simple Pydantic Settings implementation."""
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """통합 설정 클래스 - Pydantic Settings 방식"""

    # Application Configuration
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    app_locale: str = Field(default="en", env="APP_LOCALE")
    app_log_level: str = Field(default="info", env="APP_LOG_LEVEL")
    app_debug: bool = Field(default=False, env="APP_DEBUG")
    # FastAPI root_path 설정
    # - 리버스 프록시 환경에서 사용 (Nginx, API Gateway 등)
    # - 빈 문자열: 직접 접근 (로컬 개발, 단순 배포)
    # - "/api": API Gateway 뒤에서 실행 시
    # - "/v1": 버전별 API 경로가 있는 경우
    # - "/ai-backend": Kubernetes Ingress path가 있는 경우
    # 개발: "" (직접 접근, 라우터에서 /v1 사용)
    # 프로덕션: "" 또는 "/api" (인프라에 따라)
    app_root_path: str = Field(default="", env="APP_ROOT_PATH")

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Field(default=8000, env="SERVER_PORT")
    server_debug: bool = Field(default=False, env="SERVER_DEBUG")
    server_reload: bool = Field(default=False, env="SERVER_RELOAD")
    server_log_level: str = Field(default="info", env="SERVER_LOG_LEVEL")

    # CORS Configuration
    cors_origins: str = Field(
        default="http://localhost:8000,file://", env="CORS_ORIGINS"
    )

    # JWT/SSO Configuration
    # ==========================================
    # JWT/SSO 사용 여부
    # - True: JWT/SSO 사용 (request.state.user_id 사용)
    # - False: JWT/SSO 미사용 (파라미터 user_id 사용)
    # - 환경변수: JWT_ENABLED
    jwt_enabled: bool = Field(
        default=False,
        env="JWT_ENABLED",
        description="JWT/SSO 사용 여부 (true면 SSO 사용, false면 파라미터 user_id 사용)",
    )

    # Logging Configuration
    # ==========================================
    # 로그 파일 저장 여부
    # - True: 로그를 파일에 저장 (온프레미스, 특별한 경우)
    # - False: stdout으로만 출력 (Kubernetes 권장)
    # 개발: True (디버깅 편의)
    # 프로덕션: False (Kubernetes 로그 수집 활용)
    log_to_file: bool = Field(default=False, env="LOG_TO_FILE")

    # 로그 파일 저장 디렉토리
    # - 기본값: ./logs (로컬 개발 친화적)
    # - 개발 환경: ./logs (프로젝트 내부, gitignore 권장)
    # - Kubernetes: /var/log/ai-backend (볼륨 마운트 필요)
    # - 온프레미스: /var/log/ai-backend (표준 위치)
    log_dir: str = Field(default="./logs", env="LOG_DIR")

    # 로그 파일명
    # - 기본: app.log
    # - 로테이션 시: app.log.2025-09-16 형태로 자동 변경
    log_file: str = Field(default="app.log", env="LOG_FILE")

    # 로그 로테이션 방식
    # - daily: 매일 자정에 로테이션 (권장)
    # - weekly: 매주 월요일에 로테이션
    # - monthly: 매월 1일에 로테이션
    # - size: 파일 크기 기반 로테이션 (10MB)
    # 개발: daily (로그 분석 편의)
    # 프로덕션: daily (표준 관례)
    log_rotation: str = Field(default="daily", env="LOG_ROTATION")

    # 로그 보관 기간 (일)
    # - 30일: 일반적인 보관 기간
    # - 7일: 개발 환경 (디스크 절약)
    # - 90일: 감사 로그가 필요한 경우
    # 개발: 7 (디스크 절약)
    # 프로덕션: 30 (표준)
    log_retention_days: int = Field(default=30, env="LOG_RETENTION_DAYS")

    # Database Configuration
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_name: str = Field(default="chat_db", env="DATABASE_NAME")
    database_username: str = Field(default="postgres", env="DATABASE_USERNAME")
    database_password: str = Field(default="password", env="DATABASE_PASSWORD")
    database_schema: str = Field(default="public", env="DATABASE_SCHEMA")
    # database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    # database_echo_pool: bool = Field(default=False, env="DATABASE_ECHO_POOL")
    # database_case_sensitive: bool = Field(default=False, env="DATABASE_CASE_SENSITIVE")
    # database_encoding: str = Field(default="utf-8", env="DATABASE_ENCODING")
    # database_isolation_level: str = Field(default="READ_COMMITTED", env="DATABASE_ISOLATION_LEVEL")
    # database_pool_reset_on_return: str = Field(default="rollback", env="DATABASE_POOL_RESET_ON_RETURN")
    # database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")
    # database_pool_pre_ping: bool = Field(default=True, env="DATABASE_POOL_PRE_PING")
    # database_pool_recycle: int = Field(default=3600, env="DATABASE_POOL_RECYCLE")
    # database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    # database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    # database_implicit_returning: bool = Field(default=True, env="DATABASE_IMPLICIT_RETURNING")
    # database_hide_parameters: bool = Field(default=True, env="DATABASE_HIDE_PARAMETERS")

    # LLM Provider Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")

    # OpenAI Configuration
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")  # 기본값 추가
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")
    openai_base_url: str = Field(default="openai_base_url", env="OPENAI_BASE_URL")

    # Azure OpenAI Configuration
    azure_openai_api_key: str = Field(default="", env="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", env="AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment_name: str = Field(
        default="", env="AZURE_OPENAI_DEPLOYMENT_NAME"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview", env="AZURE_OPENAI_API_VERSION"
    )
    azure_openai_max_tokens: int = Field(default=1000, env="AZURE_OPENAI_MAX_TOKENS")
    azure_openai_temperature: float = Field(default=0.7, env="AZURE_OPENAI_TEMPERATURE")

    # External API Configuration
    external_api_url: str = Field(default="", env="EXTERNAL_API_URL")
    external_api_authorization: str = Field(
        default="", env="EXTERNAL_API_AUTHORIZATION"
    )
    external_api_max_tokens: int = Field(default=1000, env="EXTERNAL_API_MAX_TOKENS")
    external_api_temperature: float = Field(default=0.7, env="EXTERNAL_API_TEMPERATURE")

    # Knowledge API Configuration
    knowledge_api_endpoint: str = Field(
        default="http://0.0.0.0:8000",
        env="KNOWLEDGE_API_ENDPOINT",
        description="Knowledge Base API 엔드포인트",
    )
    knowledge_api_version: str = Field(
        default="v1", env="KNOWLEDGE_API_VERSION", description="Knowledge Base API 버전"
    )

    # External API OpenAI Configuration (for title generation)
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=50, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # Cache Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl_chat_messages: int = Field(
        default=1800, env="CACHE_TTL_CHAT_MESSAGES"
    )  # 30분
    cache_ttl_user_chats: int = Field(default=600, env="CACHE_TTL_USER_CHATS")  # 10분

    # Redis Configuration (캐시가 활성화된 경우에만 사용)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")

    # File Upload Configuration
    # ==========================================
    # 파일 업로드 기본 경로
    # - 로컬 개발: ./uploads (프로젝트 내부, gitignore 권장)
    # - Kubernetes: /app/uploads (PVC 마운트 경로)
    # - 온프레미스: /var/uploads (표준 위치)
    upload_base_path: str = Field(default="./uploads", env="UPLOAD_BASE_PATH")

    # Storage Configuration
    # ==========================================
    # 파일 저장소 타입
    # - local: 로컬 파일시스템 (개발 환경)
    # - s3: AWS S3 (프로덕션 환경)
    # - gcs: Google Cloud Storage (프로덕션 환경)
    # - azure: Azure Blob Storage (프로덕션 환경)
    storage_type: str = Field(default="local", env="STORAGE_TYPE")

    # S3 Configuration
    # ==========================================
    # S3 버킷 이름
    # - 환경변수: S3_BUCKET_NAME
    # - 개발: 로컬 개발 시 비워둘 수 있음 (S3 기능 비활성화)
    # - 프로덕션: 실제 S3 버킷 이름
    s3_bucket_name: str = Field(default="", env="S3_BUCKET_NAME")
    aws_s3_bucket: str = Field(
        default="", env="AWS_S3_BUCKET"
    )  # 사용하지 않음 (호환성 유지)

    # AWS 리전
    # - 기본값: ap-northeast-2 (서울)
    # - 환경변수: AWS_REGION
    aws_region: str = Field(default="ap-northeast-2", env="AWS_REGION")

    # S3 Endpoint URL (선택사항)
    # - AWS S3 사용 시: 비워두면 region_name 기반으로 자동 결정
    # - NCP Storage, MinIO 등 S3 호환 스토리지 사용 시: endpoint URL 지정
    #   예: https://kr.object.ncloudstorage.com (NCP Storage)
    #   예: http://minio:9000 (MinIO)
    # - 환경변수: S3_ENDPOINT_URL
    s3_endpoint_url: str = Field(default="", env="S3_ENDPOINT_URL")

    # S3 Addressing Style (선택사항)
    # - "auto": boto3가 자동 결정 (기본값)
    # - "path": path-style addressing 사용 (예: https://endpoint.com/bucket/key)
    # - "virtual": virtual-hosted-style 사용 (예: https://bucket.endpoint.com/key)
    # - NCP Storage 등 일부 S3 호환 스토리지는 path-style을 요구할 수 있음
    # - 환경변수: S3_ADDRESSING_STYLE
    s3_addressing_style: str = Field(default="auto", env="S3_ADDRESSING_STYLE")

    # AWS/S3 자격 증명 (선택사항)
    # - NCP Storage, MinIO 등 S3 호환 스토리지 사용 시: 명시적으로 설정 필요
    # - AWS S3 사용 시: 명시적으로 설정하거나 자동으로 찾음
    #   자동 찾기 순서:
    #   1. 환경 변수 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    #   2. AWS 자격 증명 파일 (~/.aws/credentials)
    #   3. IAM 역할 (EC2, ECS, Lambda 등)
    # - 환경변수: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    aws_access_key_id: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")

    # S3 프로그램 파일 경로 prefix
    # - 기본값: programs/
    # - 환경변수: S3_PROGRAM_PREFIX
    s3_program_prefix: str = Field(default="programs/", env="S3_PROGRAM_PREFIX")

    # 파일 업로드 최대 크기 (바이트)
    # - 기본값: 50MB (52428800 bytes)
    # - 개발: 50MB (테스트 편의)
    # - 프로덕션: 50MB (표준)
    upload_max_size: int = Field(default=52428800, env="UPLOAD_MAX_SIZE")  # 50MB

    # 허용된 파일 확장자 (쉼표로 구분)
    # - 기본값: 일반적인 문서 및 이미지 형식
    # - 보안: 실행 가능한 파일 제외
    upload_allowed_types: str = Field(
        default="pdf,txt,doc,docx,jpg,jpeg,png,gif,xls,xlsx", env="UPLOAD_ALLOWED_TYPES"
    )

    # 로깅 상세 설정
    # ==========================================
    # 에러 로그에 스택 트레이스 포함 여부
    # - True: 자세한 스택 트레이스 포함 (개발/디버깅)
    # - False: 간단한 에러 메시지만 (프로덕션)
    log_include_exc_info: bool = Field(default=True, env="LOG_INCLUDE_EXC_INFO")

    def get_cors_origins(self) -> List[str]:
        """CORS origins를 리스트로 반환"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"  # 로컬 개발용 (파일이 없어도 에러 없음)
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # 추가 필드 무시

    # Database URL property
    @property
    def database_url(self) -> str:
        """데이터베이스 URL 생성"""
        if self.database_host == "sqlite":
            return f"sqlite:///{self.database_name}.db"
        return f"postgresql://{self.database_username}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    # OpenAI masked key
    def get_openai_masked_key(self) -> str:
        """마스킹된 API 키 반환"""
        if not self.openai_api_key:
            return "Not set"
        return f"{self.openai_api_key[:8]}...{self.openai_api_key[-4:]}"

    # Cache methods
    def is_cache_enabled(self) -> bool:
        """캐시가 활성화되어 있는지 확인"""
        return self.cache_enabled

    def get_cache_ttl(self, cache_type: str) -> int:
        """캐시 타입별 TTL 반환"""
        ttl_map = {
            "chat_messages": self.cache_ttl_chat_messages,
            "user_chats": self.cache_ttl_user_chats,
        }
        return ttl_map.get(cache_type, 300)  # 기본 5분

    def get_upload_allowed_types(self) -> List[str]:
        """허용된 파일 확장자 리스트 반환"""
        return [ext.strip().lower() for ext in self.upload_allowed_types.split(",")]

    def get_upload_max_size_mb(self) -> float:
        """업로드 최대 크기를 MB 단위로 반환"""
        return self.upload_max_size / (1024 * 1024)

    def get_s3_bucket_name(self) -> str:
        """S3 버킷 이름 반환 (S3_BUCKET_NAME 환경변수 사용)"""
        return self.s3_bucket_name

    # Database config dict
    def get_database_config(self) -> dict:
        """데이터베이스 설정 반환"""
        return {
            "database": {
                "username": self.database_username,
                "password": self.database_password,
                "host": self.database_host,
                "port": self.database_port,
                "dbname": self.database_name,
            }
        }

    # Uvicorn config
    def get_uvicorn_config(self) -> dict:
        """uvicorn 설정 반환"""
        return {
            "host": self.server_host,
            "port": self.server_port,
            "reload": self.server_reload,
            "log_level": self.server_log_level,
        }

    def validate_settings(self):
        """설정 유효성 검사"""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
        elif self.llm_provider == "azure_openai":
            if not self.azure_openai_api_key:
                raise ValueError(
                    "AZURE_OPENAI_API_KEY is required when using Azure OpenAI provider"
                )
            if not self.azure_openai_endpoint:
                raise ValueError(
                    "AZURE_OPENAI_ENDPOINT is required when using Azure OpenAI provider"
                )
            if not self.azure_openai_deployment_name:
                raise ValueError(
                    "AZURE_OPENAI_DEPLOYMENT_NAME is required when using Azure OpenAI provider"
                )
        elif self.llm_provider == "external_api":
            if not self.external_api_url:
                raise ValueError(
                    "EXTERNAL_API_URL is required when using External API provider"
                )
            if not self.external_api_authorization:
                raise ValueError(
                    "EXTERNAL_API_AUTHORIZATION is required when using External API provider"
                )


# 전역 설정 인스턴스
settings = Settings()
