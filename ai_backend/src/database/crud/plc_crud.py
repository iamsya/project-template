# _*_ coding: utf-8 _*_
"""PLC CRUD operations with database."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.plc_models import PLC
from src.database.models.plc_history_models import PLCHierarchyHistory
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen

logger = logging.getLogger(__name__)


class PLCCRUD:
    """PLC 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def get_plc(self, plc_id: str) -> Optional[PLC]:
        """PLC 조회 (ID로)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.id == plc_id)
                .filter(PLC.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plc_by_plc_id(self, plc_id: str) -> Optional[PLC]:
        """PLC 조회 (plc_id로)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.plc_id == plc_id)
                .filter(PLC.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"PLC 조회 실패 (plc_id): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plc_by_uuid(self, plc_uuid: str) -> Optional[PLC]:
        """PLC 조회 (plc_uuid로)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.plc_uuid == plc_uuid)
                .filter(PLC.is_active.is_(True))
                .first()
            )
        except Exception as e:
            logger.error(f"PLC 조회 실패 (plc_uuid): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_program_id_from_plc_uuid(self, plc_uuid: str) -> Optional[str]:
        """
        PLC UUID로 매핑된 Program ID 조회
        
        Args:
            plc_uuid: PLC UUID
            
        Returns:
            Optional[str]: Program ID (없으면 None)
        """
        try:
            plc = self.get_plc_by_uuid(plc_uuid)
            if plc and plc.program_id:
                logger.info(
                    "PLC UUID %s의 program_id 조회: %s", plc_uuid, plc.program_id
                )
                return plc.program_id
            else:
                logger.warning(
                    "PLC UUID %s를 찾을 수 없거나 program_id가 없습니다.",
                    plc_uuid,
                )
                return None
        except Exception as e:
            logger.error(
                "PLC UUID %s의 program_id 조회 실패: %s", plc_uuid, str(e)
            )
            return None

    def create_plc_hierarchy_snapshot(
        self, plc_uuid: str
    ) -> Optional[Dict]:
        """
        PLC의 계층 구조 스냅샷 생성 (채팅 메시지 저장용)
        
        화면 계층: Plant → 공정 → Line → 장비 그룹 → 호기 → PLC
        스냅샷 저장 항목: plant, 공정, line, 호기, plc명, 등록일시
        
        Args:
            plc_uuid: PLC UUID
            
        Returns:
            Optional[Dict]: 계층 구조 스냅샷 JSON
                {
                    "plant_id": "...",
                    "plant_name": "...",
                    "process_id": "...",
                    "process_name": "...",
                    "line_id": "...",
                    "line_name": "...",
                    "unit": "...",  # 호기
                    "plc_name": "...",
                    "plc_id": "...",
                    "create_dt": "2025-10-31 18:39:00"  # 등록일시
                }
        """
        try:
            plc = self.get_plc_by_uuid(plc_uuid)
            if not plc:
                logger.warning("PLC UUID %s를 찾을 수 없습니다.", plc_uuid)
                return None

            # 계층 구조 정보 조회 (ID와 이름 포함)
            # PLC 테이블의 현재 hierarchy 사용 (plant_id, process_id, line_id)
            hierarchy_ids = {
                "plant_id": plc.plant_id,
                "process_id": plc.process_id,
                "line_id": plc.line_id,
            }
            hierarchy = self._get_hierarchy_with_names(hierarchy_ids)

            # 스냅샷 생성
            snapshot = {
                "plc_uuid": plc.plc_uuid,
                "plc_id": plc.plc_id,
                "plc_name": plc.plc_name,
                "unit": plc.unit,
            }

            # Plant 정보
            if hierarchy and hierarchy.get("plant"):
                plant = hierarchy["plant"]
                snapshot["plant_id"] = plant.get("id")
                snapshot["plant_name"] = plant.get("name")
                snapshot["plant_code"] = plant.get("code")

            # Process 정보
            if hierarchy and hierarchy.get("process"):
                process = hierarchy["process"]
                snapshot["process_id"] = process.get("id")
                snapshot["process_name"] = process.get("name")
                snapshot["process_code"] = process.get("code")

            # Line 정보
            if hierarchy and hierarchy.get("line"):
                line = hierarchy["line"]
                snapshot["line_id"] = line.get("id")
                snapshot["line_name"] = line.get("name")
                snapshot["line_code"] = line.get("code")

            # 등록일시 (문자열 형식으로 저장)
            if plc.create_dt:
                snapshot["create_dt"] = plc.create_dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

            logger.info("PLC UUID %s의 계층 구조 스냅샷 생성 완료", plc_uuid)
            return snapshot

        except Exception as e:
            logger.error(
                "PLC UUID %s의 계층 구조 스냅샷 생성 실패: %s",
                plc_uuid,
                str(e),
            )
            return None

    def _get_current_hierarchy_snapshot(self, plc: PLC) -> Optional[Dict]:
        """
        PLC의 현재 계층 구조 스냅샷 ID들을 딕셔너리로 반환
        
        Returns:
            {
                "plant_id": "...",
                "process_id": "...",
                "line_id": "...",
            }
        """
        snapshot = {}
        if plc.plant_id_snapshot:
            snapshot["plant_id"] = plc.plant_id_snapshot
        if plc.process_id_snapshot:
            snapshot["process_id"] = plc.process_id_snapshot
        if plc.line_id_snapshot:
            snapshot["line_id"] = plc.line_id_snapshot

        return snapshot if snapshot else None

    def update_plc_hierarchy(
        self,
        plc_id: str,
        plant_id: Optional[str] = None,
        process_id: Optional[str] = None,
        line_id: Optional[str] = None,
        update_user: str = "system",
        change_reason: Optional[str] = None,
    ) -> bool:
        """
        PLC 계층 구조 업데이트 (변경 이력 자동 저장)
        
        Args:
            plc_id: PLC ID
            plant_id: 새로운 Plant ID
            process_id: 새로운 Process ID
            line_id: 새로운 Line ID
            update_user: 수정 사용자
            change_reason: 변경 사유
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            plc = self.get_plc(plc_id)
            if not plc:
                return False

            # 변경 전 계층 구조 스냅샷 저장
            previous_hierarchy = self._get_current_hierarchy_snapshot(plc)

            # Master 테이블에서 최신 정보 조회
            from src.database.crud.master_crud import (
                LineMasterCRUD,
                PlantMasterCRUD,
                ProcessMasterCRUD,
            )

            plant_crud = PlantMasterCRUD(self.db)
            process_crud = ProcessMasterCRUD(self.db)
            line_crud = LineMasterCRUD(self.db)

            # 새로운 계층 구조 정보 조회 및 스냅샷 업데이트
            new_snapshot = {}
            new_current = {}

            if plant_id:
                plant = plant_crud.get_plant(plant_id)
                if plant:
                    new_snapshot["plant_id"] = plant.plant_id
                    new_current["plant_id"] = plant_id

            if process_id:
                process = process_crud.get_process(process_id)
                if process:
                    new_snapshot["process_id"] = process.process_id
                    new_current["process_id"] = process_id

            if line_id:
                line = line_crud.get_line(line_id)
                if line:
                    new_snapshot["line_id"] = line.line_id
                    new_current["line_id"] = line_id

            # 기존 스냅샷과 병합 (변경되지 않은 레벨은 유지)
            if previous_hierarchy:
                for key in ["plant_id", "process_id", "line_id"]:
                    if key not in new_snapshot:
                        new_snapshot[key] = previous_hierarchy.get(key)

            # PLC 스냅샷 및 current 업데이트
            plc.plant_id_snapshot = new_snapshot.get("plant_id")
            plc.process_id_snapshot = new_snapshot.get("process_id")
            plc.line_id_snapshot = new_snapshot.get("line_id")

            # 계층 구조가 실제로 변경되었는지 확인
            if previous_hierarchy != new_snapshot:
                # 변경 이력 저장 (ID만 저장)
                self._save_hierarchy_history(
                    plc_id=plc_id,
                    previous_hierarchy=previous_hierarchy,
                    new_hierarchy=new_snapshot,
                    changed_by=update_user,
                    change_reason=change_reason,
                )

            # PLC 업데이트
            plc.update_dt = datetime.now()
            plc.update_user = update_user
            self.db.commit()

            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 계층 구조 업데이트 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def _save_hierarchy_history(
        self,
        plc_id: str,
        previous_hierarchy: Optional[Dict],
        new_hierarchy: Optional[Dict],
        changed_by: str,
        change_reason: Optional[str] = None,
    ):
        """PLC 계층 구조 변경 이력 저장"""
        try:
            # 이전 변경 이력의 최대 sequence 조회
            max_sequence = (
                self.db.query(PLCHierarchyHistory)
                .filter(PLCHierarchyHistory.plc_id == plc_id)
                .order_by(desc(PLCHierarchyHistory.change_sequence))
                .first()
            )
            next_sequence = (max_sequence.change_sequence + 1) if max_sequence else 1

            history = PLCHierarchyHistory(
                history_id=gen(),
                plc_id=plc_id,
                previous_hierarchy=previous_hierarchy,
                new_hierarchy=new_hierarchy,
                change_reason=change_reason,
                changed_by=changed_by,
                change_sequence=next_sequence,
                changed_at=datetime.now(),
            )

            self.db.add(history)
            # commit은 호출하는 쪽에서 처리
        except Exception as e:
            logger.error(f"PLC 계층 구조 변경 이력 저장 실패: {str(e)}")
            # 이력 저장 실패해도 PLC 업데이트는 계속 진행

    def get_plc_hierarchy_history(
        self, plc_id: str, limit: int = 10
    ) -> List[PLCHierarchyHistory]:
        """
        PLC 계층 구조 변경 이력 조회
        
        Args:
            plc_id: PLC ID
            limit: 조회할 이력 개수
            
        Returns:
            List[PLCHierarchyHistory]: 변경 이력 목록 (최신순)
        """
        try:
            return (
                self.db.query(PLCHierarchyHistory)
                .filter(PLCHierarchyHistory.plc_id == plc_id)
                .order_by(desc(PLCHierarchyHistory.changed_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"PLC 계층 구조 변경 이력 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plc_hierarchy_at_time(
        self, plc_id: str, target_time: datetime
    ) -> Optional[Dict]:
        """
        특정 시점의 PLC 계층 구조 조회
        
        Args:
            plc_id: PLC ID
            target_time: 조회할 시점
            
        Returns:
            Optional[Dict]: 해당 시점의 계층 구조 스냅샷
        """
        try:
            # target_time 이전의 가장 최근 변경 이력 조회
            history = (
                self.db.query(PLCHierarchyHistory)
                .filter(PLCHierarchyHistory.plc_id == plc_id)
                .filter(PLCHierarchyHistory.changed_at <= target_time)
                .order_by(desc(PLCHierarchyHistory.changed_at))
                .first()
            )

            if history:
                # 변경 이력이 있으면 해당 시점의 계층 구조 반환
                return history.new_hierarchy

            # 변경 이력이 없으면 현재 PLC의 스냅샷 반환
            plc = self.get_plc(plc_id)
            if plc:
                return self._get_current_hierarchy_snapshot(plc)

            return None
        except Exception as e:
            logger.error(f"특정 시점의 PLC 계층 구조 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def _get_hierarchy_with_names(
        self, snapshot_ids: Optional[Dict]
    ) -> Optional[Dict]:
        """
        스냅샷 ID들로부터 master 테이블 조인하여 계층 구조 정보 조회
        
        Returns:
            Dict: 계층 구조 정보 (id, code, name 포함)
        """
        if not snapshot_ids:
            return None

        try:
            from src.database.crud.master_crud import (
                LineMasterCRUD,
                PlantMasterCRUD,
                ProcessMasterCRUD,
            )

            plant_crud = PlantMasterCRUD(self.db)
            process_crud = ProcessMasterCRUD(self.db)
            line_crud = LineMasterCRUD(self.db)

            hierarchy = {}

            if snapshot_ids.get("plant_id"):
                plant = plant_crud.get_plant(snapshot_ids["plant_id"])
                if plant:
                    hierarchy["plant"] = {
                        "id": plant.plant_id,
                        "code": plant.plant_code,
                        "name": plant.plant_name,
                    }

            if snapshot_ids.get("process_id"):
                process = process_crud.get_process(snapshot_ids["process_id"])
                if process:
                    hierarchy["process"] = {
                        "id": process.process_id,
                        "code": process.process_code,
                        "name": process.process_name,
                    }

            if snapshot_ids.get("line_id"):
                line = line_crud.get_line(snapshot_ids["line_id"])
                if line:
                    hierarchy["line"] = {
                        "id": line.line_id,
                        "code": line.line_code,
                        "name": line.line_name,
                    }


            return hierarchy if hierarchy else None

        except Exception as e:
            logger.warning(f"스냅샷 ID로 계층 구조 조회 실패: {str(e)}")
            return None

    def get_plcs(
        self,
        plant_id: Optional[str] = None,
        process_id: Optional[str] = None,
        line_id: Optional[str] = None,
        plc_id: Optional[str] = None,
        plc_name: Optional[str] = None,
        program_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "plc_id",
        sort_order: str = "asc",
    ) -> tuple[List[PLC], int]:
        """
        PLC 목록 조회 (검색, 필터링, 페이지네이션, 정렬)

        Args:
            plant_id: Plant ID로 필터링
            process_id: Process ID로 필터링
            line_id: Line ID로 필터링
            plc_id: PLC ID로 검색 (부분 일치)
            plc_name: PLC 이름으로 검색 (부분 일치)
            program_name: PGM명으로 필터링 (부분 일치)
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지당 항목 수
            sort_by: 정렬 기준 (plc_id, plc_name, create_dt)
            sort_order: 정렬 순서 (asc, desc)

        Returns:
            Tuple[List[PLC], int]: (PLC 목록, 전체 개수)
        """
        try:
            from src.database.models.master_models import (
                LineMaster,
                PlantMaster,
                ProcessMaster,
            )
            from src.database.models.program_models import Program

            # 기본 쿼리: PLC와 Master 테이블, Program 테이블 조인
            query = (
                self.db.query(PLC)
                .outerjoin(
                    PlantMaster,
                    PLC.plant_id == PlantMaster.plant_id,
                )
                .outerjoin(
                    ProcessMaster,
                    PLC.process_id == ProcessMaster.process_id,
                )
                .outerjoin(
                    LineMaster,
                    PLC.line_id == LineMaster.line_id,
                )
                .outerjoin(
                    Program,
                    PLC.program_id == Program.program_id,
                )
                .filter(PLC.is_active.is_(True))
            )

            # 필터링 조건
            if plant_id:
                query = query.filter(PLC.plant_id == plant_id)
            if process_id:
                query = query.filter(PLC.process_id == process_id)
            if line_id:
                query = query.filter(PLC.line_id == line_id)
            if plc_id:
                query = query.filter(PLC.plc_id.ilike(f"%{plc_id}%"))
            if plc_name:
                query = query.filter(PLC.plc_name.ilike(f"%{plc_name}%"))
            if program_name:
                query = query.filter(Program.program_name.ilike(f"%{program_name}%"))

            # 전체 개수 조회
            total_count = query.count()

            # 정렬
            sort_column = getattr(PLC, sort_by, PLC.plc_id)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(sort_column)

            # 페이지네이션
            offset = (page - 1) * page_size
            plcs = query.offset(offset).limit(page_size).all()

            return plcs, total_count
        except Exception as e:
            logger.error(f"PLC 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def update_plc_program_mapping(
        self,
        plc_ids: List[str],
        program_id: str,
        mapping_user: str,
    ) -> Dict[str, int]:
        """
        여러 PLC에 Program 매핑 저장

        Args:
            plc_ids: 매핑할 PLC ID 리스트
            program_id: 매핑할 Program ID
            mapping_user: 매핑 사용자

        Returns:
            Dict: {
                "success_count": int,
                "failed_count": int,
                "errors": List[str]
            }
        """
        try:
            success_count = 0
            failed_count = 0
            errors = []

            for plc_id in plc_ids:
                try:
                    plc = self.get_plc(plc_id)
                    if not plc:
                        failed_count += 1
                        errors.append(f"PLC를 찾을 수 없습니다: {plc_id}")
                        continue

                    # 이전 program_id 저장 (변경 이력용)
                    if plc.program_id and plc.program_id != program_id:
                        # metadata_json에 이전 program_id 저장
                        metadata = plc.metadata_json or {}
                        metadata["previous_program_id"] = plc.program_id
                        plc.metadata_json = metadata

                    # Program 매핑 업데이트
                    plc.program_id = program_id
                    plc.mapping_dt = datetime.now()
                    plc.mapping_user = mapping_user
                    plc.update_dt = datetime.now()
                    plc.update_user = mapping_user

                    success_count += 1

                except Exception as e:
                    failed_count += 1
                    error_msg = f"PLC {plc_id} 매핑 실패: {str(e)}"
                    errors.append(error_msg)
                    logger.warning(error_msg)

            # 일괄 커밋
            self.db.commit()

            return {
                "success_count": success_count,
                "failed_count": failed_count,
                "errors": errors,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC Program 매핑 저장 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_plc(self, plc_uuid: str, delete_user: str) -> bool:
        """
        PLC 삭제 (소프트 삭제)
        
        - is_active를 False로 설정
        - program_id를 None으로 설정 (매핑 해제)
        
        Args:
            plc_uuid: PLC UUID
            delete_user: 삭제 사용자
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            plc = self.get_plc_by_uuid(plc_uuid)
            if not plc:
                return False

            # 소프트 삭제: is_active = False
            plc.is_active = False
            
            # 매핑된 program_id 제거
            plc.program_id = None
            plc.mapping_dt = None
            plc.mapping_user = None
            
            # 업데이트 정보
            plc.update_dt = datetime.now()
            plc.update_user = delete_user

            self.db.commit()
            logger.info(f"PLC {plc_uuid} 삭제 완료 (is_active=False, program_id=null)")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_plcs(self, plc_uuids: List[str], delete_user: str) -> int:
        """
        PLC 일괄 삭제 (소프트 삭제)
        
        - is_active를 False로 설정
        - program_id를 None으로 설정 (매핑 해제)
        
        Args:
            plc_uuids: PLC UUID 리스트
            delete_user: 삭제 사용자
            
        Returns:
            int: 삭제된 PLC 개수
        """
        try:
            deleted_count = 0

            for plc_uuid in plc_uuids:
                try:
                    success = self.delete_plc(plc_uuid, delete_user)
                    if success:
                        deleted_count += 1
                except Exception as e:
                    logger.warning(f"PLC {plc_uuid} 삭제 실패: {str(e)}")
                    # 개별 실패해도 계속 진행

            return deleted_count

        except Exception as e:
            logger.error(f"PLC 일괄 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
