# _*_ coding: utf-8 _*_
"""Master CRUD operations with database.
기준정보 마스터 테이블들 (PlantMaster, ProcessMaster, LineMaster, EquipmentGroupMaster) 관련 CRUD 작업
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.master_models import (
    EquipmentGroupMaster,
    LineMaster,
    PlantMaster,
    ProcessMaster,
)
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode

logger = logging.getLogger(__name__)


class PlantMasterCRUD:
    """PlantMaster 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_plant(
        self,
        plant_id: str,
        plant_code: str,
        plant_name: str,
        create_user: str,
        description: Optional[str] = None,
        display_order: Optional[int] = 0,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> PlantMaster:
        """공장 기준정보 생성"""
        try:
            plant = PlantMaster(
                plant_id=plant_id,
                plant_code=plant_code,
                plant_name=plant_name,
                description=description,
                display_order=display_order,
                is_active=is_active,
                metadata_json=metadata_json,
                create_user=create_user,
            )
            self.db.add(plant)
            self.db.commit()
            self.db.refresh(plant)
            return plant
        except Exception as e:
            self.db.rollback()
            logger.error(f"공장 기준정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plant(self, plant_id: str) -> Optional[PlantMaster]:
        """공장 기준정보 조회"""
        try:
            return (
                self.db.query(PlantMaster)
                .filter(PlantMaster.plant_id == plant_id)
                .filter(PlantMaster.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"공장 기준정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_all_plants(
        self, include_inactive: bool = False
    ) -> List[PlantMaster]:
        """모든 공장 기준정보 목록 조회"""
        try:
            query = self.db.query(PlantMaster)
            if not include_inactive:
                query = query.filter(PlantMaster.is_active.is_(True))
            return query.order_by(PlantMaster.display_order, PlantMaster.plant_code).all()
        except Exception as e:
            logger.error(f"공장 기준정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_plant(
        self, plant_id: str, update_user: Optional[str] = None, **kwargs
    ) -> bool:
        """공장 기준정보 업데이트"""
        try:
            plant = self.get_plant(plant_id)
            if plant:
                for key, value in kwargs.items():
                    if hasattr(plant, key):
                        setattr(plant, key, value)
                if update_user:
                    plant.update_user = update_user
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"공장 기준정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)


class ProcessMasterCRUD:
    """ProcessMaster 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_process(
        self,
        process_id: str,
        process_code: str,
        process_name: str,
        plant_id: str,
        create_user: str,
        description: Optional[str] = None,
        display_order: Optional[int] = 0,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> ProcessMaster:
        """공정 기준정보 생성"""
        try:
            process = ProcessMaster(
                process_id=process_id,
                process_code=process_code,
                process_name=process_name,
                plant_id=plant_id,
                description=description,
                display_order=display_order,
                is_active=is_active,
                metadata_json=metadata_json,
                create_user=create_user,
            )
            self.db.add(process)
            self.db.commit()
            self.db.refresh(process)
            return process
        except Exception as e:
            self.db.rollback()
            logger.error(f"공정 기준정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_process(self, process_id: str) -> Optional[ProcessMaster]:
        """공정 기준정보 조회"""
        try:
            return (
                self.db.query(ProcessMaster)
                .filter(ProcessMaster.process_id == process_id)
                .filter(ProcessMaster.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"공정 기준정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_processes_by_plant(
        self, plant_id: str, include_inactive: bool = False
    ) -> List[ProcessMaster]:
        """공장별 공정 기준정보 목록 조회"""
        try:
            query = self.db.query(ProcessMaster).filter(
                ProcessMaster.plant_id == plant_id
            )
            if not include_inactive:
                query = query.filter(ProcessMaster.is_active.is_(True))
            return query.order_by(ProcessMaster.display_order, ProcessMaster.process_code).all()
        except Exception as e:
            logger.error(f"공장별 공정 기준정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_process(
        self, process_id: str, update_user: Optional[str] = None, **kwargs
    ) -> bool:
        """공정 기준정보 업데이트"""
        try:
            process = self.get_process(process_id)
            if process:
                for key, value in kwargs.items():
                    if hasattr(process, key):
                        setattr(process, key, value)
                if update_user:
                    process.update_user = update_user
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"공정 기준정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)


class LineMasterCRUD:
    """LineMaster 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_line(
        self,
        line_id: str,
        line_code: str,
        line_name: str,
        process_id: str,
        create_user: str,
        description: Optional[str] = None,
        display_order: Optional[int] = 0,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> LineMaster:
        """라인 기준정보 생성"""
        try:
            line = LineMaster(
                line_id=line_id,
                line_code=line_code,
                line_name=line_name,
                process_id=process_id,
                description=description,
                display_order=display_order,
                is_active=is_active,
                metadata_json=metadata_json,
                create_user=create_user,
            )
            self.db.add(line)
            self.db.commit()
            self.db.refresh(line)
            return line
        except Exception as e:
            self.db.rollback()
            logger.error(f"라인 기준정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_line(self, line_id: str) -> Optional[LineMaster]:
        """라인 기준정보 조회"""
        try:
            return (
                self.db.query(LineMaster)
                .filter(LineMaster.line_id == line_id)
                .filter(LineMaster.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"라인 기준정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_lines_by_process(
        self, process_id: str, include_inactive: bool = False
    ) -> List[LineMaster]:
        """공정별 라인 기준정보 목록 조회"""
        try:
            query = self.db.query(LineMaster).filter(
                LineMaster.process_id == process_id
            )
            if not include_inactive:
                query = query.filter(LineMaster.is_active.is_(True))
            return query.order_by(LineMaster.display_order, LineMaster.line_code).all()
        except Exception as e:
            logger.error(f"공정별 라인 기준정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_line(
        self, line_id: str, update_user: Optional[str] = None, **kwargs
    ) -> bool:
        """라인 기준정보 업데이트"""
        try:
            line = self.get_line(line_id)
            if line:
                for key, value in kwargs.items():
                    if hasattr(line, key):
                        setattr(line, key, value)
                if update_user:
                    line.update_user = update_user
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"라인 기준정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)


class EquipmentGroupMasterCRUD:
    """EquipmentGroupMaster 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def create_equipment_group(
        self,
        equipment_group_id: str,
        equipment_group_code: str,
        equipment_group_name: str,
        line_id: str,
        create_user: str,
        description: Optional[str] = None,
        display_order: Optional[int] = 0,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> EquipmentGroupMaster:
        """장비 그룹 기준정보 생성"""
        try:
            equipment_group = EquipmentGroupMaster(
                equipment_group_id=equipment_group_id,
                equipment_group_code=equipment_group_code,
                equipment_group_name=equipment_group_name,
                line_id=line_id,
                description=description,
                display_order=display_order,
                is_active=is_active,
                metadata_json=metadata_json,
                create_user=create_user,
            )
            self.db.add(equipment_group)
            self.db.commit()
            self.db.refresh(equipment_group)
            return equipment_group
        except Exception as e:
            self.db.rollback()
            logger.error(f"장비 그룹 기준정보 생성 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_equipment_group(
        self, equipment_group_id: str
    ) -> Optional[EquipmentGroupMaster]:
        """장비 그룹 기준정보 조회"""
        try:
            return (
                self.db.query(EquipmentGroupMaster)
                .filter(
                    EquipmentGroupMaster.equipment_group_id == equipment_group_id
                )
                .filter(EquipmentGroupMaster.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"장비 그룹 기준정보 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_equipment_groups_by_line(
        self, line_id: str, include_inactive: bool = False
    ) -> List[EquipmentGroupMaster]:
        """라인별 장비 그룹 기준정보 목록 조회"""
        try:
            query = self.db.query(EquipmentGroupMaster).filter(
                EquipmentGroupMaster.line_id == line_id
            )
            if not include_inactive:
                query = query.filter(EquipmentGroupMaster.is_active.is_(True))
            return query.order_by(
                EquipmentGroupMaster.display_order,
                EquipmentGroupMaster.equipment_group_code
            ).all()
        except Exception as e:
            logger.error(f"라인별 장비 그룹 기준정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_equipment_group(
        self,
        equipment_group_id: str,
        update_user: Optional[str] = None,
        **kwargs,
    ) -> bool:
        """장비 그룹 기준정보 업데이트"""
        try:
            equipment_group = self.get_equipment_group(equipment_group_id)
            if equipment_group:
                for key, value in kwargs.items():
                    if hasattr(equipment_group, key):
                        setattr(equipment_group, key, value)
                if update_user:
                    equipment_group.update_user = update_user
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"장비 그룹 기준정보 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)


class MasterHierarchyCRUD:
    """계층 구조 전체를 효율적으로 조회하는 CRUD 클래스
    Plant -> Process -> Line -> EquipmentGroup 전체를 최적화된 쿼리로 조회
    """

    def __init__(self, db: Session):
        self.db = db

    def get_hierarchy_by_plant(
        self,
        plant_id: str,
        include_inactive: bool = False,
    ) -> Dict:
        """
        공장 기준으로 전체 계층 구조를 한 번에 조회 (최적화)
        
        Returns:
            {
                'plant': PlantMaster,
                'processes': [ProcessMaster],
                'lines': [LineMaster],
                'equipment_groups': [EquipmentGroupMaster]
            }
        """
        try:
            # 1. Plant 조회
            plant_query = self.db.query(PlantMaster).filter(
                PlantMaster.plant_id == plant_id
            )
            if not include_inactive:
                plant_query = plant_query.filter(PlantMaster.is_active.is_(True))
            plant = plant_query.first()

            if not plant:
                return {
                    "plant": None,
                    "processes": [],
                    "lines": [],
                    "equipment_groups": [],
                }

            # 2. 해당 Plant의 모든 Process를 한 번에 조회
            process_query = self.db.query(ProcessMaster).filter(
                ProcessMaster.plant_id == plant_id
            )
            if not include_inactive:
                process_query = process_query.filter(
                    ProcessMaster.is_active.is_(True)
                )
            processes = process_query.order_by(
                ProcessMaster.display_order, ProcessMaster.process_code
            ).all()

            if not processes:
                return {
                    "plant": plant,
                    "processes": [],
                    "lines": [],
                    "equipment_groups": [],
                }

            # 3. 모든 Process의 Line을 한 번에 조회 (IN 절 사용)
            process_ids = [p.process_id for p in processes]
            line_query = self.db.query(LineMaster).filter(
                LineMaster.process_id.in_(process_ids)
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            lines = line_query.order_by(
                LineMaster.display_order, LineMaster.line_code
            ).all()

            if not lines:
                return {
                    "plant": plant,
                    "processes": processes,
                    "lines": [],
                    "equipment_groups": [],
                }

            # 4. 모든 Line의 EquipmentGroup을 한 번에 조회 (IN 절 사용)
            line_ids = [l.line_id for l in lines]
            equipment_query = self.db.query(EquipmentGroupMaster).filter(
                EquipmentGroupMaster.line_id.in_(line_ids)
            )
            if not include_inactive:
                equipment_query = equipment_query.filter(
                    EquipmentGroupMaster.is_active.is_(True)
                )
            equipment_groups = equipment_query.order_by(
                EquipmentGroupMaster.display_order,
                EquipmentGroupMaster.equipment_group_code,
            ).all()

            return {
                "plant": plant,
                "processes": processes,
                "lines": lines,
                "equipment_groups": equipment_groups,
            }
        except Exception as e:
            logger.error(f"계층 구조 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_hierarchy_by_process(
        self,
        process_id: str,
        include_inactive: bool = False,
    ) -> Dict:
        """
        공정 기준으로 하위 계층 구조를 한 번에 조회 (최적화)
        
        Returns:
            {
                'process': ProcessMaster,
                'lines': [LineMaster],
                'equipment_groups': [EquipmentGroupMaster]
            }
        """
        try:
            # 1. Process 조회
            process_query = self.db.query(ProcessMaster).filter(
                ProcessMaster.process_id == process_id
            )
            if not include_inactive:
                process_query = process_query.filter(
                    ProcessMaster.is_active.is_(True)
                )
            process = process_query.first()

            if not process:
                return {
                    "process": None,
                    "lines": [],
                    "equipment_groups": [],
                }

            # 2. 해당 Process의 모든 Line을 한 번에 조회
            line_query = self.db.query(LineMaster).filter(
                LineMaster.process_id == process_id
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            lines = line_query.order_by(
                LineMaster.display_order, LineMaster.line_code
            ).all()

            if not lines:
                return {
                    "process": process,
                    "lines": [],
                    "equipment_groups": [],
                }

            # 3. 모든 Line의 EquipmentGroup을 한 번에 조회 (IN 절 사용)
            line_ids = [l.line_id for l in lines]
            equipment_query = self.db.query(EquipmentGroupMaster).filter(
                EquipmentGroupMaster.line_id.in_(line_ids)
            )
            if not include_inactive:
                equipment_query = equipment_query.filter(
                    EquipmentGroupMaster.is_active.is_(True)
                )
            equipment_groups = equipment_query.order_by(
                EquipmentGroupMaster.display_order,
                EquipmentGroupMaster.equipment_group_code,
            ).all()

            return {
                "process": process,
                "lines": lines,
                "equipment_groups": equipment_groups,
            }
        except Exception as e:
            logger.error(f"계층 구조 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_hierarchy_by_line(
        self,
        line_id: str,
        include_inactive: bool = False,
    ) -> Dict:
        """
        라인 기준으로 하위 계층 구조를 한 번에 조회 (최적화)
        
        Returns:
            {
                'line': LineMaster,
                'equipment_groups': [EquipmentGroupMaster]
            }
        """
        try:
            # 1. Line 조회
            line_query = self.db.query(LineMaster).filter(
                LineMaster.line_id == line_id
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            line = line_query.first()

            if not line:
                return {
                    "line": None,
                    "equipment_groups": [],
                }

            # 2. 해당 Line의 모든 EquipmentGroup을 한 번에 조회
            equipment_query = self.db.query(EquipmentGroupMaster).filter(
                EquipmentGroupMaster.line_id == line_id
            )
            if not include_inactive:
                equipment_query = equipment_query.filter(
                    EquipmentGroupMaster.is_active.is_(True)
                )
            equipment_groups = equipment_query.order_by(
                EquipmentGroupMaster.display_order,
                EquipmentGroupMaster.equipment_group_code,
            ).all()

            return {
                "line": line,
                "equipment_groups": equipment_groups,
            }
        except Exception as e:
            logger.error(f"계층 구조 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_all_hierarchies(
        self,
        plant_ids: Optional[List[str]] = None,
        include_inactive: bool = False,
    ) -> List[Dict]:
        """
        여러 공장의 전체 계층 구조를 한 번에 조회 (최적화)
        
        Args:
            plant_ids: 조회할 공장 ID 리스트 (None이면 모든 공장)
            include_inactive: 비활성 항목 포함 여부
            
        Returns:
            [
                {
                    'plant': PlantMaster,
                    'processes': [ProcessMaster],
                    'lines': [LineMaster],
                    'equipment_groups': [EquipmentGroupMaster]
                },
                ...
            ]
        """
        try:
            # 1. Plant 조회
            plant_query = self.db.query(PlantMaster)
            if plant_ids:
                plant_query = plant_query.filter(PlantMaster.plant_id.in_(plant_ids))
            if not include_inactive:
                plant_query = plant_query.filter(PlantMaster.is_active.is_(True))
            plants = plant_query.order_by(
                PlantMaster.display_order, PlantMaster.plant_code
            ).all()

            if not plants:
                return []

            plant_id_list = [p.plant_id for p in plants]

            # 2. 모든 Plant의 Process를 한 번에 조회 (IN 절 사용)
            process_query = self.db.query(ProcessMaster).filter(
                ProcessMaster.plant_id.in_(plant_id_list)
            )
            if not include_inactive:
                process_query = process_query.filter(
                    ProcessMaster.is_active.is_(True)
                )
            all_processes = process_query.order_by(
                ProcessMaster.display_order, ProcessMaster.process_code
            ).all()

            # Process를 plant_id로 그룹화
            processes_by_plant = {}
            for process in all_processes:
                if process.plant_id not in processes_by_plant:
                    processes_by_plant[process.plant_id] = []
                processes_by_plant[process.plant_id].append(process)

            if not all_processes:
                return [
                    {"plant": p, "processes": [], "lines": [], "equipment_groups": []}
                    for p in plants
                ]

            # 3. 모든 Process의 Line을 한 번에 조회 (IN 절 사용)
            process_id_list = [p.process_id for p in all_processes]
            line_query = self.db.query(LineMaster).filter(
                LineMaster.process_id.in_(process_id_list)
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            all_lines = line_query.order_by(
                LineMaster.display_order, LineMaster.line_code
            ).all()

            # Line을 process_id로 그룹화
            lines_by_process = {}
            for line in all_lines:
                if line.process_id not in lines_by_process:
                    lines_by_process[line.process_id] = []
                lines_by_process[line.process_id].append(line)

            # 4. 모든 Line의 EquipmentGroup을 한 번에 조회 (IN 절 사용)
            line_id_list = [l.line_id for l in all_lines] if all_lines else []
            equipment_groups = []
            if line_id_list:
                equipment_query = self.db.query(EquipmentGroupMaster).filter(
                    EquipmentGroupMaster.line_id.in_(line_id_list)
                )
                if not include_inactive:
                    equipment_query = equipment_query.filter(
                        EquipmentGroupMaster.is_active.is_(True)
                    )
                equipment_groups = equipment_query.order_by(
                    EquipmentGroupMaster.display_order,
                    EquipmentGroupMaster.equipment_group_code,
                ).all()

            # EquipmentGroup을 line_id로 그룹화
            equipment_by_line = {}
            for equipment in equipment_groups:
                if equipment.line_id not in equipment_by_line:
                    equipment_by_line[equipment.line_id] = []
                equipment_by_line[equipment.line_id].append(equipment)

            # 결과 구성
            result = []
            for plant in plants:
                processes = processes_by_plant.get(plant.plant_id, [])
                lines = []
                equipment_groups_for_plant = []

                for process in processes:
                    process_lines = lines_by_process.get(process.process_id, [])
                    lines.extend(process_lines)

                    for line in process_lines:
                        line_equipment = equipment_by_line.get(line.line_id, [])
                        equipment_groups_for_plant.extend(line_equipment)

                result.append(
                    {
                        "plant": plant,
                        "processes": processes,
                        "lines": lines,
                        "equipment_groups": equipment_groups_for_plant,
                    }
                )

            return result
        except Exception as e:
            logger.error(f"전체 계층 구조 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_all_active_hierarchies(self) -> List[Dict]:
        """
        모든 활성 Plant의 전체 계층 구조를 한 번에 조회 (최적화)
        plant_id를 모를 때 사용하는 편의 메서드
        
        Returns:
            [
                {
                    'plant': PlantMaster,
                    'processes': [ProcessMaster],
                    'lines': [LineMaster],
                    'equipment_groups': [EquipmentGroupMaster]
                },
                ...
            ]
        """
        return self.get_all_hierarchies(plant_ids=None, include_inactive=False)

