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
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import false, true

from src.database.base import Base


class PermissionGroup(Base):
    """
    권한 그룹 테이블
    
    - 사용자가 화면에서 직접 권한 그룹을 생성
    - super 권한: 기준정보 메뉴 접근 가능
    - plc 권한그룹: program 탭 등 여러 탭 접근 가능
    """

    __tablename__ = "PERMISSION_GROUPS"

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
    
    # Role 권한 (단수 선택)
    # 시스템 관리자: 사용자 관리 + 모든 공정 접근 권한
    # 통합 관리자: PLC 모든 공정 접근 가능
    # 공정 관리자: 선택한 공정만 접근 가능
    role = Column(
        "ROLE",
        String(50),
        nullable=False,
        index=True,
        comment=(
            "Role 권한 타입: "
            "system_admin (시스템 관리자), "
            "integrated_admin (통합 관리자), "
            "process_manager (공정 관리자)"
        )
    )
    
    # Role 상수
    ROLE_SYSTEM_ADMIN = "system_admin"
    ROLE_INTEGRATED_ADMIN = "integrated_admin"
    ROLE_PROCESS_MANAGER = "process_manager"
    
    VALID_ROLES = [
        ROLE_SYSTEM_ADMIN,
        ROLE_INTEGRATED_ADMIN,
        ROLE_PROCESS_MANAGER,
    ]

    # 메뉴 접근 권한 (JSON)
    # 프론트엔드에서 이 값을 받아서 해당 메뉴들을 보여주거나 숨김
    # 예: {"menus": ["기준정보", "program", "chat", "plc_management"]}
    # 이 배열에 포함된 메뉴명만 화면에 표시됨
    menu_permissions = Column(
        "MENU_PERMISSIONS",
        JSON,
        nullable=True,
        comment=(
            "접근 가능한 메뉴명 리스트 (JSON): "
            "{'menus': ['기준정보', 'program', 'chat', 'plc_management']} "
            "프론트엔드에서 이 값을 받아서 해당 메뉴들을 표시"
        )
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
        # role 단일 인덱스 (role별 그룹 조회 최적화)
        Index(
            "idx_permission_group_role",
            "ROLE"
        ),
    )

    def __repr__(self):
        return (
            f"<PermissionGroup(group_id='{self.group_id}', "
            f"group_name='{self.group_name}')>"
        )


class GroupProcessPermission(Base):
    """
    권한 그룹별 공정 권한 테이블
    
    - plc 권한그룹의 경우, 접근 가능한 공정을 여기에 추가
    - super 권한그룹은 모든 공정에 접근 가능하므로 이 테이블에 데이터가 없을 수 있음
    """

    __tablename__ = "GROUP_PROCESS_PERMISSIONS"

    # Primary Key
    permission_id = Column(
        "PERMISSION_ID",
        String(50),
        primary_key=True,
        comment="권한 ID (PK)"
    )

    # 권한 그룹 및 공정 정보
    group_id = Column(
        "GROUP_ID",
        String(50),
        ForeignKey("PERMISSION_GROUPS.GROUP_ID"),
        nullable=False,
        index=True,
        comment="권한 그룹 ID"
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
            "idx_group_process_permission_unique",
            "GROUP_ID",
            "PROCESS_ID",
            unique=True
        ),
        # group_id + is_active 복합 인덱스 (그룹별 활성 권한 조회 최적화)
        Index(
            "idx_group_process_permission_group_active",
            "GROUP_ID",
            "IS_ACTIVE"
        ),
        # process_id + is_active 복합 인덱스 (공정별 활성 권한 조회 최적화)
        Index(
            "idx_group_process_permission_process_active",
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
    사용자-권한 그룹 매핑 테이블
    
    - 사용자는 여러 권한 그룹에 속할 수 있음
    - 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합
    """

    __tablename__ = "USER_GROUP_MAPPINGS"

    # Primary Key
    mapping_id = Column(
        "MAPPING_ID",
        String(50),
        primary_key=True,
        comment="매핑 ID (PK)"
    )

    # 사용자 및 권한 그룹 정보
    user_id = Column(
        "USER_ID",
        String(50),
        ForeignKey("USERS.USER_ID"),
        nullable=False,
        index=True,
        comment="사용자 ID"
    )
    group_id = Column(
        "GROUP_ID",
        String(50),
        ForeignKey("PERMISSION_GROUPS.GROUP_ID"),
        nullable=False,
        index=True,
        comment="권한 그룹 ID"
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
            "idx_user_group_mapping_unique",
            "USER_ID",
            "GROUP_ID",
            unique=True
        ),
        # user_id + is_active 복합 인덱스 (사용자별 활성 매핑 조회 최적화)
        Index(
            "idx_user_group_mapping_user_active",
            "USER_ID",
            "IS_ACTIVE"
        ),
        # group_id + is_active 복합 인덱스 (그룹별 활성 매핑 조회 최적화)
        Index(
            "idx_user_group_mapping_group_active",
            "GROUP_ID",
            "IS_ACTIVE"
        ),
    )

    def __repr__(self):
        return (
            f"<UserGroupMapping(mapping_id='{self.mapping_id}', "
            f"user_id='{self.user_id}', group_id='{self.group_id}')>"
        )

