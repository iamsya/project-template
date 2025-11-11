# _*_ coding: utf-8 _*_
"""Dependency injection for FastAPI."""
import logging
from typing import Generator
from fastapi import Depends
from sqlalchemy.orm import Session
from src.api.services.llm_chat_service import LLMChatService
from src.api.services.program_service import ProgramService
from src.api.services.document_service import DocumentService
from src.api.services.user_service import UserService
from src.api.services.group_service import GroupService
from src.api.services.s3_download_service import S3DownloadService
from src.api.services.knowledge_status_service import KnowledgeStatusService
from src.database.base import Database
from src.config import settings
from src.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# 전역 인스턴스들 (싱글톤)
_db_instance = None
_redis_instance = None


def get_database() -> Database:
    """데이터베이스 의존성 주입 (싱글톤 패턴)"""
    global _db_instance
    
    if _db_instance is not None:
        logger.debug("Returning existing database instance")
        return _db_instance
    
    logger.info("Creating new database instance")
    
    # 설정 유효성 검사 (Pydantic Settings는 자동으로 검증됨)
    
    # DB 설정
    try:
        db_config = settings.get_database_config()
        _db_instance = Database(db_config)
        _db_instance.create_database()
        print(f"[DEBUG] Database connection established: {settings.database_host}:{settings.database_port}")
        return _db_instance
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        raise ValueError(f"Database connection is required but failed: {e}")


def get_db() -> Generator[Session, None, None]:
    """데이터베이스 세션 의존성 주입 (요청별 세션)"""
    db = get_database()
    session = db._session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_redis_client():
    """Redis 클라이언트 의존성 주입 (싱글톤 패턴)"""
    global _redis_instance
    
    # 캐시가 비활성화된 경우 None 반환
    if not settings.is_cache_enabled():
        print("[DEBUG] Cache is disabled, returning None for Redis client")
        return None
    
    if _redis_instance is not None:
        return _redis_instance
    
    try:
        from src.cache.redis_client import RedisClient
        _redis_instance = RedisClient()
        if _redis_instance.ping():
            print("[DEBUG] Redis connection established")
            return _redis_instance
        else:
            print("[WARNING] Redis connection failed, returning None")
            _redis_instance = None
            return None
    except Exception as e:
        print(f"[WARNING] Redis connection failed: {e}, returning None")
        _redis_instance = None
        return None


def get_llm_chat_service(
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis_client)
) -> LLMChatService:
    """LLM 채팅 서비스 의존성 주입 (Redis fallback 지원)"""
    # LLMChatService는 환경 변수에서 LLM 제공자를 자동으로 선택
    return LLMChatService(
        db=db,
        redis_client=redis_client
    )


def get_document_service(
    db: Session = Depends(get_db)
) -> DocumentService:
    """문서 관리 서비스 의존성 주입"""
    return DocumentService(db=db)


def get_user_service(
    db: Session = Depends(get_db)
) -> UserService:
    """사용자 관리 서비스 의존성 주입"""
    return UserService(db=db)


def get_group_service(
    db: Session = Depends(get_db)
) -> GroupService:
    """그룹 관리 서비스 의존성 주입"""
    return GroupService(db=db)

def get_program_service(db: Session = Depends(get_db)) -> ProgramService:
    """프로그램 관리 서비스 의존성 주입"""
    return ProgramService(db=db)


def get_s3_download_service() -> S3DownloadService:
    """S3 다운로드 서비스 의존성 주입"""
    import os

    # S3 버킷 이름 (환경변수에서 가져오기)
    s3_bucket = os.getenv("S3_BUCKET_NAME", os.getenv("AWS_S3_BUCKET"))

    # S3 클라이언트 초기화
    s3_client = None
    if s3_bucket:
        try:
            import boto3

            # AWS 자격 증명은 다음 순서로 자동으로 찾습니다:
            # 1. 환경 변수 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # 2. AWS 자격 증명 파일 (~/.aws/credentials)
            # 3. IAM 역할 (EC2, ECS, Lambda 등에서 실행 시)
            s3_client = boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION", "ap-northeast-2"),
            )
            logger.info("S3 클라이언트 초기화 완료: bucket=%s", s3_bucket)
        except Exception as e:
            logger.warning(
                "S3 클라이언트 초기화 실패: %s. "
                "S3 다운로드 기능이 비활성화됩니다.",
                str(e),
            )
    else:
        logger.warning(
            "S3_BUCKET_NAME 환경변수가 설정되지 않았습니다. "
            "S3 다운로드 기능이 비활성화됩니다."
        )

    return S3DownloadService(s3_client=s3_client, s3_bucket=s3_bucket)


def get_knowledge_status_service(
    db: Session = Depends(get_db),
) -> KnowledgeStatusService:
    """Knowledge 상태 확인 서비스 의존성 주입"""
    return KnowledgeStatusService(db=db)
