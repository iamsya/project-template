# _*_ coding: utf-8 _*_
"""
권한 체크 공통 기능
FastAPI Depends를 사용하여 라우터에서 권한 체크

사용 예시:
    # 1. 시스템 관리자만 허용
    @router.post("/programs/register")
    async def register_program(
        user_id: str = Query(...),
        db: Session = Depends(get_db),
        _: None = Depends(lambda: check_system_admin(user_id, db)),
    ):
        # ...

    # 2. 시스템 관리자 또는 통합 관리자 허용
    @router.get("/programs")
    async def get_programs(
        user_id: str = Query(...),
        db: Session = Depends(get_db),
        _: None = Depends(lambda: check_admin(user_id, db)),
    ):
        # ...

    # 3. 특정 공정 접근 권한 체크
    @router.get("/programs/{program_id}")
    async def get_program(
        program_id: str,
        user_id: str = Query(...),
        db: Session = Depends(get_db),
        _: None = Depends(lambda: check_program_access(program_id, user_id, db)),
    ):
        # ...
"""
import logging
from typing import List, Optional

from fastapi import Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from src.core.dependencies import get_db
from src.database.crud.program_crud import ProgramCRUD
from src.database.models.permission_group_models import PermissionGroup

logger = logging.getLogger(__name__)

# ==================== 헬퍼 함수 ====================


def is_all_processes_accessible(accessible_process_ids: Optional[List[str]]) -> bool:
    """
    접근 가능한 공정 ID 목록이 "모든 공정 접근 가능"을 의미하는지 확인

    get_accessible_process_ids()의 반환값 해석:
    - None: 모든 공정 접근 가능 (system_admin 또는 process_admin)
    - List[str]: 특정 공정만 접근 가능 (process_manager)
    - []: 접근 불가 (일반 사용자)

    Args:
        accessible_process_ids: get_accessible_process_ids()의 반환값

    Returns:
        bool: True면 모든 공정 접근 가능, False면 특정 공정만 또는 접근 불가
    """
    return accessible_process_ids is None


def is_process_accessible(
    process_id: str, accessible_process_ids: Optional[List[str]]
) -> bool:
    """
    특정 공정에 접근 가능한지 확인하는 헬퍼 함수

    Args:
        process_id: 확인할 공정 ID
        accessible_process_ids: 접근 가능한 공정 ID 목록
            - None: 모든 공정 접근 가능 (항상 True 반환)
            - List[str]: 특정 공정만 접근 가능 (process_id가 리스트에 있는지 확인)
            - []: 접근 불가 (항상 False 반환)

    Returns:
        bool: 접근 가능하면 True, 불가하면 False
    """
    if accessible_process_ids is None:
        return True  # 모든 공정 접근 가능
    if not accessible_process_ids:
        return False  # 접근 불가
    return process_id in accessible_process_ids


# ==================== 권한 체크 함수들 ====================


def get_user_roles(user_id: str, db: Session) -> List[str]:
    """
    사용자가 가진 역할 목록 조회

    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Returns:
        List[str]: 역할 ID 목록 (예: ['system_admin'], ['process_manager'], [])
    """
    try:
        from src.database.models.permission_group_models import (
            PermissionGroup,
            UserGroupMapping,
        )

        groups = (
            db.query(PermissionGroup)
            .join(
                UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id
            )
            .filter(UserGroupMapping.user_id == user_id)
            .all()
        )

        roles = [group.role_id for group in groups]
        return list(set(roles))  # 중복 제거

    except Exception as e:
        logger.error(f"사용자 역할 조회 실패: user_id={user_id}, error={str(e)}")
        return []


def check_system_admin(user_id: str, db: Session) -> None:
    """
    시스템 관리자 권한 체크

    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 시스템 관리자가 아닐 때 403 에러
    """
    roles = get_user_roles(user_id, db)

    if PermissionGroup.ROLE_SYSTEM_ADMIN not in roles:
        logger.warning(f"시스템 관리자 권한 없음: user_id={user_id}, roles={roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="시스템 관리자 권한이 필요합니다.",
        )


def check_admin(user_id: str, db: Session) -> None:
    """
    시스템 관리자 또는 공정 관리자 권한 체크

    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 권한이 없을 때 403 에러
    """
    roles = get_user_roles(user_id, db)

    allowed_roles = [
        PermissionGroup.ROLE_SYSTEM_ADMIN,
        PermissionGroup.ROLE_PROCESS_ADMIN,
    ]

    if not any(role in roles for role in allowed_roles):
        logger.warning(f"관리자 권한 없음: user_id={user_id}, roles={roles}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="시스템 관리자 또는 공정 관리자 권한이 필요합니다.",
        )


def check_system_admin_dependency(
    request: Request,
    db: Session = Depends(get_db),
) -> None:
    """
    시스템 관리자 권한 체크 - Depends용 래퍼 함수

    FastAPI Depends에서 사용하기 위한 래퍼 함수입니다.
    system_admin이 아니면 403 에러를 반환합니다.
    request.state.user_id (SSO)만 사용합니다.

    라우터에서 다음과 같이 사용:
        _: None = Depends(check_system_admin_dependency)
    """
    # request.state.user_id만 사용
    check_user_id = getattr(request.state, "user_id", None)

    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )

    check_system_admin(check_user_id, db)


def check_admin_dependency(
    request: Request,
    user_id: Optional[str] = Query(
        None,
        description="사용자 ID (테스트용. request.state.user_id가 있으면 우선 사용)",
    ),
    db: Session = Depends(get_db),
) -> None:
    """
    시스템 관리자 또는 공정 관리자 권한 체크 - Depends용 래퍼 함수

    FastAPI Depends에서 사용하기 위한 래퍼 함수입니다.
    system_admin 또는 process_admin이 아니면 403 에러를 반환합니다.

    user_id 우선순위:
    1. request.state.user_id (미들웨어에서 설정된 경우) - 우선 사용
    2. 파라미터 user_id (테스트용) - fallback

    라우터에서 다음과 같이 사용:
        _: None = Depends(check_admin_dependency)
    """
    from src.core.dependencies import resolve_user_id

    # request.state.user_id 우선 사용 (미들웨어에서 설정된 경우), 없으면 파라미터 user_id 사용 (테스트용)
    check_user_id = resolve_user_id(request, user_id)

    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )

    check_admin(check_user_id, db)


def check_any_role_dependency(
    request: Request,
    user_id: Optional[str] = Query(
        None,
        description="사용자 ID (테스트용. request.state.user_id가 있으면 우선 사용)",
    ),
    db: Session = Depends(get_db),
) -> None:
    """
    모든 역할 허용 (일반 사용자 제외) - Depends용 래퍼 함수

    FastAPI Depends에서 사용하기 위한 래퍼 함수입니다.

    user_id 우선순위:
    1. request.state.user_id (미들웨어에서 설정된 경우) - 우선 사용
    2. 파라미터 user_id (테스트용) - fallback

    라우터에서 다음과 같이 사용:
        _: None = Depends(check_any_role_dependency)
    """
    from src.core.dependencies import resolve_user_id

    # request.state.user_id 우선 사용 (미들웨어에서 설정된 경우), 없으면 파라미터 user_id 사용 (테스트용)
    check_user_id = resolve_user_id(request, user_id)

    if not check_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="사용자 ID가 필요합니다.",
        )

    check_any_role(check_user_id, db)


def check_any_role(user_id: str, db: Session) -> None:
    """
    모든 역할 허용 (일반 사용자 제외)
    - system_admin, process_admin, process_manager 중 하나라도 있으면 허용

    Args:
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 권한이 없을 때 403 에러
    """
    program_crud = ProgramCRUD(db)
    accessible_process_ids = program_crud.get_accessible_process_ids(user_id)

    # 모든 공정 접근 가능 (system_admin 또는 process_admin)이면 허용
    if is_all_processes_accessible(accessible_process_ids):
        return

    # 접근 가능한 공정이 없으면 (일반 사용자)
    if not accessible_process_ids:
        logger.warning(
            f"권한 없음: user_id={user_id}, accessible_process_ids={accessible_process_ids}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 기능을 사용할 권한이 없습니다.",
        )


def check_process_access_by_id(process_id: str, user_id: str, db: Session) -> None:
    """
    특정 공정에 대한 접근 권한 체크

    Args:
        process_id: 공정 ID
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 접근 권한이 없으면 403 에러
    """
    program_crud = ProgramCRUD(db)
    accessible_process_ids = program_crud.get_accessible_process_ids(user_id)

    # None이면 모든 공정 접근 가능 (system_admin 또는 process_admin)
    if accessible_process_ids is None:
        return

    # 빈 리스트면 접근 불가 (일반 사용자)
    if not accessible_process_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"공정 '{process_id}'에 접근할 권한이 없습니다.",
        )

    # 특정 공정만 접근 가능한 경우, 요청한 공정이 포함되어 있는지 확인
    if process_id not in accessible_process_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"공정 '{process_id}'에 접근할 권한이 없습니다.",
        )


def check_process_access(process_id: str, user_id: str, db: Session) -> None:
    """
    특정 공정 접근 권한 체크

    Args:
        process_id: 체크할 공정 ID
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 공정 접근 권한이 없을 때 403 에러
    """
    program_crud = ProgramCRUD(db)
    accessible_process_ids = program_crud.get_accessible_process_ids(user_id)

    # 모든 공정 접근 가능 (system_admin 또는 integrated_admin)
    if is_all_processes_accessible(accessible_process_ids):
        return

    # 특정 공정만 접근 가능한 경우
    if process_id not in accessible_process_ids:
        logger.warning(
            f"공정 접근 권한 없음: user_id={user_id}, "
            f"process_id={process_id}, accessible_process_ids={accessible_process_ids}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"공정 '{process_id}'에 접근할 권한이 없습니다.",
        )


def check_program_access(program_id: str, user_id: str, db: Session) -> None:
    """
    프로그램 접근 권한 체크 (프로그램의 process_id로 체크)

    Args:
        program_id: 프로그램 ID
        user_id: 사용자 ID
        db: 데이터베이스 세션

    Raises:
        HTTPException: 프로그램 접근 권한이 없을 때 403 에러
    """
    program_crud = ProgramCRUD(db)

    # 프로그램 조회
    program = program_crud.get_program(program_id)
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"프로그램을 찾을 수 없습니다: {program_id}",
        )

    # 프로그램의 process_id로 접근 권한 체크
    if program.process_id:
        check_process_access(program.process_id, user_id, db)
