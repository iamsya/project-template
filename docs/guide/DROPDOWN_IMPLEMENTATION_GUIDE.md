# 드롭다운 리스트 구현 가이드

## 1. 드롭다운 리스트 데이터 조회 방법

### 테이블 참조
드롭다운 리스트는 다음 마스터 테이블에서 데이터를 조회합니다:
- **Plant 드롭다운**: `PLANT_MASTER` 테이블
- **Process 드롭다운**: `PROCESS_MASTER` 테이블 (선택한 Plant에 따라 필터링)
- **Line 드롭다운**: `LINE_MASTER` 테이블 (선택한 Process에 따라 필터링)

### CRUD 메서드

#### Plant 목록 조회
```python
from src.database.crud.master_crud import PlantMasterCRUD

plant_crud = PlantMasterCRUD(db)
plants = plant_crud.get_all_plants(include_inactive=False)
# 반환: List[PlantMaster]
# - is_active=True인 것만 조회
# - display_order, plant_code 순으로 정렬
```

**코드 위치**: `ai_backend/src/database/crud/master_crud.py`
```73:84:ai_backend/src/database/crud/master_crud.py
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
```

#### Process 목록 조회 (Plant별)
```python
from src.database.crud.master_crud import ProcessMasterCRUD

process_crud = ProcessMasterCRUD(db)
processes = process_crud.get_processes_by_plant(plant_id, include_inactive=False)
# 반환: List[ProcessMaster]
# - 특정 plant_id에 속한 process만 조회
# - is_active=True인 것만 조회
# - display_order, process_code 순으로 정렬
```

**코드 위치**: `ai_backend/src/database/crud/master_crud.py`
```160:173:ai_backend/src/database/crud/master_crud.py
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
```

#### Line 목록 조회 (전체)
```python
from src.database.crud.master_crud import LineMasterCRUD

line_crud = LineMasterCRUD(db)
lines = line_crud.get_all_lines(include_inactive=False)
# 반환: List[LineMaster]
# - 모든 Line 조회 (Process와 무관)
# - is_active=True인 것만 조회
# - line_name 순으로 정렬
```

**코드 위치**: `ai_backend/src/database/crud/master_crud.py` (비슷한 패턴)

### 드롭다운 데이터 구조

각 마스터 테이블의 객체는 다음 필드를 포함합니다:
- `plant_id` / `process_id` / `line_id`: ID (드롭다운 value로 사용)
- `plant_code` / `process_code` / `line_code`: 코드
- `plant_name` / `process_name` / `line_name`: 이름 (드롭다운 label로 사용)
- `display_order`: 표시 순서
- `is_active`: 활성화 여부

### 프론트엔드 구현 예시

```javascript
// 1. Plant 드롭다운 로드
const plants = await fetch('/v1/masters/plants').then(r => r.json());
// plants: [{ plant_id, plant_code, plant_name, display_order, ... }]

// 2. Plant 선택 시 Process 드롭다운 로드
const selectedPlantId = 'plant001';
const processes = await fetch(`/v1/masters/processes?plant_id=${selectedPlantId}`).then(r => r.json());
// processes: [{ process_id, process_code, process_name, ... }]

// 3. Line 드롭다운 로드 (Process와 무관하게 전체 조회)
const lines = await fetch(`/v1/masters/lines`).then(r => r.json());
// lines: [{ line_id, line_name, ... }]
```

### 권한 관리 고려사항

사용자가 접근 가능한 공정만 보여지게 하려면:
- API에서 사용자 권한을 확인하여 필터링
- `get_processes_by_plant()` 호출 전에 권한 체크
- 또는 쿼리에 권한 조건 추가

---

## 2. Plant 이름 변경 시 영향

### 현재 구현 방식

PLC 테이블은 `plant_id`, `process_id`, `line_id`를 **FK로 직접 참조**하고 있습니다.
스냅샷 필드는 제거되었으므로, **마스터 테이블의 이름이 변경되면 PLC 조회 시 보이는 이름도 변경됩니다**.

### PLC 조회 시 이름 가져오는 방법

PLC 조회 시 계층 구조 이름은 `_get_hierarchy_with_names()` 메서드를 통해 실시간으로 마스터 테이블에서 조회합니다:

**코드 위치**: `ai_backend/src/database/crud/plc_crud.py`
```282:338:ai_backend/src/database/crud/plc_crud.py
    def _get_hierarchy_with_names(
        self, hierarchy_ids: Optional[Dict]
    ) -> Optional[Dict]:
        """
        Hierarchy ID들로부터 master 테이블 조인하여 계층 구조 정보 조회
        
        Returns:
            Dict: 계층 구조 정보 (id, code, name 포함)
        """
        if not hierarchy_ids:
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

            if hierarchy_ids.get("plant_id"):
                plant = plant_crud.get_plant(hierarchy_ids["plant_id"])
                if plant:
                    hierarchy["plant"] = {
                        "id": plant.plant_id,
                        "code": plant.plant_code,
                        "name": plant.plant_name,  # ← 실시간으로 마스터 테이블에서 조회
                    }

            if hierarchy_ids.get("process_id"):
                process = process_crud.get_process(hierarchy_ids["process_id"])
                if process:
                    hierarchy["process"] = {
                        "id": process.process_id,
                        "code": process.process_code,
                        "name": process.process_name,  # ← 실시간으로 마스터 테이블에서 조회
                    }

            if hierarchy_ids.get("line_id"):
                line = line_crud.get_line(hierarchy_ids["line_id"])
                if line:
                    hierarchy["line"] = {
                        "id": line.line_id,
                        "code": line.line_code,
                        "name": line.line_name,  # ← 실시간으로 마스터 테이블에서 조회
                    }

            return hierarchy if hierarchy else None

        except Exception as e:
            logger.warning(f"계층 구조 조회 실패: {str(e)}")
            return None
```

### 예시 시나리오

**시나리오**: Plant 이름이 "공장1"에서 "본사 공장"으로 변경됨

1. **마스터 테이블 업데이트**:
   ```sql
   UPDATE PLANT_MASTER 
   SET PLANT_NAME = '본사 공장', UPDATE_DT = NOW()
   WHERE PLANT_ID = 'plant001';
   ```

2. **PLC 조회 시**:
   - PLC 테이블의 `plant_id = 'plant001'`는 **변경되지 않음** (hierarchy는 수정되지 않음)
   - 하지만 `_get_hierarchy_with_names()` 메서드가 마스터 테이블에서 실시간으로 조회하므로
   - PLC 목록에서 보이는 Plant 이름은 **"본사 공장"**으로 표시됨

3. **결과**:
   - ✅ **Plant ID는 변경되지 않음** (PLC의 hierarchy는 불변)
   - ✅ **Plant 이름은 변경됨** (마스터 테이블과 실시간 조인)

### 장단점

**장점**:
- 마스터 데이터 변경 시 모든 PLC에 자동 반영
- 데이터 일관성 유지
- 스냅샷 관리 불필요

**단점**:
- 과거 이름 정보를 보존할 수 없음
- 마스터 데이터 삭제 시 PLC 조회 시 NULL이 될 수 있음

### 권장 사항

1. **마스터 데이터 삭제 방지**: PLC가 참조하는 마스터 데이터는 `is_active=false`로 비활성화만 하고 삭제하지 않음
2. **이름 변경 이력 관리**: 필요시 별도의 변경 이력 테이블 관리
3. **PLC hierarchy 불변**: 사용자 요구사항대로 "한번 입력된 PLC의 hierarchy는 수정되지 않음"을 유지

---

## 3. API 엔드포인트 (필요시 구현)

현재는 CRUD 메서드만 있고 API 엔드포인트는 없는 것 같습니다. 
드롭다운용 API가 필요하다면 다음과 같이 구현할 수 있습니다:

```python
# ai_backend/src/api/routers/master_router.py (새로 생성)

@router.get("/plants")
def get_plants_for_dropdown(db: Session = Depends(get_db)):
    """Plant 드롭다운용 목록 조회"""
    plant_crud = PlantMasterCRUD(db)
    plants = plant_crud.get_all_plants(include_inactive=False)
    return [{"id": p.plant_id, "code": p.plant_code, "name": p.plant_name} 
            for p in plants]

@router.get("/processes")
def get_processes_for_dropdown(
    plant_id: str = Query(..., description="Plant ID"),
    db: Session = Depends(get_db)
):
    """Process 드롭다운용 목록 조회"""
    process_crud = ProcessMasterCRUD(db)
    processes = process_crud.get_processes_by_plant(plant_id, include_inactive=False)
    return [{"id": p.process_id, "code": p.process_code, "name": p.process_name} 
            for p in processes]

@router.get("/lines")
def get_lines_for_dropdown(
    process_id: str = Query(..., description="Process ID"),
    db: Session = Depends(get_db)
):
    """Line 드롭다운용 목록 조회"""
    line_crud = LineMasterCRUD(db)
    lines = line_crud.get_all_lines(include_inactive=False)
    return [{"id": l.line_id, "code": l.line_code, "name": l.line_name} 
            for l in lines]
```

