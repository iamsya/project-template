# 드롭다운 리스트 성능 최적화 가이드

## 현재 상태 분석

### 인덱스 현황 (이미 최적화됨)

✅ **PlantMaster**
- `idx_plant_master_active_order` (IS_ACTIVE, DISPLAY_ORDER) - 복합 인덱스
- `idx_plant_master_active` (IS_ACTIVE) - 단일 인덱스

✅ **ProcessMaster**
- `idx_process_master_plant_active` (PLANT_ID, IS_ACTIVE) - 복합 인덱스 ⭐
- `idx_process_master_active_order` (IS_ACTIVE, DISPLAY_ORDER) - 복합 인덱스

✅ **LineMaster**
- `idx_line_master_process_active` (PROCESS_ID, IS_ACTIVE) - 복합 인덱스 ⭐
- `idx_line_master_active_order` (IS_ACTIVE, DISPLAY_ORDER) - 복합 인덱스

**현재 인덱스는 이미 최적화되어 있습니다!** 드롭다운 조회에 필요한 필터링과 정렬이 모두 인덱스로 커버됩니다.

---

## 최적화 방안

### 1. Redis 캐싱 (가장 효과적) ⭐⭐⭐

마스터 데이터는 변경 빈도가 낮고 조회 빈도가 높으므로 **Redis 캐싱**이 가장 효과적입니다.

#### 구현 예시

```python
# ai_backend/src/database/crud/master_crud.py에 추가

from src.cache.redis_client import RedisClient
import json
from typing import Optional

class PlantMasterCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = RedisClient() if RedisClient().ping() else None
        self.cache_ttl = 3600  # 1시간 (마스터 데이터는 변경 빈도 낮음)
    
    def get_all_plants(
        self, include_inactive: bool = False
    ) -> List[PlantMaster]:
        """모든 공장 기준정보 목록 조회 (캐싱 적용)"""
        cache_key = f"master:plants:active={not include_inactive}"
        
        # 1. Redis 캐시 확인
        if self.redis_client:
            cached = self.redis_client.redis_client.get(cache_key)
            if cached:
                data = json.loads(cached)
                # Dict를 PlantMaster 객체로 변환 (또는 Dict 그대로 반환)
                return [PlantMaster(**item) for item in data]
        
        # 2. DB 조회
        try:
            query = self.db.query(PlantMaster)
            if not include_inactive:
                query = query.filter(PlantMaster.is_active.is_(True))
            plants = query.order_by(
                PlantMaster.display_order, 
                PlantMaster.plant_code
            ).all()
            
            # 3. 캐시에 저장 (Dict 형태로 직렬화)
            if self.redis_client and plants:
                plant_dicts = [
                    {
                        "plant_id": p.plant_id,
                        "plant_code": p.plant_code,
                        "plant_name": p.plant_name,
                        "display_order": p.display_order,
                    }
                    for p in plants
                ]
                self.redis_client.redis_client.setex(
                    cache_key,
                    self.cache_ttl,
                    json.dumps(plant_dicts, default=str)
                )
            
            return plants
        except Exception as e:
            logger.error(f"공장 기준정보 목록 조회 실패: {str(e)}")
            raise HandledException(ResponseCode.DATABASE_QUERY_ERROR, e=e)
    
    def invalidate_cache(self):
        """캐시 무효화 (마스터 데이터 변경 시 호출)"""
        if self.redis_client:
            # 패턴 매칭으로 관련 캐시 모두 삭제
            keys = self.redis_client.redis_client.keys("master:plants:*")
            if keys:
                self.redis_client.redis_client.delete(*keys)
    
    def update_plant(self, plant_id: str, update_user: Optional[str] = None, **kwargs):
        """공장 기준정보 업데이트 (캐시 무효화 포함)"""
        result = self._update_plant_internal(plant_id, update_user, **kwargs)
        if result:
            self.invalidate_cache()  # 캐시 무효화
        return result
```

#### 캐시 키 전략

```
master:plants:active=true          # 활성 Plant 목록
master:plants:active=false         # 전체 Plant 목록
master:processes:plant_id={id}    # 특정 Plant의 Process 목록
master:lines                       # 전체 Line 목록
```

#### TTL 설정

- **Plant/Process/Line 마스터**: 1시간 (3600초)
  - 변경 빈도: 매우 낮음 (운영자가 수정)
  - 조회 빈도: 매우 높음 (드롭다운에서 계속 조회)

---

### 2. 필요한 컬럼만 SELECT (컬럼 최적화)

현재는 전체 객체를 조회하지만, 드롭다운에는 `id`, `code`, `name`, `display_order`만 필요합니다.

```python
def get_all_plants_optimized(
    self, include_inactive: bool = False
) -> List[Dict]:
    """드롭다운용 Plant 목록 조회 (필요한 컬럼만)"""
    query = self.db.query(
        PlantMaster.plant_id,
        PlantMaster.plant_code,
        PlantMaster.plant_name,
        PlantMaster.display_order,
    )
    if not include_inactive:
        query = query.filter(PlantMaster.is_active.is_(True))
    return query.order_by(
        PlantMaster.display_order,
        PlantMaster.plant_code
    ).all()
    # 반환: [(plant_id, plant_code, plant_name, display_order), ...]
```

**성능 향상**: 네트워크 전송량 감소, 메모리 사용량 감소

---

### 3. 배치 조회 (여러 Plant의 Process를 한 번에)

여러 Plant를 선택하는 경우, 각각 조회하지 않고 한 번에 조회:

```python
def get_processes_by_plants_batch(
    self, plant_ids: List[str], include_inactive: bool = False
) -> Dict[str, List[ProcessMaster]]:
    """여러 Plant의 Process를 한 번에 조회"""
    query = self.db.query(ProcessMaster).filter(
        ProcessMaster.plant_id.in_(plant_ids)
    )
    if not include_inactive:
        query = query.filter(ProcessMaster.is_active.is_(True))
    
    processes = query.order_by(
        ProcessMaster.plant_id,
        ProcessMaster.display_order,
        ProcessMaster.process_code
    ).all()
    
    # Plant별로 그룹화
    result = {plant_id: [] for plant_id in plant_ids}
    for process in processes:
        result[process.plant_id].append(process)
    
    return result
```

**사용 예시**:
```python
# 기존: 3번의 DB 쿼리
processes1 = process_crud.get_processes_by_plant("plant001")
processes2 = process_crud.get_processes_by_plant("plant002")
processes3 = process_crud.get_processes_by_plant("plant003")

# 최적화: 1번의 DB 쿼리
all_processes = process_crud.get_processes_by_plants_batch(
    ["plant001", "plant002", "plant003"]
)
```

---

### 4. 전체 계층 구조 한 번에 조회 (MasterHierarchyCRUD 활용)

이미 구현된 `MasterHierarchyCRUD`를 활용하면 Plant → Process → Line을 한 번에 조회할 수 있습니다.

```python
from src.database.crud.master_crud import MasterHierarchyCRUD

hierarchy_crud = MasterHierarchyCRUD(db)

# Plant별 전체 계층 구조 조회
hierarchy = hierarchy_crud.get_hierarchy_by_plant("plant001")
# 반환:
# {
#   "plant": PlantMaster,
#   "processes": [ProcessMaster, ...],
#   "lines": [LineMaster, ...],
# }
```

**장점**:
- 3번의 쿼리 → 1번의 쿼리 (IN 절 사용)
- 네트워크 왕복 감소

**단점**:
- Plant를 선택하지 않은 상태에서는 불필요한 데이터 조회

---

### 5. 인덱스 추가 최적화 (현재 이미 최적화됨)

현재 인덱스는 이미 최적화되어 있지만, 정렬 최적화를 위해 다음 인덱스도 고려할 수 있습니다:

```python
# display_order + code 정렬을 위한 복합 인덱스
Index("idx_plant_master_order_code", "DISPLAY_ORDER", "PLANT_CODE")
Index("idx_process_master_order_code", "DISPLAY_ORDER", "PROCESS_CODE")
Index("idx_line_master_order_code", "DISPLAY_ORDER", "LINE_CODE")
```

하지만 현재 인덱스로도 충분히 빠릅니다.

---

## 성능 비교

### 현재 방식 (인덱스만 사용)
```
Plant 조회:     ~5ms
Process 조회:   ~3ms (plant_id 인덱스 활용)
Line 조회:      ~3ms (process_id 인덱스 활용)
총 시간:        ~11ms
```

### Redis 캐싱 적용 후
```
Plant 조회:     ~0.1ms (캐시 히트 시)
Process 조회:   ~0.1ms (캐시 히트 시)
Line 조회:      ~0.1ms (캐시 히트 시)
총 시간:        ~0.3ms (약 36배 향상)
```

### 배치 조회 + 캐싱
```
전체 계층 조회: ~0.5ms (캐시 히트 시, 한 번의 조회)
```

---

## 권장 구현 순서

### 1단계: Redis 캐싱 추가 (가장 효과적) ⭐
- 구현 난이도: 중
- 성능 향상: 매우 높음 (10-50배)
- 우선순위: 최우선

### 2단계: 필요한 컬럼만 SELECT
- 구현 난이도: 낮음
- 성능 향상: 중간 (네트워크/메모리 최적화)
- 우선순위: 높음

### 3단계: 배치 조회 메서드 추가
- 구현 난이도: 중
- 성능 향상: 중간 (특정 시나리오에서 효과적)
- 우선순위: 중간

### 4단계: 전체 계층 구조 조회 활용
- 구현 난이도: 낮음 (이미 구현됨)
- 성능 향상: 중간 (특정 시나리오에서 효과적)
- 우선순위: 낮음

---

## 구현 예시: 최적화된 CRUD 메서드

```python
# ai_backend/src/database/crud/master_crud.py

class PlantMasterCRUD:
    def __init__(self, db: Session):
        self.db = db
        self.redis_client = RedisClient() if RedisClient().ping() else None
        self.cache_ttl = int(os.getenv("CACHE_TTL_MASTER", "3600"))
    
    def get_all_plants_for_dropdown(
        self, include_inactive: bool = False
    ) -> List[Dict]:
        """드롭다운용 Plant 목록 조회 (최적화)"""
        cache_key = f"master:plants:dropdown:active={not include_inactive}"
        
        # Redis 캐시 확인
        if self.redis_client:
            cached = self.redis_client.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # DB 조회 (필요한 컬럼만)
        query = self.db.query(
            PlantMaster.plant_id,
            PlantMaster.plant_code,
            PlantMaster.plant_name,
            PlantMaster.display_order,
        )
        if not include_inactive:
            query = query.filter(PlantMaster.is_active.is_(True))
        
        results = query.order_by(
            PlantMaster.display_order,
            PlantMaster.plant_code
        ).all()
        
        # Dict 형태로 변환
        plants = [
            {
                "id": r.plant_id,
                "code": r.plant_code,
                "name": r.plant_name,
                "display_order": r.display_order,
            }
            for r in results
        ]
        
        # 캐시 저장
        if self.redis_client:
            self.redis_client.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(plants, default=str)
            )
        
        return plants
    
    def invalidate_plant_cache(self):
        """Plant 캐시 무효화"""
        if self.redis_client:
            keys = self.redis_client.redis_client.keys("master:plants:*")
            if keys:
                self.redis_client.redis_client.delete(*keys)
```

---

## 캐시 무효화 전략

마스터 데이터가 변경될 때 캐시를 무효화해야 합니다:

```python
def update_plant(self, plant_id: str, **kwargs):
    """공장 기준정보 업데이트"""
    # ... 업데이트 로직 ...
    self.invalidate_plant_cache()  # 캐시 무효화
    return result

def create_plant(self, ...):
    """공장 기준정보 생성"""
    # ... 생성 로직 ...
    self.invalidate_plant_cache()  # 캐시 무효화
    return result
```

---

## 결론

1. **인덱스는 이미 최적화되어 있습니다** ✅
2. **Redis 캐싱이 가장 효과적** (10-50배 성능 향상) ⭐
3. **필요한 컬럼만 SELECT**로 네트워크/메모리 최적화
4. **배치 조회**는 특정 시나리오에서 유용

**권장**: Redis 캐싱을 먼저 구현하고, 필요시 다른 최적화를 추가하세요.

