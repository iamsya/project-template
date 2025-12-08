# _*_ coding: utf-8 _*_
"""
날짜/시간 유틸리티 함수들
Asia/Seoul 시간대를 기본으로 사용
"""
from datetime import datetime
from zoneinfo import ZoneInfo

# 기본 시간대 (Asia/Seoul)
DEFAULT_TIMEZONE = ZoneInfo("Asia/Seoul")


def get_current_datetime(timezone: ZoneInfo = None) -> datetime:
    """
    현재 시간을 가져옵니다 (Asia/Seoul 시간대)
    
    Args:
        timezone: 시간대 (기본값: Asia/Seoul)
        
    Returns:
        datetime: 현재 시간 (Asia/Seoul 시간대)
        
    Examples:
        >>> now = get_current_datetime()
        >>> print(now)
        2025-01-15 15:30:45+09:00
        
        >>> utc_now = get_current_datetime(ZoneInfo("UTC"))
        >>> print(utc_now)
        2025-01-15 06:30:45+00:00
    """
    if timezone is None:
        timezone = DEFAULT_TIMEZONE
    return datetime.now(timezone)


def get_current_datetime_iso() -> str:
    """
    현재 시간을 ISO 8601 형식 문자열로 반환합니다 (Asia/Seoul 시간대)
    
    Returns:
        str: ISO 8601 형식 시간 문자열 (예: "2025-01-15T15:30:45+09:00")
        
    Examples:
        >>> iso_time = get_current_datetime_iso()
        >>> print(iso_time)
        2025-01-15T15:30:45+09:00
    """
    return get_current_datetime().isoformat()


def get_current_datetime_str(format: str = "%Y%m%d_%H%M%S") -> str:
    """
    현재 시간을 지정된 형식의 문자열로 반환합니다 (Asia/Seoul 시간대)
    
    Args:
        format: 시간 형식 문자열 (기본값: "%Y%m%d_%H%M%S")
        
    Returns:
        str: 형식화된 시간 문자열
        
    Examples:
        >>> time_str = get_current_datetime_str()
        >>> print(time_str)
        20250115_153045
        
        >>> time_str = get_current_datetime_str("%Y-%m-%d %H:%M:%S")
        >>> print(time_str)
        2025-01-15 15:30:45
    """
    return get_current_datetime().strftime(format)


__all__ = [
    "DEFAULT_TIMEZONE",
    "get_current_datetime",
    "get_current_datetime_iso",
    "get_current_datetime_str",
]

