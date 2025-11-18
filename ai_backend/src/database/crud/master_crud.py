# _*_ coding: utf-8 _*_
"""Master CRUD operations with database.
기준정보 마스터 테이블들 (PlantMaster, ProcessMaster, LineMaster) 관련 CRUD 작업
"""
import logging
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.master_models import (
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
        plant_name: str,
        create_user: str,
        description: Optional[str] = None,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> PlantMaster:
        """공장 기준정보 생성"""
        try:
            plant = PlantMaster(
                plant_id=plant_id,
                plant_name=plant_name,
                description=description,
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
        self,
        include_inactive: bool = False,
        sort_by: str = "plant_name",
        sort_order: str = "asc",
    ) -> List[PlantMaster]:
        """모든 공장 기준정보 목록 조회"""
        try:
            query = self.db.query(PlantMaster)
            if not include_inactive:
                query = query.filter(PlantMaster.is_active.is_(True))
            
            # 정렬
            sort_column = getattr(PlantMaster, sort_by, PlantMaster.plant_name)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            return query.all()
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
        process_name: str,
        create_user: str,
        description: Optional[str] = None,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> ProcessMaster:
        """공정 기준정보 생성"""
        try:
            process = ProcessMaster(
                process_id=process_id,
                process_name=process_name,
                description=description,
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

    def get_all_processes(
        self,
        include_inactive: bool = False,
        sort_by: str = "process_name",
        sort_order: str = "asc",
    ) -> List[ProcessMaster]:
        """모든 공정 기준정보 목록 조회 (Plant와 무관하게 전체 조회)"""
        try:
            query = self.db.query(ProcessMaster)
            if not include_inactive:
                query = query.filter(ProcessMaster.is_active.is_(True))
            
            # 정렬
            sort_column = getattr(
                ProcessMaster, sort_by, ProcessMaster.process_name
            )
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            return query.all()
        except Exception as e:
            logger.error(f"공정 기준정보 목록 조회 실패: {str(e)}")
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
        line_name: str,
        process_id: str,
        create_user: str,
        description: Optional[str] = None,
        is_active: bool = True,
        metadata_json: Optional[Dict] = None,
    ) -> LineMaster:
        """라인 기준정보 생성"""
        try:
            line = LineMaster(
                line_id=line_id,
                line_name=line_name,
                process_id=process_id,
                description=description,
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
        self,
        process_id: str,
        include_inactive: bool = False,
        sort_by: str = "line_name",
        sort_order: str = "asc",
    ) -> List[LineMaster]:
        """공정별 라인 기준정보 목록 조회"""
        try:
            query = self.db.query(LineMaster).filter(
                LineMaster.process_id == process_id
            )
            if not include_inactive:
                query = query.filter(LineMaster.is_active.is_(True))
            
            # 정렬
            sort_column = getattr(LineMaster, sort_by, LineMaster.line_name)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)
            
            return query.all()
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


class MasterHierarchyCRUD:
    """계층 구조 전체를 효율적으로 조회하는 CRUD 클래스
    Plant -> Process -> Line 전체를 최적화된 쿼리로 조회
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
                'lines': [LineMaster]
            }
        """
        try:
            # 1. Plant 조회
            plant_query = self.db.query(PlantMaster).filter(
                PlantMaster.plant_id == plant_id
            )
            if not include_inactive:
                plant_query = plant_query.filter(
                    PlantMaster.is_active.is_(True)
                )
            plant = plant_query.first()

            if not plant:
                return {
                    "plant": None,
                    "processes": [],
                    "lines": [],
                }

            # 2. 모든 Process 조회 (Plant와 무관하게 전체 조회)
            process_query = self.db.query(ProcessMaster)
            if not include_inactive:
                process_query = process_query.filter(
                    ProcessMaster.is_active.is_(True)
                )
            processes = process_query.order_by(
                ProcessMaster.process_name
            ).all()

            if not processes:
                return {
                    "plant": plant,
                    "processes": [],
                    "lines": [],
                }

            # 3. 모든 Process의 Line을 한 번에 조회 (IN 절 사용)
            process_ids = [p.process_id for p in processes]
            line_query = self.db.query(LineMaster).filter(
                LineMaster.process_id.in_(process_ids)
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            lines = line_query.order_by(
                LineMaster.line_name
            ).all()

            return {
                "plant": plant,
                "processes": processes,
                "lines": lines,
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
                'lines': [LineMaster]
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
                }

            # 2. 해당 Process의 모든 Line을 한 번에 조회
            line_query = self.db.query(LineMaster).filter(
                LineMaster.process_id == process_id
            )
            if not include_inactive:
                line_query = line_query.filter(LineMaster.is_active.is_(True))
            lines = line_query.order_by(
                LineMaster.line_name
            ).all()

            return {
                "process": process,
                "lines": lines,
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
                'line': LineMaster
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
                }

            return {
                "line": line,
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
                plant_query = plant_query.filter(
                    PlantMaster.plant_id.in_(plant_ids)
                )
            if not include_inactive:
                plant_query = plant_query.filter(
                    PlantMaster.is_active.is_(True)
                )
            plants = plant_query.order_by(
                PlantMaster.plant_name
            ).all()

            if not plants:
                return []

            # 2. 모든 Process 조회 (Plant와 무관하게 전체 조회)
            process_query = self.db.query(ProcessMaster)
            if not include_inactive:
                process_query = process_query.filter(
                    ProcessMaster.is_active.is_(True)
                )
            all_processes = process_query.order_by(
                ProcessMaster.process_name
            ).all()

            # Process는 모든 Plant에서 공통으로 사용되므로 모든 Plant에 동일하게 표시
            processes_by_plant = {}
            for plant in plants:
                processes_by_plant[plant.plant_id] = all_processes

            if not all_processes:
                return [
                    {"plant": p, "processes": [], "lines": []}
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
                LineMaster.line_name
            ).all()

            # Line을 process_id로 그룹화
            lines_by_process = {}
            for line in all_lines:
                if line.process_id not in lines_by_process:
                    lines_by_process[line.process_id] = []
                lines_by_process[line.process_id].append(line)

            # 결과 구성
            result = []
            for plant in plants:
                # 모든 Process는 모든 Plant에서 공통으로 사용
                processes = processes_by_plant.get(plant.plant_id, [])
                lines = []

                for process in processes:
                    process_lines = lines_by_process.get(
                        process.process_id, []
                    )
                    lines.extend(process_lines)

                result.append(
                    {
                        "plant": plant,
                        "processes": processes,
                        "lines": lines,
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

    def get_all_masters_for_dropdown(self) -> Dict:
        """
        드롭다운용 전체 마스터 데이터 조회 (Plant, Process, Line)
        
        프론트엔드 연쇄 드롭다운 구현에 최적화된 구조로 반환:
        - plants: Plant 목록 (첫 번째 드롭다운)
        - processesByPlant: Plant ID → Process 목록 맵 (두 번째 드롭다운)
        - linesByProcess: Process ID → Line 목록 맵 (세 번째 드롭다운)
        
        프론트엔드에서 사용하기 쉬운 구조:
        - Plant 선택: response.plants 사용
        - Process 필터링: response.processesByPlant[plantId] 사용
        - Line 필터링: response.linesByProcess[processId] 사용
        
        Returns:
            Dict: {
                "plants": [
                    {"id": "...", "code": "...", "name": "..."}, ...
                ],
                "processesByPlant": {
                    "plant_001": [
                        {"id": "...", "code": "...", "name": "..."}, ...
                    ],
                    ...
                },
                "linesByProcess": {
                    "process_001": [
                        {"id": "...", "code": "...", "name": "..."}, ...
                    ],
                    ...
                }
            }
        """
        try:
            # 1. 모든 Plant 조회
            plants = (
                self.db.query(PlantMaster)
                .filter(PlantMaster.is_active.is_(True))
                .order_by(PlantMaster.plant_name)
                .all()
            )
            
            if not plants:
                return {
                    "plants": [],
                    "processesByPlant": {},
                    "linesByProcess": {},
                }
            
            plant_id_list = [p.plant_id for p in plants]
            
            # 2. 모든 Process 조회 (Plant와 무관하게 전체 조회)
            processes = (
                self.db.query(ProcessMaster)
                .filter(ProcessMaster.is_active.is_(True))
                .order_by(ProcessMaster.process_name)
                .all()
            )
            
            # Process는 모든 Plant에서 공통으로 사용되므로 모든 Plant에 동일하게 표시
            processes_by_plant = {}
            for plant in plants:
                processes_by_plant[plant.plant_id] = [
                    {
                        "id": process.process_id,
                        "name": process.process_name,
                    }
                    for process in processes
                ]
            
            # 3. 모든 Line 조회
            process_id_list = [p.process_id for p in processes]
            lines = []
            if process_id_list:
                lines = (
                    self.db.query(LineMaster)
                    .filter(LineMaster.is_active.is_(True))
                    .filter(LineMaster.process_id.in_(process_id_list))
                    .order_by(LineMaster.line_name)
                    .all()
                )
            
            # Line을 process_id로 그룹화
            lines_by_process = {}
            for line in lines:
                if line.process_id not in lines_by_process:
                    lines_by_process[line.process_id] = []
                lines_by_process[line.process_id].append({
                    "id": line.line_id,
                    "name": line.line_name,
                })
            
            # 평면 구조로 변환
            return {
                "plants": [
                    {
                        "id": p.plant_id,
                        "name": p.plant_name,
                    }
                    for p in plants
                ],
                "processesByPlant": processes_by_plant,
                "linesByProcess": lines_by_process,
            }
        except Exception as e:
            logger.error(f"드롭다운용 마스터 데이터 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_masters_for_mapping_dropdown(
        self, accessible_process_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        PLC-PGM 매핑 화면용 드롭다운 데이터 조회 (권한 기반 공정 필터링)
        
        사용자 권한에 따라 접근 가능한 공정만 포함하여 반환합니다.
        
        Args:
            accessible_process_ids: 접근 가능한 공정 ID 리스트 (None이면 모든 공정)
        
        Returns:
            Dict: {
                "plants": [...],
                "processesByPlant": {...},
                "linesByProcess": {...}
            }
        """
        try:
            # 1. 모든 Plant 조회
            plants = (
                self.db.query(PlantMaster)
                .filter(PlantMaster.is_active.is_(True))
                .order_by(PlantMaster.plant_name)
                .all()
            )
            
            if not plants:
                return {
                    "plants": [],
                    "processesByPlant": {},
                    "linesByProcess": {},
                }
            
            plant_id_list = [p.plant_id for p in plants]
            
            # 2. 공정 조회 (권한 필터링 적용, Plant와 무관하게 전체 조회)
            process_query = (
                self.db.query(ProcessMaster)
                .filter(ProcessMaster.is_active.is_(True))
            )
            
            # 접근 가능한 공정만 필터링
            if accessible_process_ids:
                process_query = process_query.filter(
                    ProcessMaster.process_id.in_(accessible_process_ids)
                )
            
            processes = process_query.order_by(ProcessMaster.process_name).all()
            
            # Process는 모든 Plant에서 공통으로 사용되므로 모든 Plant에 동일하게 표시
            processes_by_plant = {}
            for plant in plants:
                processes_by_plant[plant.plant_id] = [
                    {
                        "id": process.process_id,
                        "name": process.process_name,
                    }
                    for process in processes
                ]
            
            # 3. Line 조회 (필터링된 공정에 대한 Line만)
            process_id_list = [p.process_id for p in processes]
            lines = []
            if process_id_list:
                lines = (
                    self.db.query(LineMaster)
                    .filter(LineMaster.is_active.is_(True))
                    .filter(LineMaster.process_id.in_(process_id_list))
                    .order_by(LineMaster.line_name)
                    .all()
                )
            
            # Line을 process_id로 그룹화
            lines_by_process = {}
            for line in lines:
                if line.process_id not in lines_by_process:
                    lines_by_process[line.process_id] = []
                lines_by_process[line.process_id].append({
                    "id": line.line_id,
                    "name": line.line_name,
                })
            
            return {
                "plants": [
                    {
                        "id": p.plant_id,
                        "name": p.plant_name,
                    }
                    for p in plants
                ],
                "processesByPlant": processes_by_plant,
                "linesByProcess": lines_by_process,
            }
        except Exception as e:
            logger.error(
                f"매핑 화면용 드롭다운 데이터 조회 실패: {str(e)}"
            )
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

