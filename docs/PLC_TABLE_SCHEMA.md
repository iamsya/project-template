# PLC 관련 테이블 스키마

## 1. PLC 테이블 (PLC)

**용도**: PLC 기준 정보 및 Program 매핑 테이블

**Hierarchy 구조**: Plant → 공정(Process) → Line → PLC명 → 호기(Unit)
- Plant, Process, Line: 운영자가 입력하는 마스터 데이터 (드롭다운 선택)
- PLC명, 호기, PLC ID: 사용자가 화면에서 직접 입력
- 한번 입력된 PLC의 hierarchy는 수정되지 않음

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| PLC_UUID | String(50) | PK | PLC UUID (Primary Key, 기존 ID에서 변경) |
| PLANT_ID | String(50) | FK, NOT NULL, INDEX | Plant ID (hierarchy 1단계, 필수) |
| PROCESS_ID | String(50) | FK, NOT NULL, INDEX | 공정(Process) ID (hierarchy 2단계, 필수) |
| LINE_ID | String(50) | FK, NOT NULL, INDEX | Line ID (hierarchy 3단계, 필수) |
| PLC_NAME | String(255) | NOT NULL | PLC명 (hierarchy 4단계, 사용자 입력) |
| UNIT | String(100) | NULL | 호기 (hierarchy 5단계, 사용자 입력, 예: 1, 2) |
| PLC_ID | String(50) | NOT NULL, INDEX | PLC 식별자 (사용자 수기 입력) |
| PROGRAM_ID | String(50) | FK, UNIQUE, INDEX | PLC 1개 → Program 1개 (unique) |
| MAPPING_DT | DateTime | NULL | 매핑 일시 |
| MAPPING_USER | String(50) | NULL | 매핑 사용자 |
| IS_ACTIVE | Boolean | NOT NULL, DEFAULT true | 활성화 여부 |
| METADATA_JSON | JSON | NULL | 메타데이터 (previous_program_id 등 저장) |
| CREATE_DT | DateTime | NOT NULL, DEFAULT now() | PLC 등록일시 |
| CREATE_USER | String(50) | NOT NULL | PLC 입력한 사람 |
| UPDATE_DT | DateTime | NULL | 수정 일시 |
| UPDATE_USER | String(50) | NULL | 수정 사용자 |

### Foreign Key 관계
- `PLANT_ID` → `PLANT_MASTER.PLANT_ID`
- `PROCESS_ID` → `PROCESS_MASTER.PROCESS_ID`
- `LINE_ID` → `LINE_MASTER.LINE_ID`
- `PROGRAM_ID` → `PROGRAMS.PROGRAM_ID`

### 메타데이터 (METADATA_JSON)

`METADATA_JSON` 필드에 저장되는 주요 정보:
- `previous_program_id`: 이전에 매핑되었던 Program ID (Program 매핑 변경 시 저장)

### 제거된 컬럼
- `ID` (→ `PLC_UUID`로 변경)
- `PLANT_ID_SNAPSHOT` (스냅샷 개념 제거)
- `PROCESS_ID_SNAPSHOT` (스냅샷 개념 제거)
- `LINE_ID_SNAPSHOT` (스냅샷 개념 제거)
- `PLANT_ID_CURRENT` (불필요)
- `PROCESS_ID_CURRENT` (불필요)
- `LINE_ID_CURRENT` (불필요)
- `EQUIPMENT_GROUP_ID_SNAPSHOT` (Equipment Group 제거)
- `EQUIPMENT_GROUP_ID_CURRENT` (Equipment Group 제거)

---

## 2. CHAT_MESSAGES 테이블

**용도**: 채팅 메시지 저장

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| MESSAGE_ID | String(50) | PK | 메시지 ID |
| CHAT_ID | String(50) | FK, NOT NULL | 채팅 ID |
| USER_ID | String(50) | NOT NULL | 사용자 ID |
| MESSAGE | Text | NOT NULL | 메시지 내용 |
| MESSAGE_TYPE | String(20) | NOT NULL | 메시지 타입 (text, image, file, assistant, user, cancelled) |
| STATUS | String(20) | NULL | 상태 (generating, completed, cancelled, error) |
| CREATE_DT | DateTime | NOT NULL, DEFAULT now() | 생성 일시 |
| IS_DELETED | Boolean | NOT NULL, DEFAULT false | 삭제 여부 |
| IS_CANCELLED | Boolean | NOT NULL, DEFAULT false | 취소 여부 |
| PLC_UUID | String(50) | FK, NULL, INDEX | PLC UUID (PLC 테이블 참조) |
| PLC_HIERARCHY_SNAPSHOT | JSON | NULL | PLC Hierarchy 스냅샷 (채팅 메시지 저장 시점의 정보) |
| EXTERNAL_API_NODES | JSON | NULL | External API 노드 처리 결과 저장용 |

### Foreign Key 관계
- `CHAT_ID` → `CHATS.CHAT_ID`
- `PLC_UUID` → `PLC.PLC_UUID`

### 제거된 컬럼
- `PLC_ID` (→ `PLC_UUID`로 변경)
- `PLC_PLANT_ID_SNAPSHOT` (스냅샷 개념 제거)
- `PLC_PROCESS_ID_SNAPSHOT` (스냅샷 개념 제거)
- `PLC_LINE_ID_SNAPSHOT` (스냅샷 개념 제거)
- `PLC_EQUIPMENT_GROUP_ID_SNAPSHOT` (Equipment Group 제거)

---

## 3. PLANT_MASTER 테이블

**용도**: 공장 기준정보 마스터 테이블 (운영자 입력)

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| PLANT_ID | String(50) | PK | Plant ID |
| PLANT_CODE | String(50) | UNIQUE, NOT NULL, INDEX | Plant 코드 |
| PLANT_NAME | String(255) | NOT NULL | Plant 이름 |
| DESCRIPTION | Text | NULL | 설명 |
| IS_ACTIVE | Boolean | NOT NULL, DEFAULT true | 활성화 여부 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATE_DT | DateTime | NOT NULL, DEFAULT now() | 생성 일시 |
| CREATE_USER | String(50) | NOT NULL | 생성 사용자 |
| UPDATE_DT | DateTime | NULL | 수정 일시 |
| UPDATE_USER | String(50) | NULL | 수정 사용자 |

---

## 4. PROCESS_MASTER 테이블

**용도**: 공정 기준정보 마스터 테이블 (운영자 입력)

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| PROCESS_ID | String(50) | PK | Process ID |
| PROCESS_CODE | String(50) | UNIQUE, NOT NULL, INDEX | Process 코드 |
| PROCESS_NAME | String(255) | NOT NULL | Process 이름 |
| PLANT_ID | String(50) | FK, NOT NULL, INDEX | Plant ID |
| DESCRIPTION | Text | NULL | 설명 |
| IS_ACTIVE | Boolean | NOT NULL, DEFAULT true | 활성화 여부 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATE_DT | DateTime | NOT NULL, DEFAULT now() | 생성 일시 |
| CREATE_USER | String(50) | NOT NULL | 생성 사용자 |
| UPDATE_DT | DateTime | NULL | 수정 일시 |
| UPDATE_USER | String(50) | NULL | 수정 사용자 |

### Foreign Key 관계
- `PLANT_ID` → `PLANT_MASTER.PLANT_ID`

---

## 5. LINE_MASTER 테이블

**용도**: 라인 기준정보 마스터 테이블 (운영자 입력)

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| LINE_ID | String(50) | PK | Line ID |
| LINE_CODE | String(50) | UNIQUE, NOT NULL, INDEX | Line 코드 |
| LINE_NAME | String(255) | NOT NULL | Line 이름 |
| PROCESS_ID | String(50) | FK, NOT NULL, INDEX | Process ID |
| DESCRIPTION | Text | NULL | 설명 |
| IS_ACTIVE | Boolean | NOT NULL, DEFAULT true | 활성화 여부 |
| METADATA_JSON | JSON | NULL | 메타데이터 |
| CREATE_DT | DateTime | NOT NULL, DEFAULT now() | 생성 일시 |
| CREATE_USER | String(50) | NOT NULL | 생성 사용자 |
| UPDATE_DT | DateTime | NULL | 수정 일시 |
| UPDATE_USER | String(50) | NULL | 수정 사용자 |

### Foreign Key 관계
- `PROCESS_ID` → `PROCESS_MASTER.PROCESS_ID`

---

## 6. PLC_HIERARCHY_HISTORY 테이블 (참고)

**용도**: PLC 계층 구조 변경 이력 (하지만 hierarchy는 수정되지 않으므로 사용하지 않을 수 있음)

### 컬럼 정의

| 컬럼명 | 타입 | 제약조건 | 설명 |
|--------|------|----------|------|
| HISTORY_ID | String(50) | PK | History ID |
| PLC_UUID | String(50) | FK, NOT NULL, INDEX | PLC UUID (PLC 테이블 참조) |
| PREVIOUS_HIERARCHY | JSON | NULL | 변경 전 계층 구조 스냅샷 |
| NEW_HIERARCHY | JSON | NULL | 변경 후 계층 구조 스냅샷 |
| CHANGE_REASON | String(500) | NULL | 변경 사유 |
| CHANGED_AT | DateTime | NOT NULL, DEFAULT now() | 변경 일시 |
| CHANGED_BY | String(50) | NOT NULL | 변경 사용자 |
| CHANGE_SEQUENCE | Integer | NOT NULL, DEFAULT 1 | 변경 순서 |

### Foreign Key 관계
- `PLC_UUID` → `PLC.PLC_UUID`

### 참고
- Hierarchy는 수정되지 않으므로 이 테이블은 실제로 사용되지 않을 수 있음
- 필요시 삭제 고려

---

## 주요 변경 사항 요약

1. **PLC 테이블**
   - `ID` → `PLC_UUID`로 변경
   - 스냅샷 필드 모두 제거 (`*_SNAPSHOT`, `*_CURRENT`)
   - `plant_id`, `process_id`, `line_id`를 직접 FK로 참조 (필수)
   - Equipment Group 관련 필드 제거

2. **CHAT_MESSAGES 테이블**
   - `PLC_ID` → `PLC_UUID`로 변경
   - 스냅샷 필드 모두 제거

3. **PLCHierarchyHistory 테이블**
   - `PLC_ID` → `PLC_UUID`로 변경
   - 하지만 hierarchy는 수정되지 않으므로 사용하지 않을 수 있음

4. **EquipmentGroupMaster 테이블**
   - 더 이상 사용하지 않음 (필요시 삭제 고려)

