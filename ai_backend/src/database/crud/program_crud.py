# _*_ coding: utf-8 _*_
"""Program CRUD operations with database."""
import logging
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.program_models import Program
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.datetime_utils import get_current_datetime

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
                create_dt=get_current_datetime(),
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
        """프로그램 조회 (is_deleted=False인 것만, 사용 중으로 인식)"""
        try:
            return (
                self.db.query(Program)
                .filter(Program.program_id == program_id)
                .filter(Program.is_deleted.is_(False))
                .first()
            )
        except Exception as e:
            logger.error(f"프로그램 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_user_programs(self, user_id: str) -> List[Program]:
        """사용자의 프로그램 목록 조회 (is_deleted=False인 것만, 사용 중으로 인식)"""
        try:
            return (
                self.db.query(Program)
                .filter(Program.create_user == user_id)
                .filter(Program.is_deleted.is_(False))
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
                program.update_dt = get_current_datetime()
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
                    program.completed_at = get_current_datetime()
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

    def get_accessible_process_ids(self, user_id: Optional[str]) -> Optional[List[str]]:
        """
        사용자가 접근 가능한 공정 ID 목록 조회
        
        여러 그룹에 속한 경우, 제일 넓은 권한이 적용됩니다:
        - 시스템 관리자 또는 통합관리자 그룹이 하나라도 있으면
          → 모든 공정 접근 가능 (None 반환)
        - 공정 관리자 그룹만 있는 경우
          → 모든 공정 관리자 그룹의 공정을 합집합으로 반환
        
        Args:
            user_id: 사용자 ID (None이면 모든 공정 접근 가능)
            
        Returns:
            Optional[List[str]]: 접근 가능한 process_id 목록
                - None: 모든 공정 접근 가능 (super 권한)
                - List[str]: 접근 가능한 process_id 목록
                - []: 접근 불가 (일반 사용자)
        
        Examples:
            # 예시 1: 시스템 관리자 그룹 1개
            user_id = "user1"
            groups = [group_system_admin]
            → None (모든 공정 접근 가능)
            
            # 예시 2: 공정 관리자 그룹 2개
            # (prc_module, prc_hwaseong) + (prc_electrode)
            user_id = "user2"
            groups = [group_process_manager_001, group_process_manager_002]
            → ['prc_module', 'prc_hwaseong', 'prc_electrode'] (합집합)
            
            # 예시 3: 시스템 관리자 + 공정 관리자 그룹
            user_id = "user3"
            groups = [group_system_admin, group_process_manager_001]
            → None (시스템 관리자 권한이 우선)
        """
        if not user_id:
            return None  # user_id가 없으면 모든 공정 접근 가능
            
        try:
            from src.database.models.permission_group_models import (
                GroupProcessPermission,
                PermissionGroup,
                UserGroupMapping,
            )
            
            # 사용자가 속한 활성 그룹 조회
            groups = (
                self.db.query(PermissionGroup)
                .join(
                    UserGroupMapping,
                    PermissionGroup.group_id == UserGroupMapping.group_id
                )
                .filter(UserGroupMapping.user_id == user_id)
                .filter(UserGroupMapping.is_active.is_(True))
                .filter(PermissionGroup.is_active.is_(True))
                .all()
            )
            
            if not groups:
                # 일반 사용자: 그룹에 속하지 않음 → 접근 불가
                return []
            
            # 1. 시스템 관리자 또는 통합 관리자: 모든 공정 접근 가능
            # 여러 그룹 중 하나라도 system_admin 또는 integrated_admin이 있으면
            # 제일 넓은 권한인 "모든 공정 접근"이 적용됨
            for group in groups:
                if group.role_id in [
                    PermissionGroup.ROLE_SYSTEM_ADMIN,
                    PermissionGroup.ROLE_INTEGRATED_ADMIN
                ]:
                    return None  # None = 모든 공정 접근 가능
            
            # 2. 공정 관리자: GROUP_PROCESSES에 지정된 공정만 접근 가능
            # 여러 공정 관리자 그룹에 속한 경우,
            # 모든 그룹의 공정을 합집합으로 반환
            accessible_process_ids = set()
            for group in groups:
                if group.role_id == PermissionGroup.ROLE_PROCESS_MANAGER:
                    process_permissions = (
                        self.db.query(GroupProcessPermission)
                        .filter(
                            GroupProcessPermission.group_id == group.group_id
                )
                .filter(GroupProcessPermission.is_active.is_(True))
                .all()
            )
                    accessible_process_ids.update(
                        [pp.process_id for pp in process_permissions]
                    )
            
            return list(accessible_process_ids) if accessible_process_ids else []
            
        except Exception as e:
            logger.error(f"접근 가능한 공정 조회 실패: {str(e)}")
            # 에러 발생 시 안전하게 모든 공정 접근 가능으로 처리
            return None

    def get_accessible_processes(self, user_id: Optional[str]) -> List:
        """
        사용자가 접근 가능한 공정 목록 조회 (드롭다운용)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            List[ProcessMaster]: 접근 가능한 공정 목록
                - 권한이 없으면 빈 리스트 반환
                - 모든 공정 접근 가능하면 모든 활성 공정 반환
                - 특정 공정만 접근 가능하면 해당 공정만 반환
        """
        try:
            from src.database.models.master_models import ProcessMaster
            
            # 접근 가능한 process_id 목록 조회
            accessible_process_ids = self.get_accessible_process_ids(user_id)
            
            if accessible_process_ids is None:
                # 모든 공정 접근 가능 (super 권한)
                processes = (
                    self.db.query(ProcessMaster)
                    .filter(ProcessMaster.is_active.is_(True))
                    .order_by(
                        ProcessMaster.process_name,
                    )
                    .all()
                )
                return processes
            elif not accessible_process_ids:
                # 접근 가능한 공정이 없음
                return []
            else:
                # 특정 공정만 접근 가능
                processes = (
                    self.db.query(ProcessMaster)
                    .filter(ProcessMaster.process_id.in_(accessible_process_ids))
                    .filter(ProcessMaster.is_active.is_(True))
                    .order_by(
                        ProcessMaster.process_name,
                    )
                    .all()
                )
                return processes
                
        except Exception as e:
            logger.error(f"접근 가능한 공정 목록 조회 실패: {str(e)}")
            # 에러 발생 시 빈 리스트 반환 (안전하게 처리)
            return []

    def get_programs(
        self,
        program_id: Optional[str] = None,
        program_name: Optional[str] = None,
        status: Optional[str] = None,
        create_user: Optional[str] = None,
        process_id: Optional[str] = None,
        user_id: Optional[str] = None,
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
            status: 상태로 필터링 (부분 일치)
            create_user: 작성자로 필터링 (부분 일치)
            process_id: 공정 ID로 필터링 (부분 일치)
            user_id: 사용자 ID (권한 기반 필터링용)
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            sort_by: 정렬 기준 (create_dt, program_id, program_name, status)
            sort_order: 정렬 순서 (asc, desc)

        Returns:
            Tuple[List[Program], int]: (프로그램 목록, 전체 개수)
        """
        try:
            # is_deleted=False인 것만 조회 (사용 중으로 인식)
            query = self.db.query(Program).filter(Program.is_deleted.is_(False))

            # 권한 기반 필터링 (user_id가 제공된 경우)
            if user_id:
                accessible_process_ids = self.get_accessible_process_ids(user_id)
                if accessible_process_ids is not None:  # None이면 모든 공정 접근 가능
                    if not accessible_process_ids:
                        # 접근 가능한 공정이 없으면 빈 결과 반환
                        return [], 0
                    query = query.filter(Program.process_id.in_(accessible_process_ids))

            # 검색 조건 (모두 부분 일치)
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
                query = query.filter(
                    Program.create_user.ilike(f"%{create_user}%")
                )
            if process_id:
                query = query.filter(
                    Program.process_id.ilike(f"%{process_id}%")
                )

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
        실제로는 is_deleted를 True로 설정 (소프트 삭제)

        Args:
            program_ids: 삭제할 프로그램 ID 리스트

        Returns:
            int: 삭제된 프로그램 개수
        """
        try:
            deleted_count = (
                self.db.query(Program)
                .filter(Program.program_id.in_(program_ids))
                .filter(Program.is_deleted.is_(False))
                .update({"is_deleted": True, "deleted_at": get_current_datetime()}, synchronize_session=False)
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
        실제로는 is_deleted를 True로 설정 (소프트 삭제)

        Args:
            program_id: 삭제할 프로그램 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            program = self.get_program(program_id)
            if program:
                program.is_deleted = True
                program.deleted_at = get_current_datetime()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"프로그램 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
