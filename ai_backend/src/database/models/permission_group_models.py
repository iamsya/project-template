# _*_ coding: utf-8 _*_
"""
권한 그룹 모델 정의
사용자가 화면에서 직접 권한 그룹을 생성하고, 사용자와 매핑
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import false, true

from src.database.base import Base


class RoleMaster(Base):
    """
    Role 마스터 테이블
    
    - Role 정보를 관리하는 마스터 테이블
    - 시스템 관리자, 통합관리자, 공정 관리자 정보 저장
    """
    
    __tablename__ = "ROLE_MASTER"
    
    # Primary Key
    role_id = Column(
        "ROLE_ID",
        String(50),
        primary_key=True,
        comment=(
            "Role ID (PK) - "
            "system_admin, integrated_admin, process_manager"
        )
    )
    
    # Role 정보
    role_name = Column(
        "ROLE_NAME",
        String(100),
        nullable=False,
        comment="Role 한글 이름 (예: 시스템 관리자, 통합관리자, 공정 관리자)"
    )
    description = Column(
        "DESCRIPTION",
        Text,
        nullable=True,
        comment="Role 설명"
    )
    display_order = Column(
        "DISPLAY_ORDER",
        Integer,
        nullable=False,
        server_default="0",
        comment="화면 표시 순서"
    )
    
    # 활성화 여부
    is_active = Column(
        "IS_ACTIVE",
        Boolean,
        nullable=False,
        server_default=true(),
        comment="활성화 여부"
    )
    
    # 시간 정보
    create_dt = Column(
        "CREATE_DT",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="생성 일시"
    )
    create_user = Column(
        "CREATE_USER",
        String(50),
        nullable=False,
        comment="생성자"
    )
    update_dt = Column(
        "UPDATE_DT",
        DateTime,
        nullable=True,
        onupdate=func.now(),
        comment="수정 일시"
    )
    update_user = Column(
        "UPDATE_USER",
        String(50),
        nullable=True,
        comment="수정자"
    )
    
    # 인덱스 정의
    __table_args__ = (
        # is_active + display_order 복합 인덱스 (활성 Role 조회 및 정렬 최적화)
        Index(
            "idx_role_master_active_order",
            "IS_ACTIVE",
            "DISPLAY_ORDER"
        ),
    )
    
    def __repr__(self):
        return (
            f"<RoleMaster(role_id='{self.role_id}', "
            f"role_name='{self.role_name}')>"
        )


class PermissionGroup(Base):
    """
    권한 그룹 테이블 (그룹)
    
    - 사용자가 화면에서 직접 권한 그룹을 생성
    - 시스템 관리자: 기준정보 + 사용자관리 + 모든 공정 접근 가능
    - 통합관리자: 모든 공정 접근 가능
    - 공정 관리자: 지정한 공정만 접근 가능
    - 일반 사용자: 그룹에 속하지 않음 (메뉴 접근 불가, 채팅만 가능)
    """

    __tablename__ = "GROUPS"

    # Primary Key
    group_id = Column(
        "GROUP_ID",
        String(50),
        primary_key=True,
        comment="권한 그룹 ID (PK)"
    )

    # 그룹 정보
    group_name = Column(
        "GROUP_NAME",
        String(100),
        nullable=False,
        comment="권한 그룹명 (예: 시스템 관리자, 통합 관리자, 공정 관리자 등)"
    )
    description = Column(
        "DESCRIPTION",
        Text,
        nullable=True,
        comment="권한 그룹 설명"
    )
    
    # Role 권한 (FK)
    # ROLE_MASTER 테이블을 참조하여 Role 정보 관리
    role_id = Column(
        "ROLE_ID",
        String(50),
        ForeignKey("ROLE_MASTER.ROLE_ID"),
        nullable=False,
        index=True,
        comment="Role ID (FK) - ROLE_MASTER 참조"
    )
    
    # Role 상수 (하위 호환성을 위해 유지)
    ROLE_SYSTEM_ADMIN = "system_admin"
    ROLE_INTEGRATED_ADMIN = "integrated_admin"
    ROLE_PROCESS_MANAGER = "process_manager"
    
    VALID_ROLES = [
        ROLE_SYSTEM_ADMIN,
        ROLE_INTEGRATED_ADMIN,
        ROLE_PROCESS_MANAGER,
    ]

    # 메뉴 접근 권한은 ROLE로 판단:
    # - system_admin: 기준정보 + 사용자관리 + 모든 공정 접근 가능
    # - integrated_admin: 모든 공정 접근 가능
    # - process_manager: 지정한 공정만 접근 가능
    # - 일반 사용자 (그룹 없음): 메뉴 접근 불가, 채팅만 가능

    # 활성화 여부
    is_active = Column(
        "IS_ACTIVE",
        Boolean,
        nullable=False,
        server_default=true(),
        comment="활성화 여부"
    )

    # 시간 정보
    create_dt = Column(
        "CREATE_DT",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="생성 일시"
    )
    create_user = Column(
        "CREATE_USER",
        String(50),
        nullable=False,
        comment="생성자"
    )
    update_dt = Column(
        "UPDATE_DT",
        DateTime,
        nullable=True,
        onupdate=func.now(),
        comment="수정 일시"
    )
    update_user = Column(
        "UPDATE_USER",
        String(50),
        nullable=True,
        comment="수정자"
    )

    # 삭제 관리
    is_deleted = Column(
        "IS_DELETED",
        Boolean,
        nullable=False,
        server_default=false(),
        comment="삭제 여부 (소프트 삭제)"
    )
    deleted_at = Column(
        "DELETED_AT",
        DateTime,
        nullable=True,
        comment="삭제 일시"
    )
    deleted_by = Column(
        "DELETED_BY",
        String(50),
        nullable=True,
        comment="삭제자"
    )

    # 인덱스 정의
    __table_args__ = (
        # is_active + is_deleted 복합 인덱스 (활성 그룹 조회 최적화)
        Index(
            "idx_permission_group_active_deleted",
            "IS_ACTIVE",
            "IS_DELETED"
        ),
        # role_id 단일 인덱스 (role별 그룹 조회 최적화)
        Index(
            "idx_group_role",
            "ROLE_ID"
        ),
    )

    def __repr__(self):
        return (
            f"<PermissionGroup(group_id='{self.group_id}', "
            f"group_name='{self.group_name}')>"
        )


class GroupProcessPermission(Base):
    """
    그룹별 공정 권한 테이블 (그룹-공정 매핑)
    
    - 공정 관리자 그룹의 경우, 접근 가능한 공정을 여기에 추가
    - 시스템 관리자, 통합관리자는 모든 공정에 접근 가능하므로 이 테이블에 데이터가 없을 수 있음
    """

    __tablename__ = "GROUP_PROCESSES"

    # Primary Key
    permission_id = Column(
        "PERMISSION_ID",
        String(50),
        primary_key=True,
        comment="권한 ID (PK)"
    )

    # 그룹 및 공정 정보
    group_id = Column(
        "GROUP_ID",
        String(50),
        ForeignKey("GROUPS.GROUP_ID"),
        nullable=False,
        index=True,
        comment="그룹 ID (FK)"
    )
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=False,
        index=True,
        comment="공정 ID"
    )

    # 활성화 여부
    is_active = Column(
        "IS_ACTIVE",
        Boolean,
        nullable=False,
        server_default=true(),
        comment="활성화 여부"
    )

    # 시간 정보
    create_dt = Column(
        "CREATE_DT",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="생성 일시"
    )
    create_user = Column(
        "CREATE_USER",
        String(50),
        nullable=False,
        comment="생성자"
    )
    update_dt = Column(
        "UPDATE_DT",
        DateTime,
        nullable=True,
        onupdate=func.now(),
        comment="수정 일시"
    )
    update_user = Column(
        "UPDATE_USER",
        String(50),
        nullable=True,
        comment="수정자"
    )

    # 인덱스 정의
    __table_args__ = (
        # group_id + process_id 복합 유니크 (한 그룹이 같은 공정에 대한 권한을 중복으로 가질 수 없음)
        Index(
            "idx_group_process_unique",
            "GROUP_ID",
            "PROCESS_ID",
            unique=True
        ),
        # group_id + is_active 복합 인덱스 (그룹별 활성 권한 조회 최적화)
        Index(
            "idx_group_process_group_active",
            "GROUP_ID",
            "IS_ACTIVE"
        ),
        # process_id + is_active 복합 인덱스 (공정별 활성 권한 조회 최적화)
        Index(
            "idx_group_process_process_active",
            "PROCESS_ID",
            "IS_ACTIVE"
        ),
    )

    def __repr__(self):
        return (
            f"<GroupProcessPermission(permission_id='{self.permission_id}', "
            f"group_id='{self.group_id}', process_id='{self.process_id}')>"
        )


class UserGroupMapping(Base):
    """
    사용자-그룹 매핑 테이블 (사용자 그룹)
    
    - 사용자는 여러 그룹에 속할 수 있음
    - 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합
    """

    __tablename__ = "USER_GROUPS"

    # Primary Key
    mapping_id = Column(
        "MAPPING_ID",
        String(50),
        primary_key=True,
        comment="매핑 ID (PK)"
    )

    # 사용자 및 그룹 정보
    user_id = Column(
        "USER_ID",
        String(50),
        ForeignKey("USERS.USER_ID"),
        nullable=False,
        index=True,
        comment="사용자 ID (FK)"
    )
    group_id = Column(
        "GROUP_ID",
        String(50),
        ForeignKey("GROUPS.GROUP_ID"),
        nullable=False,
        index=True,
        comment="그룹 ID (FK)"
    )

    # 활성화 여부
    is_active = Column(
        "IS_ACTIVE",
        Boolean,
        nullable=False,
        server_default=true(),
        comment="활성화 여부"
    )

    # 시간 정보
    create_dt = Column(
        "CREATE_DT",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="생성 일시"
    )
    create_user = Column(
        "CREATE_USER",
        String(50),
        nullable=False,
        comment="생성자"
    )
    update_dt = Column(
        "UPDATE_DT",
        DateTime,
        nullable=True,
        onupdate=func.now(),
        comment="수정 일시"
    )
    update_user = Column(
        "UPDATE_USER",
        String(50),
        nullable=True,
        comment="수정자"
    )

    # 인덱스 정의
    __table_args__ = (
        # user_id + group_id 복합 유니크 (한 사용자가 같은 그룹에 중복으로 속할 수 없음)
        Index(
            "idx_user_group_unique",
            "USER_ID",
            "GROUP_ID",
            unique=True
        ),
        # user_id + is_active 복합 인덱스 (사용자별 활성 매핑 조회 최적화)
        Index(
            "idx_user_group_user_active",
            "USER_ID",
            "IS_ACTIVE"
        ),
        # group_id + is_active 복합 인덱스 (그룹별 활성 매핑 조회 최적화)
        Index(
            "idx_user_group_group_active",
            "GROUP_ID",
            "IS_ACTIVE"
        ),
    )

    def __repr__(self):
        return (
            f"<UserGroupMapping(mapping_id='{self.mapping_id}', "
            f"user_id='{self.user_id}', group_id='{self.group_id}')>"
        )

