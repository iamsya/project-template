# _*_ coding: utf-8 _*_
"""Program CRUD operations with database."""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.program_models import Program
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class ProgramCRUD:
    """Program 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_program(
        self,
        program_id: str,
        program_name: str,
        create_user: str,
        description: Optional[str] = None,
        status: str = Program.STATUS_PREPARING,
        is_used: bool = True,
        **kwargs,
    ) -> Program:
        """프로그램 생성"""
        try:
            program = Program(
                program_id=program_id,
                program_name=program_name,
                create_user=create_user,
                description=description,
                status=status,
                is_used=is_used,
                **kwargs,
            )
            self.db.add(program)
            self.db.commit()
            self.db.refresh(program)
            return program
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_program(self, program_id: str) -> Optional[Program]:
        """프로그램 조회"""
        try:
            return (
                self.db.query(Program)
                .filter(Program.program_id == program_id)
                .filter(Program.is_used.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"프로그램 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_user_programs(self, user_id: str) -> List[Program]:
        """사용자의 프로그램 목록 조회"""
        try:
            return (
                self.db.query(Program)
                .filter(Program.create_user == user_id)
                .filter(Program.is_used.is_(True))
                .order_by(desc(Program.create_dt))
                .all()
            )
        except Exception as e:
            logger.error(f"사용자 프로그램 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program(
        self, program_id: str, update_user: Optional[str] = None, **kwargs
    ) -> bool:
        """프로그램 정보 업데이트"""
        try:
            program = self.get_program(program_id)
            if program:
                for key, value in kwargs.items():
                    if hasattr(program, key):
                        setattr(program, key, value)
                # 수정 정보 업데이트
                program.update_dt = datetime.now()
                if update_user:
                    program.update_user = update_user
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_s3_paths(
        self, program_id: str, s3_paths: Dict[str, str]
    ) -> bool:
        """프로그램 S3 경로 업데이트 (metadata_json에 저장)"""
        try:
            program = self.get_program(program_id)
            if program:
                current_metadata = program.metadata_json or {}
                current_metadata["s3_paths"] = s3_paths
                return self.update_program(
                    program_id=program_id, metadata_json=current_metadata
                )
            return False
        except Exception as e:
            logger.error(f"S3 경로 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_vector_info(
        self,
        program_id: str,
        vector_indexed: bool = True,
        vector_collection_name: Optional[str] = None,
    ) -> bool:
        """프로그램 벡터 정보 업데이트 (metadata_json에 저장)"""
        try:
            program = self.get_program(program_id)
            if program:
                current_metadata = program.metadata_json or {}
                current_metadata["vector_indexed"] = vector_indexed
                if vector_collection_name:
                    current_metadata["vector_collection_name"] = (
                        vector_collection_name
                    )
                return self.update_program(
                    program_id=program_id, metadata_json=current_metadata
                )
            return False
        except Exception as e:
            logger.error(f"프로그램 벡터 정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_program_status(
        self,
        program_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> bool:
        """프로그램 상태 업데이트"""
        try:
            program = self.get_program(program_id)
            if program:
                program.status = status
                if status == Program.STATUS_COMPLETED:
                    program.completed_at = datetime.now()
                    program.error_message = None
                elif error_message:
                    program.error_message = error_message
                elif status != Program.STATUS_FAILED:
                    program.error_message = None
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 상태 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_programs(
        self,
        program_id: Optional[str] = None,
        program_name: Optional[str] = None,
        status: Optional[str] = None,
        create_user: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "create_dt",
        sort_order: str = "desc",
    ) -> Tuple[List[Program], int]:
        """
        프로그램 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

        Args:
            program_id: PGM ID로 검색 (부분 일치)
            program_name: 제목으로 검색 (부분 일치)
            status: 상태로 필터링
            create_user: 작성자로 필터링
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            sort_by: 정렬 기준 (create_dt, program_id, program_name, status)
            sort_order: 정렬 순서 (asc, desc)

        Returns:
            Tuple[List[Program], int]: (프로그램 목록, 전체 개수)
        """
        try:
            query = self.db.query(Program).filter(Program.is_used.is_(True))

            # 검색 조건
            if program_id:
                query = query.filter(
                    Program.program_id.ilike(f"%{program_id}%")
                )
            if program_name:
                query = query.filter(
                    Program.program_name.ilike(f"%{program_name}%")
                )
            if status:
                query = query.filter(Program.status == status)
            if create_user:
                query = query.filter(Program.create_user == create_user)

            # 전체 개수 조회
            total_count = query.count()

            # 정렬
            sort_column = getattr(Program, sort_by, Program.create_dt)
            if sort_order.lower() == "asc":
                query = query.order_by(sort_column)
            else:
                query = query.order_by(desc(sort_column))

            # 페이지네이션
            offset = (page - 1) * page_size
            programs = query.offset(offset).limit(page_size).all()

            return programs, total_count
        except Exception as e:
            logger.error(f"프로그램 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_programs(self, program_ids: List[str]) -> int:
        """
        프로그램 삭제 (여러 개 일괄 삭제)
        실제로는 is_used를 False로 설정 (소프트 삭제)

        Args:
            program_ids: 삭제할 프로그램 ID 리스트

        Returns:
            int: 삭제된 프로그램 개수
        """
        try:
            deleted_count = (
                self.db.query(Program)
                .filter(Program.program_id.in_(program_ids))
                .filter(Program.is_used.is_(True))
                .update({"is_used": False}, synchronize_session=False)
            )
            self.db.commit()
            return deleted_count
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_program(self, program_id: str) -> bool:
        """
        프로그램 삭제 (단일)
        실제로는 is_used를 False로 설정 (소프트 삭제)

        Args:
            program_id: 삭제할 프로그램 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            program = self.get_program(program_id)
            if program:
                program.is_used = False
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
