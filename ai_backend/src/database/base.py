# -*- coding: utf-8 -*-
"""Database module."""

import logging

# from typing import Any, Callable, Dict, ContextManager
import os

# from pathlib import Path
from contextlib import contextmanager

# import pandas as pd

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, inspect, orm, text
from sqlalchemy.ext.declarative import declarative_base

# 모델 import는 __init__.py에서 처리


__all__ = [
    "Base",
    "Database",
]

Base = declarative_base()


class Database:
    def __init__(self, db_config):
        """
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
            
            # 스키마 존재 확인 및 생성
            with self._engine.connect() as conn:
                try:
                    # PostgreSQL 9.5+ 지원: IF NOT EXISTS 사용
                    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    conn.commit()
                    logger.info(f"스키마 확인 완료: {schema}")
                except Exception as e:
                    # IF NOT EXISTS를 지원하지 않거나 이미 존재하는 경우
                    error_str = str(e)
                    if "duplicate key value violates unique constraint" in error_str and "pg_namespace_nspname_index" in error_str:
                        logger.warning(f"⚠️ 스키마가 이미 존재함 (정상 동작): {schema}")
                        conn.rollback()
                    elif "syntax error" in error_str.lower() or "unexpected" in error_str.lower():
                        # IF NOT EXISTS를 지원하지 않는 경우: 존재 여부 확인 후 생성
                        result = conn.execute(text(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema}'"))
                        schema_exists = result.fetchone() is not None
                        if not schema_exists:
                            conn.execute(text(f"CREATE SCHEMA {schema}"))
                            conn.commit()
                            logger.info(f"스키마 생성 완료: {schema}")
                        else:
                            logger.info(f"스키마 이미 존재: {schema}")
                    else:
                        raise
            
            # 스키마 설정을 위한 세션 생성
            with self._engine.connect() as conn:
                conn.execute(text(f"SET search_path TO {schema}"))
                conn.commit()
            
            # ai_backend 모델들을 import하여 Base.metadata에 등록
            # 순환 import를 피하기 위해 여기서 직접 import
            try:
                # 모든 모델 파일을 import하여 Base.metadata에 등록
                from src.database.models import program_models  # noqa: F401
                from src.database.models import template_models  # noqa: F401
                from src.database.models import plc_models  # noqa: F401
                from src.database.models import master_models  # noqa: F401
                from src.database.models import plc_history_models  # noqa: F401
                from src.database.models import knowledge_reference_models  # noqa: F401
                # user_models, chat_models 등은 원래 있던 모델들
                from src.database.models import user_models  # noqa: F401
                from src.database.models import chat_models  # noqa: F401
                from src.database.models import document_models  # noqa: F401
                from src.database.models import group_models  # noqa: F401
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
                    existing_tables = inspector.get_table_names(schema=schema)
                
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
                error_str = str(e)
                if "duplicate key value violates unique constraint" in error_str and "pg_type_typname_nsp_index" in error_str:
                    logger.warning("⚠️ PostgreSQL 타입 중복 오류 무시 (이미 존재하는 타입 - 정상 동작)")
                else:
                    raise
            
            # 최종 로그는 위에서 이미 출력됨 (생성 필요 시 또는 모두 존재 시)
        except Exception as e:
            logger.error("❌ 테이블 생성 실패: " + str(e))
            raise e

    @contextmanager
    def session(self):
        """
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