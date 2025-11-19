# _*_ coding: utf-8 _*_
"""PLC CRUD operations with database."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session
from src.database.models.plc_models import PLC
from src.types.response.exceptions import HandledException
from src.types.response.response_code import ResponseCode
from src.utils.uuid_gen import gen_plc_uuid

logger = logging.getLogger(__name__)


class PLCCRUD:
    """PLC 관련 CRUD 작업을 처리하는 클래스"""

    def __init__(self, db: Session):
        self.db = db

    def get_plc(self, plc_id: str) -> Optional[PLC]:
        """PLC 조회 (ID로, is_deleted=False인 것만)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.id == plc_id)
                .filter(PLC.is_deleted.is_(False))
                .first()
            )
        except Exception as e:
            logger.error(f"PLC 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plc_by_plc_id(self, plc_id: str) -> Optional[PLC]:
        """PLC 조회 (plc_id로, is_deleted=False인 것만)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.plc_id == plc_id)
                .filter(PLC.is_deleted.is_(False))
                .first()
            )
        except Exception as e:
            logger.error(f"PLC 조회 실패 (plc_id): {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def get_plc_by_uuid(self, plc_uuid: str) -> Optional[PLC]:
        """PLC 조회 (plc_uuid로, is_deleted=False인 것만)"""
        try:
            return (
                self.db.query(PLC)
                .filter(PLC.plc_uuid == plc_uuid)
                .filter(PLC.is_deleted.is_(False))
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

    def create_plc(
        self,
        plant_id: str,
        process_id: str,
        line_id: str,
        plc_name: str,
        plc_id: str,
        create_user: str,
        unit: Optional[str] = None,
    ) -> PLC:
        """
        PLC 생성

        Args:
            plant_id: Plant ID
            process_id: Process ID
            line_id: Line ID
            plc_name: PLC명
            plc_id: PLC ID (사용자 입력)
            create_user: 생성 사용자
            unit: 호기 (선택사항)

        Returns:
            PLC: 생성된 PLC 객체

        Note:
            plc_uuid는 자동 생성됩니다 (plc_{plc_id}_{타임스탬프}_{랜덤문자열} 형식)
        """
        try:
            # PLC ID 중복 확인
            existing_plc = self.get_plc_by_plc_id(plc_id)
            if existing_plc:
                raise HandledException(
                    ResponseCode.VALIDATION_ERROR,
                    msg=f"PLC ID '{plc_id}'가 이미 존재합니다."
                )

            # PLC UUID 자동 생성
            plc_uuid = gen_plc_uuid(plc_id)

            # PLC 객체 생성
            plc = PLC(
                plc_uuid=plc_uuid,
                plant_id=plant_id,
                process_id=process_id,
                line_id=line_id,
                plc_name=plc_name,
                plc_id=plc_id,
                unit=unit,
                create_user=create_user,
            )

            self.db.add(plc)
            self.db.commit()
            self.db.refresh(plc)

            logger.info(
                "PLC 생성 완료: plc_uuid=%s, plc_id=%s",
                plc_uuid,
                plc_id
            )
            return plc

        except HandledException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error("PLC 생성 실패: %s", str(e))
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

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

            # Process 정보
            if hierarchy and hierarchy.get("process"):
                process = hierarchy["process"]
                snapshot["process_id"] = process.get("id")
                snapshot["process_name"] = process.get("name")

            # Line 정보
            if hierarchy and hierarchy.get("line"):
                line = hierarchy["line"]
                snapshot["line_id"] = line.get("id")
                snapshot["line_name"] = line.get("name")

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
                        "name": plant.plant_name,
                    }

            if snapshot_ids.get("process_id"):
                process = process_crud.get_process(snapshot_ids["process_id"])
                if process:
                    hierarchy["process"] = {
                        "id": process.process_id,
                        "name": process.process_name,
                    }

            if snapshot_ids.get("line_id"):
                line = line_crud.get_line(snapshot_ids["line_id"])
                if line:
                    hierarchy["line"] = {
                        "id": line.line_id,
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
                .filter(PLC.is_deleted.is_(False))
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

    def update_plc(
        self,
        plc_uuid: str,
        plc_name: str,
        plc_id: str,
        update_user: str,
        plant_id: Optional[str] = None,
        process_id: Optional[str] = None,
        line_id: Optional[str] = None,
        unit: Optional[str] = None,
    ) -> Optional[PLC]:
        """
        PLC 수정
        
        Args:
            plc_uuid: PLC UUID (필수)
            plc_name: PLC명
            plc_id: PLC ID
            update_user: 수정 사용자
            plant_id: Plant ID (선택)
            process_id: Process ID (선택)
            line_id: Line ID (선택)
            unit: 호기 (선택)
            
        Returns:
            Optional[PLC]: 수정된 PLC 객체 (없으면 None)
        """
        try:
            plc = self.get_plc_by_uuid(plc_uuid)
            if not plc:
                return None
            
            # PLC ID 중복 확인 (다른 PLC가 같은 plc_id를 사용하는지)
            if plc_id != plc.plc_id:
                existing_plc = self.get_plc_by_plc_id(plc_id)
                if existing_plc:
                    raise HandledException(
                        ResponseCode.VALIDATION_ERROR,
                        msg=f"PLC ID '{plc_id}'가 이미 존재합니다."
                    )
            
            # 필드 업데이트
            plc.plc_name = plc_name
            plc.plc_id = plc_id
            plc.update_dt = datetime.now()
            plc.update_user = update_user
            
            if plant_id is not None:
                plc.plant_id = plant_id
            if process_id is not None:
                plc.process_id = process_id
            if line_id is not None:
                plc.line_id = line_id
            if unit is not None:
                plc.unit = unit
            
            self.db.commit()
            self.db.refresh(plc)
            
            logger.info(f"PLC {plc_uuid} 수정 완료")
            return plc
            
        except HandledException:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 수정 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_plc(self, plc_uuid: str, delete_user: str) -> bool:
        """
        PLC 삭제 (소프트 삭제)
        
        - is_deleted를 True로 설정
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

            # 소프트 삭제: is_deleted = True
            plc.is_deleted = True
            plc.deleted_at = datetime.now()
            plc.deleted_by = delete_user
            
            # 매핑된 program_id 제거
            plc.program_id = None
            plc.mapping_dt = None
            plc.mapping_user = None
            
            # 업데이트 정보
            plc.update_dt = datetime.now()
            plc.update_user = delete_user

            self.db.commit()
            logger.info(f"PLC {plc_uuid} 삭제 완료 (is_deleted=True, program_id=null)")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"PLC 삭제 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)

    def delete_plcs(self, plc_uuids: List[str], delete_user: str) -> int:
        """
        PLC 일괄 삭제 (소프트 삭제)
        
        - is_deleted를 True로 설정
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

    def get_plc_tree(self) -> List[Dict]:
        """
        PLC Tree 구조 조회 (채팅 메뉴에서 PLC 선택용)
        
        Hierarchy: Plant → 공정 → Line → PLC명 → 호기 → PLC ID
        
        Returns:
            List[Dict]: Plant 리스트 (각 Plant는 procList를 포함)
            
        Note:
            program_id가 있는 PLC만 조회합니다 (프로그램이 매핑된 PLC만)
        """
        try:
            from src.database.models.master_models import (
                LineMaster,
                PlantMaster,
                ProcessMaster,
            )

            # 활성화된 PLC만 조회 (마스터 테이블과 조인하여 이름도 함께 가져옴)
            # program_id가 있는 것만 조회
            plcs_with_masters = (
                self.db.query(
                    PLC,
                    PlantMaster.plant_name,
                    ProcessMaster.process_name,
                    LineMaster.line_name,
                )
                .join(
                    PlantMaster,
                    PLC.plant_id == PlantMaster.plant_id,
                )
                .join(
                    ProcessMaster,
                    PLC.process_id == ProcessMaster.process_id,
                )
                .join(
                    LineMaster,
                    PLC.line_id == LineMaster.line_id,
                )
                .filter(PLC.is_deleted.is_(False))
                .filter(PLC.program_id.isnot(None))  # program_id가 있는 것만
                .filter(PlantMaster.is_active.is_(True))
                .filter(ProcessMaster.is_active.is_(True))
                .filter(LineMaster.is_active.is_(True))
                .order_by(
                    PlantMaster.plant_name,
                    ProcessMaster.process_name,
                    LineMaster.line_name,
                    PLC.plc_name,
                    PLC.unit,
                )
                .all()
            )

            # 계층 구조로 그룹화
            # Plant → Process → Line → PLC명 → 호기 → PLC 정보
            tree = {}

            for plc, plant_name, process_name, line_name in plcs_with_masters:
                # Plant 레벨
                if plant_name not in tree:
                    tree[plant_name] = {}

                # Process 레벨
                if process_name not in tree[plant_name]:
                    tree[plant_name][process_name] = {}

                # Line 레벨
                if line_name not in tree[plant_name][process_name]:
                    tree[plant_name][process_name][line_name] = {}

                # PLC명 레벨
                plc_name = plc.plc_name
                if plc_name not in tree[plant_name][process_name][line_name]:
                    tree[plant_name][process_name][line_name][plc_name] = {}

                # 호기 레벨
                unit = plc.unit or "N/A"
                if unit not in tree[plant_name][process_name][line_name][plc_name]:
                    tree[plant_name][process_name][line_name][plc_name][unit] = []

                # PLC 정보 추가
                plc_info = {
                    "plc_id": plc.plc_id,
                    "plc_uuid": plc.plc_uuid,
                    "create_dt": (
                        plc.create_dt.strftime("%Y/%m/%d %H:%M")
                        if plc.create_dt
                        else ""
                    ),
                    "user": plc.create_user or "",
                }
                tree[plant_name][process_name][line_name][plc_name][unit].append(
                    plc_info
                )

            # 응답 형식으로 변환
            result = []
            for plant_name, processes in sorted(tree.items()):
                proc_list = []
                for process_name, lines in sorted(processes.items()):
                    line_list = []
                    for line_name, plc_names in sorted(lines.items()):
                        plc_name_list = []
                        for plc_name, units in sorted(plc_names.items()):
                            unit_list = []
                            for unit, plc_infos in sorted(units.items()):
                                unit_list.append({
                                    "unit": unit,
                                    "info": plc_infos,
                                })
                            plc_name_list.append({
                                "plcName": plc_name,
                                "unitList": unit_list,
                            })
                        line_list.append({
                            "line": line_name,
                            "plcNameList": plc_name_list,
                        })
                    proc_list.append({
                        "proc": process_name,
                        "lineList": line_list,
                    })
                result.append({
                    "plant": plant_name,
                    "procList": proc_list,
                })

            return result

        except Exception as e:
            logger.error(f"PLC Tree 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
