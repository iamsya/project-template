# _*_ coding: utf-8 _*_
"""
기준정보 마스터 모델 정의
공장, 공정, 라인, 장비 그룹 기준정보 마스터 테이블들
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.sql.expression import true

from src.database.base import Base


class PlantMaster(Base):
    """공장 기준정보 마스터 테이블"""

    __tablename__ = "PLANT_MASTER"

    # 기본 정보
    plant_id = Column("PLANT_ID", String(50), primary_key=True)
    plant_code = Column(
        "PLANT_CODE", String(50), unique=True, nullable=False, index=True
    )
    plant_name = Column("PLANT_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
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

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # is_active + display_order 복합 인덱스 (활성 항목 조회 및 정렬 최적화)
        Index("idx_plant_master_active_order", "IS_ACTIVE", "DISPLAY_ORDER"),
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_plant_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<PlantMaster(plant_id='{self.plant_id}', "
            f"plant_code='{self.plant_code}', "
            f"plant_name='{self.plant_name}')>"
        )


class ProcessMaster(Base):
    """공정 기준정보 마스터 테이블"""

    __tablename__ = "PROCESS_MASTER"

    # 기본 정보
    process_id = Column("PROCESS_ID", String(50), primary_key=True)
    process_code = Column(
        "PROCESS_CODE", String(50), unique=True, nullable=False, index=True
    )
    process_name = Column("PROCESS_NAME", String(255), nullable=False)
    plant_id = Column(
        "PLANT_ID",
        String(50),
        ForeignKey("PLANT_MASTER.PLANT_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
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

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # plant_id + is_active 복합 인덱스 (공장별 활성 공정 조회 최적화)
        Index("idx_process_master_plant_active", "PLANT_ID", "IS_ACTIVE"),
        # is_active + display_order 복합 인덱스 (활성 항목 조회 및 정렬 최적화)
        Index("idx_process_master_active_order", "IS_ACTIVE", "DISPLAY_ORDER"),
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_process_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<ProcessMaster(process_id='{self.process_id}', "
            f"process_code='{self.process_code}', "
            f"process_name='{self.process_name}')>"
        )


class LineMaster(Base):
    """라인 기준정보 마스터 테이블"""

    __tablename__ = "LINE_MASTER"

    # 기본 정보
    line_id = Column("LINE_ID", String(50), primary_key=True)
    line_code = Column("LINE_CODE", String(50), unique=True, nullable=False, index=True)
    line_name = Column("LINE_NAME", String(255), nullable=False)
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
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

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # process_id + is_active 복합 인덱스 (공정별 활성 라인 조회 최적화)
        Index("idx_line_master_process_active", "PROCESS_ID", "IS_ACTIVE"),
        # is_active + display_order 복합 인덱스 (활성 항목 조회 및 정렬 최적화)
        Index("idx_line_master_active_order", "IS_ACTIVE", "DISPLAY_ORDER"),
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_line_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<LineMaster(line_id='{self.line_id}', "
            f"line_code='{self.line_code}', "
            f"line_name='{self.line_name}')>"
        )


class EquipmentGroupMaster(Base):
    """장비 그룹 기준정보 마스터 테이블"""

    __tablename__ = "EQUIPMENT_GROUP_MASTER"

    # 기본 정보
    equipment_group_id = Column("EQUIPMENT_GROUP_ID", String(50), primary_key=True)
    equipment_group_code = Column(
        "EQUIPMENT_GROUP_CODE", String(50), unique=True, nullable=False, index=True
    )
    equipment_group_name = Column("EQUIPMENT_GROUP_NAME", String(255), nullable=False)
    line_id = Column(
        "LINE_ID",
        String(50),
        ForeignKey("LINE_MASTER.LINE_ID"),
        nullable=False,
        index=True,
    )
    description = Column("DESCRIPTION", Text, nullable=True)

    # 표시 순서 및 활성화
    display_order = Column("DISPLAY_ORDER", Integer, nullable=True, default=0)
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

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # line_id + is_active 복합 인덱스 (라인별 활성 장비 그룹 조회 최적화)
        Index("idx_equipment_group_master_line_active", "LINE_ID", "IS_ACTIVE"),
        # is_active + display_order 복합 인덱스 (활성 항목 조회 및 정렬 최적화)
        Index("idx_equipment_group_master_active_order", "IS_ACTIVE", "DISPLAY_ORDER"),
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_equipment_group_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<EquipmentGroupMaster(equipment_group_id='{self.equipment_group_id}', "
            f"equipment_group_code='{self.equipment_group_code}', "
            f"equipment_group_name='{self.equipment_group_name}')>"
        )

