import uuid
import random
import string
from datetime import datetime


__all__ = [
    "gen",
    "gen_completions_id",
    "gen_plc_uuid",
    "gen_program_id",
    "gen_template_id",
]


def gen() -> str:
    return str(uuid.uuid4())


def gen_completions_id(uid: str = None) -> str:
    return f"comp-{gen() if uid is None else uid}"


def gen_plc_uuid(plc_id: str) -> str:
    """
    PLC UUID 자동 생성
    형식: plc_{plc_id}_{타임스탬프}_{랜덤문자열}
    예: plc_M4001000_2501011200_a1b2c3

    Args:
        plc_id: PLC ID (사용자 입력값)

    Returns:
        str: 생성된 PLC UUID
    """
    # 타임스탬프: YYMMDDHHMM (10자리, 연도 2자리, 초 제거)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    # 6자리 랜덤 문자열 (소문자 + 숫자)
    random_suffix = ''.join(
        random.choices(string.ascii_lowercase + string.digits, k=6)
    )
    return f"plc_{plc_id}_{timestamp}_{random_suffix}"


def gen_program_id(process_id: str) -> str:
    """
    Program ID 자동 생성
    형식: pgm_{process_id}_{타임스탬프}
    예: pgm_process_001_2501011200

    Args:
        process_id: 공정 ID (필수)

    Returns:
        str: 생성된 Program ID
    """
    if not process_id:
        raise ValueError("process_id는 필수입니다.")

    # 타임스탬프: YYMMDDHHMM (10자리, 연도 2자리, 초 제거)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    return f"pgm_{process_id}_{timestamp}"


def gen_template_id(program_id: str) -> str:
    """
    Template ID 자동 생성
    형식: tpl_{program_id}_{타임스탬프}
    예: tpl_pgm_process_001_2501011200_2501011201

    Args:
        program_id: 프로그램 ID (필수)

    Returns:
        str: 생성된 Template ID
    """
    if not program_id:
        raise ValueError("program_id는 필수입니다.")

    # 타임스탬프: YYMMDDHHMM (10자리, 연도 2자리, 초 제거)
    timestamp = datetime.now().strftime("%y%m%d%H%M")
    return f"tpl_{program_id}_{timestamp}"
