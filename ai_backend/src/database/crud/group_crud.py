# _*_ coding: utf-8 _*_
"""
그룹 관리 CRUD 작업
권한 그룹 생성, 조회, 수정, 삭제
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from src.database.models.permission_group_models import (
    GroupProcessPermission,
    PermissionGroup,
    UserGroupMapping,
)
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class GroupCRUD:
    """그룹 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def delete_group(
        self, group_id: str, deleted_by: str
    ) -> bool:
        """
        그룹 삭제 (실제 삭제)
        
        그룹 삭제 시 관련 데이터도 함께 실제 삭제:
        1. 관련된 USER_GROUPS 삭제
        2. 관련된 GROUP_PROCESSES 삭제
        3. GROUPS 삭제
        
        Args:
            group_id: 삭제할 그룹 ID
            deleted_by: 삭제자 (로깅용)
            
        Returns:
            bool: 삭제 성공 여부
            
        Raises:
            HandledException: 그룹을 찾을 수 없거나 삭제 실패 시
        """
        try:
            # 1. 그룹 조회
            group = (
                self.db.query(PermissionGroup)
                .filter(PermissionGroup.group_id == group_id)
                .first()
            )
            
            if not group:
                raise HandledException(
                    ResponseCode.DATABASE_QUERY_ERROR,
                    msg=f"그룹을 찾을 수 없습니다: {group_id}",
                )
            
            # 2. 관련된 USER_GROUPS 삭제 (FK 제약조건 때문에 먼저 삭제)
            user_mappings = (
                self.db.query(UserGroupMapping)
                .filter(UserGroupMapping.group_id == group_id)
                .all()
            )
            
            for mapping in user_mappings:
                self.db.delete(mapping)
            
            # 3. 관련된 GROUP_PROCESSES 삭제 (FK 제약조건 때문에 먼저 삭제)
            process_permissions = (
                self.db.query(GroupProcessPermission)
                .filter(GroupProcessPermission.group_id == group_id)
                .all()
            )
            
            for permission in process_permissions:
                self.db.delete(permission)
            
            # 4. 그룹 삭제
            self.db.delete(group)
            
            # 5. 커밋
            self.db.commit()
            
            logger.info(
                "그룹 삭제 완료: group_id=%s, "
                "user_mappings=%d, process_permissions=%d",
                group_id,
                len(user_mappings),
                len(process_permissions),
            )
            
            return True
            
        except HandledException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(
                "그룹 삭제 실패: group_id=%s, error=%s", group_id, str(e)
            )
            raise HandledException(
                ResponseCode.GROUP_DELETE_ERROR,
                msg=f"그룹 삭제 중 오류가 발생했습니다: {str(e)}",
                e=e,
            )

    def get_group(self, group_id: str) -> Optional[PermissionGroup]:
        """
        그룹 조회
        
        Args:
            group_id: 그룹 ID
            
        Returns:
            PermissionGroup: 그룹 객체 (없으면 None)
        """
        try:
            return (
                self.db.query(PermissionGroup)
                .filter(PermissionGroup.group_id == group_id)
                .first()
            )
        except Exception as e:
            logger.error(
                "그룹 조회 실패: group_id=%s, error=%s", group_id, str(e)
            )
            raise HandledException(
                ResponseCode.DATABASE_QUERY_ERROR, e=e
            )

    def get_groups_by_role(
        self, role_id: Optional[str] = None
    ) -> List[PermissionGroup]:
        """
        Role별 그룹 목록 조회
        
        Args:
            role_id: Role ID (None이면 모든 Role)
            
        Returns:
            List[PermissionGroup]: 그룹 목록
        """
        try:
            query = (
                self.db.query(PermissionGroup)
                .filter(PermissionGroup.is_active.is_(True))
            )
            
            if role_id:
                query = query.filter(PermissionGroup.role_id == role_id)
            
            return query.all()
        except Exception as e:
            logger.error(
                "그룹 목록 조회 실패: role_id=%s, error=%s",
                role_id,
                str(e),
            )
            raise HandledException(
                ResponseCode.DATABASE_QUERY_ERROR, e=e
            )

