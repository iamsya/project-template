# -*- coding: utf-8 -*-
"""Database module."""

import logging
import os
import re
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, orm, text
from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# 모델 import는 __init__.py에서 처리


__all__ = [
    "Base",
    "Database",
]

Base = declarative_base()


def _safe_str(obj) -> str:
    """
    객체를 안전하게 문자열로 변환 (인코딩 오류 방지)
    
    Args:
        obj: 변환할 객체
        
    Returns:
        str: 안전하게 변환된 문자열
    """
    try:
        if isinstance(obj, bytes):
            # bytes인 경우 UTF-8로 디코딩 시도, 실패 시 errors='replace' 사용
            return obj.decode('utf-8', errors='replace')
        elif isinstance(obj, str):
            return obj
        else:
            # 일반 객체는 str()로 변환
            result = str(obj)
            # UTF-8로 인코딩 가능한지 확인
            result.encode('utf-8')
            return result
    except (UnicodeDecodeError, UnicodeEncodeError):
        # 인코딩 오류 발생 시 repr() 사용
        try:
            return repr(obj)
        except Exception:
            return f"<unable to convert {type(obj).__name__} to string>"
    except Exception:
        # 기타 오류 발생 시 타입 정보만 반환
        return f"<error converting {type(obj).__name__} to string>"


def _validate_schema_name(schema: str) -> str:
    """
    PostgreSQL 스키마 이름 검증 및 안전한 식별자로 변환
    
    Args:
        schema: 스키마 이름
        
    Returns:
        str: 검증된 스키마 이름 (따옴표로 감싼 식별자)
        
    Raises:
        ValueError: 스키마 이름이 유효하지 않은 경우
    """
    if not schema:
        raise ValueError("스키마 이름이 비어있습니다.")
    
    # PostgreSQL 식별자 규칙: 영문자, 숫자, 언더스코어, 달러 기호만 허용
    # 특수문자가 있으면 따옴표로 감싸야 함
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_$]*$', schema):
        # 안전한 식별자 (따옴표 없이 사용 가능)
        return schema
    else:
        # 특수문자나 키워드 포함 시 따옴표로 감싸기
        # SQL Injection 방지를 위해 따옴표 이스케이프
        escaped = schema.replace('"', '""')
        return f'"{escaped}"'


class Database:
    def __init__(self, db_config):
        """
        데이터베이스 연결 초기화
        
        Args:
            db_config: 데이터베이스 설정 딕셔너리
        """
        db_info = db_config['database']
        database_url = 'postgresql://{username}:{password}@{host}:{port}/{dbname}'.format(
            username=os.getenv("DATABASE__USERNAME", os.getenv("SYSTEMDB_USERNAME", db_info.get("username"))),
            password=os.getenv("DATABASE__PASSWORD", os.getenv("SYSTEMDB_PASSWORD", db_info.get("password"))),
            host=os.getenv("DATABASE__HOST", db_info.get("host")),
            port=os.getenv("DATABASE__PORT", db_info.get("port")),
            dbname=os.getenv("DATABASE__DBNAME", db_info.get("dbname")),
        )
        
        # PostgreSQL 스키마 설정
        schema = os.getenv("DATABASE_SCHEMA", "public")
        engine_kwargs = {}
        if schema:
            engine_kwargs["connect_args"] = {"options": f"-csearch_path={schema}"}
        
        logger.info(f"Database connection URL: {database_url}")
        logger.info(f"Database schema: {schema}")
        
        self._engine = create_engine(database_url, **engine_kwargs)
        self._session_factory = orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
        )

    def create_database(self, checkfirst=True):
        """
        테이블 생성
        checkfirst: True면 기존 테이블이 있으면 건너뛰고, False면 무조건 생성 시도
        """
        logger.info("create_database() 호출 시작")
        try:
            # PostgreSQL 스키마 설정
            schema = os.getenv("DATABASE_SCHEMA", "public")
            
            # 스키마 이름 검증 및 안전한 식별자로 변환
            validated_schema = _validate_schema_name(schema)
            # 검증된 스키마 이름에서 따옴표 제거 (CREATE SCHEMA에서는 필요 없음)
            schema_identifier = validated_schema.strip('"')
            
            # 스키마 존재 확인 및 생성
            with self._engine.connect() as conn:
                try:
                    # PostgreSQL 9.5+ 지원: IF NOT EXISTS 사용
                    # 스키마 이름은 검증되었으므로 안전하게 사용 가능
                    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_identifier}"'))
                    conn.commit()
                    logger.info(f"스키마 확인 완료: {schema_identifier}")
                except Exception as e:
                    # IF NOT EXISTS를 지원하지 않거나 이미 존재하는 경우
                    error_str = _safe_str(e)
                    if "duplicate key value violates unique constraint" in error_str and "pg_namespace_nspname_index" in error_str:
                        logger.warning(f"⚠️ 스키마가 이미 존재함 (정상 동작): {schema_identifier}")
                        conn.rollback()
                    elif "syntax error" in error_str.lower() or "unexpected" in error_str.lower():
                        # IF NOT EXISTS를 지원하지 않는 경우: 존재 여부 확인 후 생성
                        # 파라미터화된 쿼리 사용 (SQL Injection 방지)
                        result = conn.execute(
                            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema_name"),
                            {"schema_name": schema_identifier}
                        )
                        schema_exists = result.fetchone() is not None
                        if not schema_exists:
                            conn.execute(text(f'CREATE SCHEMA "{schema_identifier}"'))
                            conn.commit()
                            logger.info(f"스키마 생성 완료: {schema_identifier}")
                        else:
                            logger.info(f"스키마 이미 존재: {schema_identifier}")
                    else:
                        raise
            
            # 스키마 설정을 위한 세션 생성
            with self._engine.connect() as conn:
                # 검증된 스키마 이름 사용
                conn.execute(text(f'SET search_path TO "{schema_identifier}"'))
                conn.commit()
            
            # ai_backend 모델들을 import하여 Base.metadata에 등록
            # 순환 import를 피하기 위해 여기서 직접 import
            try:
                # 모든 모델 파일을 import하여 Base.metadata에 등록
                from src.database.models import program_models  # noqa: F401
                from src.database.models import template_models  # noqa: F401
                from src.database.models import plc_models  # noqa: F401
                
                # 마스터 모델 import 및 클래스 참조로 등록 보장
                from src.database.models import master_models  # noqa: F401
                from src.database.models.master_models import (
                    PlantMaster,
                    ProcessMaster,
                    LineMaster,
                    DropdownMaster,
                )
                # 클래스를 참조하여 Base.metadata에 등록 보장
                _ = PlantMaster
                _ = ProcessMaster
                _ = LineMaster
                _ = DropdownMaster
                
                from src.database.models import knowledge_reference_models  # noqa: F401
                # user_models, chat_models 등은 원래 있던 모델들
                from src.database.models import user_models  # noqa: F401
                from src.database.models import chat_models  # noqa: F401
                from src.database.models import document_models  # noqa: F401
                from src.database.models import permission_group_models  # noqa: F401
                logger.debug("ai_backend 모델들 import 완료")
            except ImportError as e:
                logger.warning(
                    "ai_backend 모델 import 실패 "
                    "(일부 모델 누락 가능): %s",
                    e,
                )
            
            # shared_core 모델들을 import하여 metadata에 포함
            from shared_core.models import Base as SharedBase
            
            # 두 Base의 metadata를 합쳐서 한 번에 생성
            # 이렇게 하면 Foreign Key 의존성 문제를 해결할 수 있음
            # (Document가 PROGRAMS를 참조하므로 PROGRAMS가 먼저 생성되어야 함)
            try:
                # 두 metadata를 합쳐서 생성
                # SQLAlchemy는 자동으로 의존성 순서를 파악하여 올바른 순서로 테이블 생성
                # SharedBase의 모든 테이블을 Base metadata에 추가
                for table_name, table in SharedBase.metadata.tables.items():
                    # 테이블이 이미 Base에 있으면 건너뛰기
                    if table_name not in Base.metadata.tables:
                        # 테이블을 복사하여 Base metadata에 추가
                        table.tometadata(Base.metadata)
                
                # 합쳐진 metadata로 한 번에 생성
                total_tables = len(Base.metadata.tables)
                table_names = list(Base.metadata.tables.keys())
                
                # 이미 존재하는 테이블 확인 (checkfirst=True인 경우)
                existing_tables = []
                if checkfirst:
                    inspector = inspect(self._engine)
                    # 스키마 이름에서 따옴표 제거 (inspector는 원본 스키마 이름 사용)
                    existing_tables = inspector.get_table_names(schema=schema_identifier)
                
                # 생성이 필요한 테이블만 필터링
                tables_to_create = [
                    name for name in table_names if name not in existing_tables
                ]
                
                if tables_to_create:
                    logger.info(
                        "테이블 생성 시작: 총 %d개 테이블 중 %d개 생성 필요",
                        total_tables,
                        len(tables_to_create),
                    )
                    logger.debug(
                        "생성할 테이블 목록: %s",
                        ", ".join(tables_to_create),
                    )
                    Base.metadata.create_all(
                        bind=self._engine, checkfirst=checkfirst
                    )
                    logger.info(
                        "테이블 생성 완료: %d개 테이블 생성됨",
                        len(tables_to_create),
                    )
                else:
                    logger.info(
                        "모든 테이블이 이미 존재합니다: 총 %d개 테이블",
                        total_tables,
                    )
                    logger.debug(
                        "기존 테이블 목록: %s",
                        ", ".join(existing_tables),
                    )
            except Exception as e:
                # PostgreSQL 타입 중복 오류는 무시 (이미 존재하는 타입)
                # 이는 이전 테이블 생성 실패 시 타입만 남아있는 경우 발생할 수 있음
                error_str = _safe_str(e)
                if "duplicate key value violates unique constraint" in error_str and "pg_type_typname_nsp_index" in error_str:
                    logger.warning("⚠️ PostgreSQL 타입 중복 오류 무시 (이미 존재하는 타입 - 정상 동작)")
                else:
                    raise
            
            # 최종 로그는 위에서 이미 출력됨 (생성 필요 시 또는 모두 존재 시)
        except Exception as e:
            error_msg = _safe_str(e)
            logger.error("❌ 테이블 생성 실패: %s", error_msg)
            raise

    @contextmanager
    def session(self):
        """
        데이터베이스 세션 컨텍스트 매니저
        
        사용 예시:
            with db.session() as session:
                # 세션 사용
                result = session.query(Model).all()
                session.commit()
        """
        session = self._session_factory()
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """데이터베이스 연결 종료"""
        if hasattr(self, '_session_factory'):
            self._session_factory.close_all()
        if hasattr(self, '_engine'):
            self._engine.dispose()
