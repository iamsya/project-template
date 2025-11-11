# _*_ coding: utf-8 _*_
"""
PLC 모델 정의
PLC 기준 정보 및 Program 매핑 테이블 (기준정보 스냅샷 포함)
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, func
from sqlalchemy.sql.expression import true

from src.database.base import Base


class PLC(Base):
    """PLC 기준 정보 및 Program 매핑 테이블 (기준정보 스냅샷 포함)"""

    __tablename__ = "PLC"

    # 기본 정보
    id = Column("ID", String(50), primary_key=True)
    plc_id = Column("PLC_ID", String(50), nullable=False, index=True)  # PLC 식별자 (중복 가능)
    plc_name = Column("PLC_NAME", String(255), nullable=False)
    unit = Column("UNIT", String(100), nullable=True)

    # Program 매핑
    program_id = Column(
        "PROGRAM_ID",
        String(50),
        ForeignKey("PROGRAMS.PROGRAM_ID"),
        nullable=True,
        unique=True,
        index=True,
    )  # PLC 1개 → Program 1개 (unique)
    mapping_dt = Column("MAPPING_DT", DateTime, nullable=True)
    mapping_user = Column("MAPPING_USER", String(50), nullable=True)

    # 활성화 여부
    is_active = Column("IS_ACTIVE", Boolean, nullable=False, server_default=true())

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column("UPDATE_DT", DateTime, nullable=True, onupdate=func.now())
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    # 기준정보 스냅샷 (PLC 생성/수정 시점의 기준정보 저장, 불변)
    # 각 레벨별 ID만 저장 (code, name은 master 테이블 조인으로 조회)
    plant_id_snapshot = Column("PLANT_ID_SNAPSHOT", String(50), nullable=True, index=True)
    process_id_snapshot = Column("PROCESS_ID_SNAPSHOT", String(50), nullable=True, index=True)
    line_id_snapshot = Column("LINE_ID_SNAPSHOT", String(50), nullable=True, index=True)
    equipment_group_id_snapshot = Column("EQUIPMENT_GROUP_ID_SNAPSHOT", String(50), nullable=True, index=True)

    # 현재 기준정보 참조 (nullable, 선택 시 사용)
    plant_id_current = Column("PLANT_ID_CURRENT", String(50), ForeignKey("PLANT_MASTER.PLANT_ID"), nullable=True, index=True)
    process_id_current = Column("PROCESS_ID_CURRENT", String(50), ForeignKey("PROCESS_MASTER.PROCESS_ID"), nullable=True, index=True)
    line_id_current = Column("LINE_ID_CURRENT", String(50), ForeignKey("LINE_MASTER.LINE_ID"), nullable=True, index=True)
    equipment_group_id_current = Column("EQUIPMENT_GROUP_ID_CURRENT", String(50), ForeignKey("EQUIPMENT_GROUP_MASTER.EQUIPMENT_GROUP_ID"), nullable=True, index=True)

    def __repr__(self):
        return f"<PLC(id='{self.id}', plc_id='{self.plc_id}', plc_name='{self.plc_name}', program_id='{self.program_id}')>"
