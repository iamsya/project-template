# 마스터 테이블 구조 변경 제안

## 현재 문제점

1. **Process, Line이 Plant에 종속됨**
   - `PROCESS_MASTER`에 `plant_id` FK가 있어서 각 Plant마다 동일한 Process를 중복 입력해야 함
   - 예: "모듈", "조립", "화성" 공정을 여러 법인에서 사용하지만, 각 Plant마다 별도로 입력 필요

2. **데이터 중복**
   - 동일한 Process/Line을 여러 Plant에 중복 입력
   - 관리 비용 증가 및 데이터 일관성 문제

## 제안 방안

### 방안 1: Process, Line을 Plant와 분리 (권장) ⭐

**구조 변경:**
- `PROCESS_MASTER`에서 `plant_id` FK 제거 → 공통 마스터로 변경
- `LINE_MASTER`에서 `process_id` FK 제거 → 공통 마스터로 변경
- `PLC` 테이블에서 `plant_id`, `process_id`, `line_id` 모두 FK로 직접 참조

**장점:**
- ✅ Process, Line을 한 번만 입력하면 모든 Plant에서 사용 가능
- ✅ 데이터 중복 제거
- ✅ 구조가 단순하고 명확함
- ✅ 기존 PLC 테이블 구조 변경 최소화

**단점:**
- ⚠️ Plant별로 다른 Process/Line이 필요한 경우 처리 어려움 (하지만 요구사항상 공통 사용이므로 문제 없음)

**변경 사항:**
```sql
-- PROCESS_MASTER 변경
ALTER TABLE PROCESS_MASTER DROP CONSTRAINT process_master_plant_id_fkey;
ALTER TABLE PROCESS_MASTER DROP COLUMN PLANT_ID;
DROP INDEX idx_process_master_plant_active;

-- PLC 테이블은 변경 없음 (이미 plant_id, process_id, line_id 모두 FK로 참조)
```

**데이터 구조:**
```
PLANT_MASTER (법인별)
  ├─ plant_001 (법인A)
  └─ plant_002 (법인B)

PROCESS_MASTER (공통)
  ├─ process_001 (모듈)
  ├─ process_002 (조립)
  └─ process_003 (화성)

LINE_MASTER (공통)
  ├─ line_001
  ├─ line_002
  └─ line_003

PLC (Plant + Process + Line 조합)
  ├─ plant_001 + process_001 + line_001 → PLC1
  ├─ plant_001 + process_002 + line_003 → PLC2
  ├─ plant_002 + process_001 + line_001 → PLC3 (같은 Process/Line 재사용)
  └─ plant_002 + process_002 + line_003 → PLC4
```

---

### 방안 2: PLC 테이블에 스냅샷 저장

**구조 변경:**
- 마스터 테이블 구조는 유지
- `PLC` 테이블에 `plant_name`, `process_name`, `line_name`을 직접 저장 (스냅샷)
- FK 제거하고 문자열로 저장

**장점:**
- ✅ 마스터 테이블 구조 변경 없음
- ✅ 마스터 데이터 삭제/변경 시에도 PLC 데이터 보존

**단점:**
- ❌ 데이터 정규화 위반
- ❌ 마스터 데이터 변경 시 PLC에 반영 안됨
- ❌ 데이터 일관성 문제
- ❌ 검색/필터링 성능 저하

**비권장 이유:**
- 데이터 정규화 원칙 위반
- 마스터 데이터와 PLC 데이터 불일치 가능성

---

### 방안 3: Plant-Process-Line 매핑 테이블 추가

**구조 변경:**
- `PLANT_PROCESS_MAPPING` 테이블 추가 (어떤 Plant에서 어떤 Process 사용 가능한지)
- `PROCESS_LINE_MAPPING` 테이블 추가 (어떤 Process에서 어떤 Line 사용 가능한지)
- 마스터 테이블은 공통으로 유지

**장점:**
- ✅ 유연성 높음 (Plant별로 다른 Process/Line 조합 가능)
- ✅ 데이터 정규화 유지

**단점:**
- ❌ 구조가 복잡해짐
- ❌ 조인 쿼리 복잡도 증가
- ❌ 요구사항(공통 사용)에 비해 과도한 설계

**비권장 이유:**
- 요구사항이 "공통 사용"인데 매핑 테이블까지 필요 없음
- 복잡도 대비 이점이 적음

---

## 최종 권장: 방안 1 (Process, Line을 Plant와 분리)

### 구현 단계

1. **마이그레이션 스크립트 작성**
   ```sql
   -- 1. 기존 데이터 백업
   CREATE TABLE PROCESS_MASTER_BACKUP AS SELECT * FROM PROCESS_MASTER;
   CREATE TABLE LINE_MASTER_BACKUP AS SELECT * FROM LINE_MASTER;
   
   -- 2. 중복 제거 (같은 이름의 Process는 하나만 유지)
   -- 예: plant_001의 "모듈"과 plant_002의 "모듈"을 하나로 통합
   
   -- 3. FK 제거
   ALTER TABLE PROCESS_MASTER DROP CONSTRAINT process_master_plant_id_fkey;
   ALTER TABLE PROCESS_MASTER DROP COLUMN PLANT_ID;
   DROP INDEX IF EXISTS idx_process_master_plant_active;
   
   -- 4. PLC 테이블은 변경 없음 (이미 plant_id, process_id, line_id 모두 FK)
   ```

2. **모델 변경**
   - `ProcessMaster`에서 `plant_id` 컬럼 제거
   - `LineMaster`는 변경 없음 (process_id FK 유지)
   - `PLC` 모델은 변경 없음

3. **CRUD 로직 변경**
   - `get_processes_by_plant()` → `get_all_processes()`로 변경
   - Process 조회 시 Plant 필터링 제거
   - 드롭다운 로직 단순화

4. **API 변경**
   - Process 드롭다운: Plant 선택 없이 전체 Process 조회
   - Line 드롭다운: 모든 Line 조회 (Process와 무관)

---

## 비교표

| 항목 | 현재 구조 | 방안 1 (권장) | 방안 2 | 방안 3 |
|------|----------|--------------|--------|--------|
| **데이터 중복** | 있음 | 없음 | 있음 | 없음 |
| **구조 복잡도** | 중간 | 낮음 | 낮음 | 높음 |
| **유지보수성** | 낮음 | 높음 | 낮음 | 중간 |
| **성능** | 중간 | 높음 | 낮음 | 중간 |
| **데이터 정규화** | 부분 | 완전 | 위반 | 완전 |
| **구현 난이도** | - | 낮음 | 낮음 | 높음 |

---

## 결론

**방안 1 (Process, Line을 Plant와 분리)**을 권장합니다.

이유:
1. 요구사항(공통 사용)에 가장 적합
2. 구조가 단순하고 명확
3. 데이터 중복 제거
4. 구현 난이도 낮음
5. 기존 PLC 테이블 구조 변경 최소화

