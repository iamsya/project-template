# _*_ coding: utf-8 _*_
"""Dependency injection for FastAPI."""
import logging
from typing import Generator, List, Optional

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from src.api.services.document_service import DocumentService
from src.api.services.knowledge_status_service import KnowledgeStatusService
from src.api.services.llm_chat_service import LLMChatService
from src.api.services.program_service import ProgramService
from src.api.services.s3_service import S3Service
from src.api.services.user_service import UserService
from src.cache.redis_client import get_redis_client
from src.config import settings
from src.database.base import Database
from src.database.crud.user_crud import UserCRUD

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
        print(
            f"[DEBUG] Database connection established: {settings.database_host}:{settings.database_port}"
        )
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
    db: Session = Depends(get_db), redis_client=Depends(get_redis_client)
) -> LLMChatService:
    """LLM 채팅 서비스 의존성 주입 (Redis fallback 지원)"""
    # LLMChatService는 환경 변수에서 LLM 제공자를 자동으로 선택
    return LLMChatService(db=db, redis_client=redis_client)


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """문서 관리 서비스 의존성 주입"""
    return DocumentService(db=db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """사용자 관리 서비스 의존성 주입"""
    return UserService(db=db)


def get_program_service(
    db: Session = Depends(get_db),
) -> ProgramService:
    """프로그램 관리 서비스 의존성 주입"""
    # S3Service는 내부에서 생성
    s3_service = get_s3_service()
    return ProgramService(db=db, s3_service=s3_service)


def get_s3_service() -> S3Service:
    """S3 업로드/다운로드 통합 서비스 의존성 주입"""
    s3_bucket = settings.get_s3_bucket_name()

    # S3 클라이언트 초기화
    s3_client = None
    if s3_bucket:
        try:
            import boto3

            # S3 클라이언트 생성 파라미터
            client_kwargs = {
                "service_name": "s3",
            }

            # S3_ENDPOINT_URL이 설정되어 있으면 사용 (NCP Storage, MinIO 등 S3 호환 스토리지)
            if settings.s3_endpoint_url:
                client_kwargs["endpoint_url"] = settings.s3_endpoint_url
                logger.info("S3 Endpoint URL 사용: %s", settings.s3_endpoint_url)
            else:
                # AWS S3 사용 시에만 region_name 필요
                client_kwargs["region_name"] = settings.aws_region

            # 자격 증명 설정 (명시적으로 설정된 경우 우선 사용)
            # NCP Storage, MinIO 등은 Access Key/Secret Key를 명시적으로 설정해야 함
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
                client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
                logger.info("S3 자격 증명을 환경변수에서 사용")
            # 명시적으로 설정되지 않은 경우 boto3가 자동으로 찾음:
            # 1. 환경 변수 (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
            # 2. AWS 자격 증명 파일 (~/.aws/credentials)
            # 3. IAM 역할 (EC2, ECS, Lambda 등에서 실행 시)

            # S3 Addressing Style 설정 (NCP Storage 등 일부 S3 호환 스토리지에서 필요)
            if settings.s3_addressing_style and settings.s3_addressing_style != "auto":
                from botocore.client import Config

                if settings.s3_addressing_style == "path":
                    s3_config = Config(s3={"addressing_style": "path"})
                    client_kwargs["config"] = s3_config
                    logger.info("S3 Addressing Style: path")
                elif settings.s3_addressing_style == "virtual":
                    s3_config = Config(s3={"addressing_style": "virtual"})
                    client_kwargs["config"] = s3_config
                    logger.info("S3 Addressing Style: virtual")

            # S3 클라이언트 생성
            s3_client = boto3.client(**client_kwargs)
            logger.info("S3 서비스 클라이언트 초기화 완료: bucket=%s", s3_bucket)
        except Exception as e:
            logger.warning(
                "S3 클라이언트 초기화 실패: %s. "
                "S3 업로드/다운로드 기능이 비활성화됩니다.",
                str(e),
            )
    else:
        logger.warning(
            "S3_BUCKET_NAME 환경변수가 설정되지 않았습니다. "
            "S3 업로드/다운로드 기능이 비활성화됩니다."
        )

    return S3Service(
        s3_client=s3_client,
        s3_bucket=s3_bucket,
        s3_region=settings.aws_region,
    )


def get_knowledge_status_service(
    db: Session = Depends(get_db),
) -> KnowledgeStatusService:
    """Knowledge 상태 확인 서비스 의존성 주입"""
    return KnowledgeStatusService(db=db)


def get_user_name(
    user_id: str,
    db: Optional[Session] = None,
    default: str = "user",
) -> str:
    """
    user_id로 users 테이블에서 name 조회

    Args:
        user_id: 사용자 ID (필수, request.state.user_id에서 가져온 값)
        db: 데이터베이스 세션
        default: user_id가 없거나 사용자를 찾을 수 없을 때 반환할 기본값

    Returns:
        str: 사용자 이름 (name 컬럼 값)
    """
    try:
        if not user_id:
            logger.debug("user_id가 없습니다. 기본값 반환: %s", default)
            return default

        # db가 없으면 기본값 반환
        if not db:
            logger.debug("db 세션이 없습니다. 기본값 반환: %s", default)
            return default

        # users 테이블에서 name 조회

        user_crud = UserCRUD(db)
        user = user_crud.get_user(user_id)

        if user and user.name:
            logger.debug(
                "사용자 이름 조회 성공: user_id=%s, name=%s", user_id, user.name
            )
            return user.name

        logger.warning(
            "사용자를 찾을 수 없습니다: user_id=%s. 기본값 반환: %s",
            user_id,
            default,
        )
        return default

    except Exception as e:
        logger.error(
            "사용자 이름 조회 중 오류 발생: user_id=%s, error=%s. 기본값 반환: %s",
            user_id,
            str(e),
            default,
        )
        return default


def get_user_name_from_request(
    request: Request,
    db: Session = Depends(get_db),
    default: str = "user",
) -> str:
    """
    request.state에서 user_id를 가져와 users 테이블에서 name 조회 (JWT_ENABLED=true 시)

    Deprecated: get_user_name() 사용 권장

    Args:
        request: FastAPI Request 객체
        db: 데이터베이스 세션
        default: user_id가 없거나 사용자를 찾을 수 없을 때 반환할 기본값

    Returns:
        str: 사용자 이름 (name 컬럼 값)
    """
    return get_user_name(request=request, db=db, default=default)


def resolve_user_id(request: Request, user_id: Optional[str] = None) -> Optional[str]:
    """
    request.state.user_id와 파라미터 user_id 중 우선순위에 따라 user_id 반환

    우선순위:
    1. request.state.user_id (미들웨어에서 설정된 경우) - 최우선
    2. 파라미터 user_id (테스트용) - fallback

    Args:
        request: FastAPI Request 객체
        user_id: 파라미터로 전달된 user_id (선택사항)

    Returns:
        Optional[str]: 결정된 user_id (둘 다 없으면 None)
    """
    if hasattr(request.state, "user_id") and request.state.user_id:
        return request.state.user_id
    return user_id


def get_user_name_from_param(
    user_id: str,
    db: Session = Depends(get_db),
    default: str = "user",
) -> str:
    """
    파라미터로 받은 user_id로 users 테이블에서 name 조회 (JWT_ENABLED=false 시)

    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션
        default: 사용자를 찾을 수 없을 때 반환할 기본값

    Returns:
        str: 사용자 이름 (name 컬럼 값)
    """
    return get_user_name(user_id=user_id, db=db, default=default)


def get_user_id_dependency(
    request: Request,
) -> str:
    """
    사용자 ID를 Depends로 주입

    API 진입 시점에 자동으로 호출되어 사용자 ID를 반환합니다.
    request.state.user_id (SSO)만 사용합니다.

    Returns:
        str: 사용자 ID

    Raises:
        HTTPException: 사용자 ID가 없으면 400 에러
    """
    check_user_id = getattr(request.state, "user_id", None)
    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )
    return check_user_id


def get_accessible_process_ids_dependency(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[List[str]]:
    """
    접근 가능한 공정 ID 목록을 Depends로 주입

    API 진입 시점에 자동으로 호출되어 접근 가능한 공정 ID 목록을 반환합니다.
    request.state.user_id (SSO)만 사용합니다.

    Returns:
        Optional[List[str]]: 접근 가능한 process_id 목록
            - None: 모든 공정 접근 가능 (system_admin 또는 integrated_admin)
            - List[str]: 특정 공정만 접근 가능 (process_manager)
            - []: 접근 불가 (일반 사용자)

    Raises:
        HTTPException: 사용자 ID가 없으면 400 에러
    """
    from src.database.crud.program_crud import ProgramCRUD

    check_user_id = getattr(request.state, "user_id", None)
    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )

    program_crud = ProgramCRUD(db)
    return program_crud.get_accessible_process_ids(check_user_id)


def get_user_roles_dependency(
    request: Request,
    user_id: Optional[str] = Query(None, description="사용자 ID (테스트용)"),
    db: Session = Depends(get_db),
) -> List[str]:
    """
    사용자 역할 목록을 Depends로 주입 (User 라우터용)

    API 진입 시점에 자동으로 호출되어 사용자의 역할 목록을 반환합니다.

    Returns:
        List[str]: 역할 ID 목록 (예: ['system_admin'], ['process_manager'], [])
    """
    from src.core.permissions import get_user_roles

    check_user_id = resolve_user_id(request, user_id)
    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )

    return get_user_roles(check_user_id, db)
