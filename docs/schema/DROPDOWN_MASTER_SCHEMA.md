# DROPDOWN_MASTER 테이블 스키마

## 개요

드롭다운 리스트용 마스터 테이블입니다. Plant-Process-Line 계층 구조를 지원하여 계층적 드롭다운을 구현할 수 있습니다.

## 테이블 정의

```sql
CREATE TABLE DROPDOWN_MASTER (
    DROPDOWN_ID VARCHAR(50) PRIMARY KEY,
    DROPDOWN_NAME VARCHAR(255) NOT NULL,
    DROPDOWN_VALUE VARCHAR(255) NULL,
    CATEGORY VARCHAR(50) NULL,
    DESCRIPTION TEXT NULL,
    PLANT_ID VARCHAR(50) NULL REFERENCES PLANT_MASTER(PLANT_ID),
    PROCESS_ID VARCHAR(50) NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    LINE_ID VARCHAR(50) NULL REFERENCES LINE_MASTER(LINE_ID),
    DISPLAY_ORDER INTEGER NOT NULL DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    METADATA_JSON JSON NULL,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP NULL,
    UPDATE_USER VARCHAR(50) NULL
);

-- 인덱스
CREATE INDEX idx_dropdown_master_category_active ON DROPDOWN_MASTER(CATEGORY, IS_ACTIVE);
CREATE INDEX idx_dropdown_master_active ON DROPDOWN_MASTER(IS_ACTIVE);
CREATE INDEX idx_dropdown_master_order ON DROPDOWN_MASTER(DISPLAY_ORDER);
CREATE INDEX idx_dropdown_master_plant ON DROPDOWN_MASTER(PLANT_ID, IS_ACTIVE);
CREATE INDEX idx_dropdown_master_process ON DROPDOWN_MASTER(PROCESS_ID, IS_ACTIVE);
CREATE INDEX idx_dropdown_master_line ON DROPDOWN_MASTER(LINE_ID, IS_ACTIVE);
```

## 컬럼 정의

<table>
<thead>
<tr>
<th>컬럼명</th>
<th>타입</th>
<th>제약조건</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>DROPDOWN_ID</code></td>
<td>String(50)</td>
<td>PK</td>
<td>드롭다운 항목 ID (Primary Key)</td>
</tr>
<tr>
<td><code>DROPDOWN_NAME</code></td>
<td>String(255)</td>
<td>NOT NULL</td>
<td>드롭다운 항목 이름 (표시명)</td>
</tr>
<tr>
<td><code>DROPDOWN_VALUE</code></td>
<td>String(255)</td>
<td>NULL</td>
<td>드롭다운 항목 값 (선택사항, name과 다를 수 있음)</td>
</tr>
<tr>
<td><code>CATEGORY</code></td>
<td>String(50)</td>
<td>NULL, INDEX</td>
<td>카테고리 (선택사항, 같은 카테고리로 그룹화 가능)</td>
</tr>
<tr>
<td><code>DESCRIPTION</code></td>
<td>Text</td>
<td>NULL</td>
<td>설명</td>
</tr>
<tr>
<td><code>PLANT_ID</code></td>
<td>String(50)</td>
<td>NULL, FK</td>
<td>Plant ID (계층 구조 1단계, Plant 드롭다운용)</td>
</tr>
<tr>
<td><code>PROCESS_ID</code></td>
<td>String(50)</td>
<td>NULL, FK</td>
<td>공정 ID (계층 구조 2단계, Process 드롭다운용)</td>
</tr>
<tr>
<td><code>LINE_ID</code></td>
<td>String(50)</td>
<td>NULL, FK</td>
<td>Line ID (계층 구조 3단계, Line 드롭다운용)</td>
</tr>
<tr>
<td><code>DISPLAY_ORDER</code></td>
<td>Integer</td>
<td>NOT NULL, DEFAULT 0</td>
<td>표시 순서 (정렬용)</td>
</tr>
<tr>
<td><code>IS_ACTIVE</code></td>
<td>Boolean</td>
<td>NOT NULL, DEFAULT true</td>
<td>활성화 여부</td>
</tr>
<tr>
<td><code>METADATA_JSON</code></td>
<td>JSON</td>
<td>NULL</td>
<td>메타데이터 (추가 정보 저장용)</td>
</tr>
<tr>
<td><code>CREATE_DT</code></td>
<td>DateTime</td>
<td>NOT NULL, DEFAULT now()</td>
<td>생성 일시</td>
</tr>
<tr>
<td><code>CREATE_USER</code></td>
<td>String(50)</td>
<td>NOT NULL</td>
<td>생성 사용자</td>
</tr>
<tr>
<td><code>UPDATE_DT</code></td>
<td>DateTime</td>
<td>NULL</td>
<td>수정 일시</td>
</tr>
<tr>
<td><code>UPDATE_USER</code></td>
<td>String(50)</td>
<td>NULL</td>
<td>수정 사용자</td>
</tr>
</tbody>
</table>

## 인덱스

- `idx_dropdown_master_category_active`: 카테고리별 활성 항목 필터링 최적화
- `idx_dropdown_master_active`: 활성 항목 필터링 최적화
- `idx_dropdown_master_order`: 정렬 최적화

## 사용 예시

### 데이터 추가

```sql
-- 계층 구조를 가진 드롭다운 항목 추가
-- 예: "a plant - b 공정 - 1라인", "a plant - b 공정 - 2라인"
INSERT INTO DROPDOWN_MASTER (
    DROPDOWN_ID, DROPDOWN_NAME, PLANT_ID, PROCESS_ID, LINE_ID, DISPLAY_ORDER, CREATE_USER
) VALUES
    ('dd_001', 'a plant - b 공정 - 1라인', 'plant_a', 'process_b', 'line_1', 1, 'admin'),
    ('dd_002', 'a plant - b 공정 - 2라인', 'plant_a', 'process_b', 'line_2', 2, 'admin'),
    ('dd_003', 'a plant - c 공정 - 1라인', 'plant_a', 'process_c', 'line_1', 3, 'admin'),
    ('dd_004', 'b plant - b 공정 - 1라인', 'plant_b', 'process_b', 'line_1', 1, 'admin');
```

### 계층 구조 조회

```sql
-- 1. Plant 목록 조회 (중복 제거)
SELECT DISTINCT PLANT_ID
FROM DROPDOWN_MASTER
WHERE IS_ACTIVE = true
  AND PLANT_ID IS NOT NULL
ORDER BY PLANT_ID;

-- 2. 특정 Plant의 Process 목록 조회
SELECT DISTINCT PROCESS_ID
FROM DROPDOWN_MASTER
WHERE IS_ACTIVE = true
  AND PLANT_ID = 'plant_a'
  AND PROCESS_ID IS NOT NULL
ORDER BY PROCESS_ID;

-- 3. 특정 Plant와 Process의 Line 목록 조회
SELECT DISTINCT LINE_ID
FROM DROPDOWN_MASTER
WHERE IS_ACTIVE = true
  AND PLANT_ID = 'plant_a'
  AND PROCESS_ID = 'process_b'
  AND LINE_ID IS NOT NULL
ORDER BY LINE_ID;

-- 4. 특정 Plant-Process-Line 조합의 드롭다운 항목 조회
SELECT DROPDOWN_ID, DROPDOWN_NAME, DROPDOWN_VALUE
FROM DROPDOWN_MASTER
WHERE IS_ACTIVE = true
  AND PLANT_ID = 'plant_a'
  AND PROCESS_ID = 'process_b'
  AND LINE_ID = 'line_1'
ORDER BY DISPLAY_ORDER, DROPDOWN_NAME;
```

### 데이터 수정

```sql
-- 드롭다운 항목 수정
UPDATE DROPDOWN_MASTER
SET DROPDOWN_NAME = '대기중',
    UPDATE_USER = 'admin',
    UPDATE_DT = NOW()
WHERE DROPDOWN_ID = 'dd_status_001';
```

### 데이터 삭제 (소프트 삭제)

```sql
-- 드롭다운 항목 비활성화
UPDATE DROPDOWN_MASTER
SET IS_ACTIVE = false,
    UPDATE_USER = 'admin',
    UPDATE_DT = NOW()
WHERE DROPDOWN_ID = 'dd_status_001';
```

## 특징

1. **계층 구조 지원**: Plant → Process → Line 계층 구조로 드롭다운 관리
2. **연쇄 드롭다운**: Plant 선택 → 해당 Plant의 Process만 표시 → Process 선택 → 해당 Process의 Line만 표시
3. **범용성**: 카테고리 필드로 추가 그룹화 가능
4. **정렬 지원**: `DISPLAY_ORDER`로 표시 순서 제어
5. **소프트 삭제**: `IS_ACTIVE` 플래그로 삭제 관리

## 프론트엔드 사용 예시

### 계층 구조 드롭다운 구현

```javascript
// 1. Plant 드롭다운 로드
const plants = await fetch('/v1/dropdowns/plants').then(r => r.json());
// 응답: ["plant_a", "plant_b", ...]

// 2. Plant 선택 시 Process 드롭다운 로드
const selectedPlantId = 'plant_a';
const processes = await fetch(`/v1/dropdowns/processes?plant_id=${selectedPlantId}`).then(r => r.json());
// 응답: ["process_b", "process_c", ...]

// 3. Process 선택 시 Line 드롭다운 로드
const selectedProcessId = 'process_b';
const lines = await fetch(`/v1/dropdowns/lines?plant_id=${selectedPlantId}&process_id=${selectedProcessId}`).then(r => r.json());
// 응답: ["line_1", "line_2", ...]

// 4. 최종 드롭다운 항목 조회
const dropdownItems = await fetch(`/v1/dropdowns?plant_id=${selectedPlantId}&process_id=${selectedProcessId}&line_id=${selectedLineId}`).then(r => r.json());
// 응답: [{dropdown_id: "dd_001", dropdown_name: "a plant - b 공정 - 1라인", ...}, ...]
```
