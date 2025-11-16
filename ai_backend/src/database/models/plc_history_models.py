# _*_ coding: utf-8 _*_
"""
PLC 계층 구조 변경 이력 모델 정의
PLC의 계층 구조가 여러 번 변경될 때 이력을 추적하기 위한 테이블
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func

from src.database.base import Base


class PLCHierarchyHistory(Base):
    """PLC 계층 구조 변경 이력 테이블"""

    __tablename__ = "PLC_HIERARCHY_HISTORY"

    # 기본 정보
    history_id = Column("HISTORY_ID", String(50), primary_key=True)
    plc_uuid = Column(
        "PLC_UUID",
        String(50),
        ForeignKey("PLC.PLC_UUID"),
        nullable=False,
        index=True,
        comment="PLC UUID (PLC 테이블 참조)"
    )

    # 변경 전 계층 구조 스냅샷 (JSON, ID만 저장)
    # 형식: {
    #   "plant_id": "...",
    #   "process_id": "...",
    #   "line_id": "...",
    #   "equipment_group_id": "..."
    # }
    # code, name은 master 테이블 조인으로 조회
    previous_hierarchy = Column("PREVIOUS_HIERARCHY", JSON, nullable=True)

    # 변경 후 계층 구조 스냅샷 (JSON, ID만 저장)
    # 형식: {
    #   "plant_id": "...",
    #   "process_id": "...",
    #   "line_id": "...",
    #   "equipment_group_id": "..."
    # }
    # code, name은 master 테이블 조인으로 조회
    new_hierarchy = Column("NEW_HIERARCHY", JSON, nullable=True)

    # 변경 사유
    change_reason = Column("CHANGE_REASON", String(500), nullable=True)

    # 변경 정보
    changed_at = Column(
        "CHANGED_AT", DateTime, nullable=False, server_default=func.now()
    )
    changed_by = Column("CHANGED_BY", String(50), nullable=False)

    # 변경 순서 (같은 PLC의 변경 이력을 시간순으로 정렬)
    change_sequence = Column("CHANGE_SEQUENCE", Integer, nullable=False, default=1)

    def __repr__(self):
        return (
            f"<PLCHierarchyHistory(history_id='{self.history_id}', "
            f"plc_uuid='{self.plc_uuid}', "
            f"changed_at='{self.changed_at}')>"
        )

