# _*_ coding: utf-8 _*_
"""
PLC 모델 정의
PLC 기준 정보 및 Program 매핑 테이블

Hierarchy 구조: Plant → 공정(Process) → Line → PLC명 → 호기(Unit)
- Plant, Process, Line: 운영자가 입력하는 마스터 데이터 (드롭다운 선택)
- PLC명, 호기, PLC ID: 사용자가 화면에서 직접 입력
- 한번 입력된 PLC의 hierarchy는 수정되지 않음
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.sql.expression import false, true

from src.database.base import Base


class PLC(Base):
    """
    PLC 기준 정보 및 Program 매핑 테이블
    
    Hierarchy 구조: Plant → 공정(Process) → Line → PLC명 → 호기(Unit)
    - Plant, Process, Line: 운영자가 입력하는 마스터 데이터
    - PLC명, 호기, PLC ID: 사용자가 화면에서 직접 입력
    - 한번 입력된 hierarchy는 수정되지 않음
    """

    __tablename__ = "PLC"

    # Primary Key (기존 id를 plc_uuid로 변경)
    plc_uuid = Column("PLC_UUID", String(50), primary_key=True)

    # Hierarchy: Plant → 공정(Process) → Line (운영자 입력, 드롭다운 선택)
    plant_id = Column(
        "PLANT_ID",
        String(50),
        ForeignKey("PLANT_MASTER.PLANT_ID"),
        nullable=False,
        index=True,
        comment="Plant ID (hierarchy 1단계, 필수)"
    )
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=False,
        index=True,
        comment="공정(Process) ID (hierarchy 2단계, 필수)"
    )
    line_id = Column(
        "LINE_ID",
        String(50),
        ForeignKey("LINE_MASTER.LINE_ID"),
        nullable=False,
        index=True,
        comment="Line ID (hierarchy 3단계, 필수)"
    )

    # Hierarchy: PLC명 → 호기 (사용자 직접 입력)
    plc_name = Column(
        "PLC_NAME",
        String(255),
        nullable=False,
        comment="PLC명 (hierarchy 4단계, 사용자 입력)"
    )
    unit = Column(
        "UNIT",
        String(100),
        nullable=True,
        comment="호기 (hierarchy 5단계, 사용자 입력, 예: 1, 2)"
    )

    # PLC ID (사용자 직접 입력)
    plc_id = Column(
        "PLC_ID",
        String(50),
        nullable=False,
        index=True,
        comment="PLC 식별자 (사용자 수기 입력)"
    )

    # Program 매핑
    program_id = Column(
        "PROGRAM_ID",
        String(50),
        ForeignKey("PROGRAMS.PROGRAM_ID"),
        nullable=True,
        unique=True,
        index=True,
        comment="PLC 1개 → Program 1개 (unique)"
    )
    mapping_dt = Column("MAPPING_DT", DateTime, nullable=True)
    mapping_user = Column("MAPPING_USER", String(50), nullable=True)

    # 활성화 여부 (deprecated: is_deleted 사용)
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 삭제 관리
    is_deleted = Column(
        "IS_DELETED",
        Boolean,
        nullable=False,
        server_default=false(),
        index=True,
        comment="삭제 여부 (소프트 삭제, false인 것은 사용 중으로 인식)"
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

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 등록 정보 (PLC 입력한 사람과 등록일시)
    create_dt = Column(
        "CREATE_DT",
        DateTime,
        nullable=False,
        server_default=func.now(),
        comment="PLC 등록일시"
    )
    create_user = Column(
        "CREATE_USER",
        String(50),
        nullable=False,
        comment="PLC 입력한 사람"
    )
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    def __repr__(self):
        return (
            f"<PLC(plc_uuid='{self.plc_uuid}', plc_id='{self.plc_id}', "
            f"plc_name='{self.plc_name}', program_id='{self.program_id}')>"
        )
