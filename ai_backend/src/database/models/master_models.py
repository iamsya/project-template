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
    plant_name = Column("PLANT_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 활성화
    is_active = Column(
        "IS_ACTIVE", Boolean, nullable=False, server_default=true()
    )

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column(
        "UPDATE_DT", DateTime, nullable=True, onupdate=func.now()
    )
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_plant_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<PlantMaster(plant_id='{self.plant_id}', "
            f"plant_name='{self.plant_name}')>"
        )


class ProcessMaster(Base):
    """공정 기준정보 마스터 테이블"""

    __tablename__ = "PROCESS_MASTER"

    # 기본 정보
    process_id = Column("PROCESS_ID", String(50), primary_key=True)
    process_name = Column("PROCESS_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 활성화
    is_active = Column(
        "IS_ACTIVE", Boolean, nullable=False, server_default=true()
    )

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column(
        "UPDATE_DT", DateTime, nullable=True, onupdate=func.now()
    )
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_process_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<ProcessMaster(process_id='{self.process_id}', "
            f"process_name='{self.process_name}')>"
        )


class LineMaster(Base):
    """라인 기준정보 마스터 테이블"""

    __tablename__ = "LINE_MASTER"

    # 기본 정보
    line_id = Column("LINE_ID", String(50), primary_key=True)
    line_name = Column("LINE_NAME", String(255), nullable=False)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 활성화
    is_active = Column(
        "IS_ACTIVE", Boolean, nullable=False, server_default=true()
    )

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    create_user = Column("CREATE_USER", String(50), nullable=False)
    update_dt = Column(
        "UPDATE_DT", DateTime, nullable=True, onupdate=func.now()
    )
    update_user = Column("UPDATE_USER", String(50), nullable=True)

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # is_active 단일 인덱스 (활성 항목 필터링 최적화)
        Index("idx_line_master_active", "IS_ACTIVE"),
    )

    def __repr__(self):
        return (
            f"<LineMaster(line_id='{self.line_id}', "
            f"line_name='{self.line_name}')>"
        )


class DropdownMaster(Base):
    """드롭다운 리스트용 마스터 테이블 (Plant-Process-Line 계층 구조)"""

    __tablename__ = "DROPDOWN_MASTER"

    # 기본 정보
    dropdown_id = Column("DROPDOWN_ID", String(50), primary_key=True)
    dropdown_name = Column("DROPDOWN_NAME", String(255), nullable=True)
    description = Column("DESCRIPTION", Text, nullable=True)

    # 계층 구조 (Plant → Process → Line)
    plant_id = Column(
        "PLANT_ID",
        String(50),
        ForeignKey("PLANT_MASTER.PLANT_ID"),
        nullable=True,
        index=True,
        comment="Plant ID (계층 구조 1단계)",
    )
    process_id = Column(
        "PROCESS_ID",
        String(50),
        ForeignKey("PROCESS_MASTER.PROCESS_ID"),
        nullable=True,
        index=True,
        comment="공정 ID (계층 구조 2단계)",
    )
    line_id = Column(
        "LINE_ID",
        String(50),
        ForeignKey("LINE_MASTER.LINE_ID"),
        nullable=True,
        index=True,
        comment="Line ID (계층 구조 3단계)",
    )

    # 메타데이터
    metadata_json = Column("METADATA_JSON", JSON, nullable=True)

    # 시간 정보
    create_dt = Column(
        "CREATE_DT", DateTime, nullable=False, server_default=func.now()
    )
    update_dt = Column(
        "UPDATE_DT", DateTime, nullable=True, onupdate=func.now()
    )

    # 인덱스 정의 (조회 성능 향상)
    __table_args__ = (
        # 계층 구조 조회 최적화 인덱스
        Index("idx_dropdown_master_plant", "PLANT_ID"),
        Index("idx_dropdown_master_process", "PROCESS_ID"),
        Index("idx_dropdown_master_line", "LINE_ID"),
    )

    def __repr__(self):
        return (
            f"<DropdownMaster(dropdown_id='{self.dropdown_id}', "
            f"dropdown_name='{self.dropdown_name}', "
            f"plant_id='{self.plant_id}', process_id='{self.process_id}', "
            f"line_id='{self.line_id}')>"
        )

