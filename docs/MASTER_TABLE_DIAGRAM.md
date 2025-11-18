# 마스터 테이블 구조 다이어그램

## 테이블 관계도

```
┌─────────────────────────────────┐
│      PLANT_MASTER               │
│  (공장 기준정보 마스터)          │
├─────────────────────────────────┤
│ PK  PLANT_ID (String(50))       │
│     PLANT_NAME (String(255))    │
│     DESCRIPTION (Text)           │
│     IS_ACTIVE (Boolean)         │
│     METADATA_JSON (JSON)         │
│     CREATE_DT (DateTime)         │
│     CREATE_USER (String(50))     │
│     UPDATE_DT (DateTime)         │
│     UPDATE_USER (String(50))     │
└─────────────────────────────────┘
           │
           │ (FK 참조)
           │
           ▼
┌─────────────────────────────────┐
│         PLC                     │
│  (PLC 기준정보 및 Program 매핑)  │
├─────────────────────────────────┤
│ PK  PLC_UUID (String(50))       │
│ FK  PLANT_ID → PLANT_MASTER     │
│ FK  PROCESS_ID → PROCESS_MASTER │
│ FK  LINE_ID → LINE_MASTER       │
│ FK  PROGRAM_ID → PROGRAMS        │
│     PLC_NAME (String(255))      │
│     PLC_ID (String(50))         │
│     UNIT (String(100))          │
│     IS_ACTIVE (Boolean)         │
│     IS_DELETED (Boolean)        │
│     DELETED_AT (DateTime)       │
│     DELETED_BY (String(50))     │
│     METADATA_JSON (JSON)         │
│     MAPPING_DT (DateTime)        │
│     MAPPING_USER (String(50))    │
│     CREATE_DT (DateTime)         │
│     CREATE_USER (String(50))     │
│     UPDATE_DT (DateTime)         │
│     UPDATE_USER (String(50))     │
└─────────────────────────────────┘
           ▲
           │ (FK 참조)
           │
┌─────────────────────────────────┐
│    PROCESS_MASTER               │
│  (공정 기준정보 마스터)          │
├─────────────────────────────────┤
│ PK  PROCESS_ID (String(50))     │
│     PROCESS_NAME (String(255))  │
│     DESCRIPTION (Text)           │
│     IS_ACTIVE (Boolean)         │
│     METADATA_JSON (JSON)         │
│     CREATE_DT (DateTime)         │
│     CREATE_USER (String(50))     │
│     UPDATE_DT (DateTime)         │
│     UPDATE_USER (String(50))     │
└─────────────────────────────────┘
           │
           │ (FK 참조)
           │
           ▼
┌─────────────────────────────────┐
│         PLC                     │
│  (위와 동일)                    │
└─────────────────────────────────┘
           ▲
           │ (FK 참조)
           │
┌─────────────────────────────────┐
│      LINE_MASTER                │
│  (라인 기준정보 마스터)          │
├─────────────────────────────────┤
│ PK  LINE_ID (String(50))        │
│     LINE_NAME (String(255))     │
│     DESCRIPTION (Text)           │
│     IS_ACTIVE (Boolean)         │
│     METADATA_JSON (JSON)         │
│     CREATE_DT (DateTime)         │
│     CREATE_USER (String(50))     │
│     UPDATE_DT (DateTime)         │
│     UPDATE_USER (String(50))     │
└─────────────────────────────────┘
```

## 계층 구조

```
PLANT_MASTER (독립적)
    │
    ├──→ PLC (FK: PLANT_ID)
    │
PROCESS_MASTER (독립적)
    │
    ├──→ PLC (FK: PROCESS_ID)
    │
LINE_MASTER (독립적)
    │
    ├──→ PLC (FK: LINE_ID)
    │
PROGRAMS (독립적)
    │
    └──→ PLC (FK: PROGRAM_ID, UNIQUE)
```

## 특징

### 1. 독립적인 마스터 테이블
- **PLANT_MASTER**: 공장 정보 (독립적)
- **PROCESS_MASTER**: 공정 정보 (독립적, Plant와 무관)
- **LINE_MASTER**: 라인 정보 (독립적, Process와 무관)

### 2. PLC 테이블의 역할
- **PLC** 테이블이 모든 마스터 테이블을 참조하여 계층 구조를 구성
- Plant, Process, Line을 조합하여 PLC를 식별
- Program과 1:1 매핑 (UNIQUE 제약)

### 3. 관계 특성
- **Plant ↔ Process**: 독립적 (종속 관계 없음)
- **Process ↔ Line**: 독립적 (종속 관계 없음)
- **PLC → Plant, Process, Line**: 다중 FK 참조 (조합으로 계층 구성)

## 테이블별 상세 구조

### PLANT_MASTER (공장 기준정보 마스터)
```
컬럼명              타입           제약조건      설명
─────────────────────────────────────────────────────────
PLANT_ID           String(50)     PK           공장 ID
PLANT_NAME         String(255)    NOT NULL     공장명
DESCRIPTION        Text           NULL         설명
IS_ACTIVE          Boolean        NOT NULL     활성화 여부
METADATA_JSON      JSON           NULL         메타데이터
CREATE_DT          DateTime       NOT NULL     생성 일시
CREATE_USER        String(50)     NOT NULL     생성자
UPDATE_DT          DateTime       NULL         수정 일시
UPDATE_USER        String(50)     NULL         수정자

인덱스:
- idx_plant_master_active (IS_ACTIVE)
```

### PROCESS_MASTER (공정 기준정보 마스터)
```
컬럼명              타입           제약조건      설명
─────────────────────────────────────────────────────────
PROCESS_ID         String(50)     PK           공정 ID
PROCESS_NAME       String(255)    NOT NULL     공정명
DESCRIPTION        Text           NULL         설명
IS_ACTIVE          Boolean        NOT NULL     활성화 여부
METADATA_JSON      JSON           NULL         메타데이터
CREATE_DT          DateTime       NOT NULL     생성 일시
CREATE_USER        String(50)     NOT NULL     생성자
UPDATE_DT          DateTime       NULL         수정 일시
UPDATE_USER        String(50)     NULL         수정자

인덱스:
- idx_process_master_active (IS_ACTIVE)
```

### LINE_MASTER (라인 기준정보 마스터)
```
컬럼명              타입           제약조건      설명
─────────────────────────────────────────────────────────
LINE_ID            String(50)     PK           라인 ID
LINE_NAME          String(255)    NOT NULL     라인명
DESCRIPTION        Text           NULL         설명
IS_ACTIVE          Boolean        NOT NULL     활성화 여부
METADATA_JSON      JSON           NULL         메타데이터
CREATE_DT          DateTime       NOT NULL     생성 일시
CREATE_USER        String(50)     NOT NULL     생성자
UPDATE_DT          DateTime       NULL         수정 일시
UPDATE_USER        String(50)     NULL         수정자

인덱스:
- idx_line_master_active (IS_ACTIVE)
```

### PLC (PLC 기준정보 및 Program 매핑)
```
컬럼명              타입           제약조건      설명
─────────────────────────────────────────────────────────
PLC_UUID           String(50)     PK           PLC UUID (자동 생성)
PLANT_ID           String(50)     FK, NOT NULL Plant ID
PROCESS_ID         String(50)     FK, NOT NULL 공정 ID
LINE_ID            String(50)     FK, NOT NULL Line ID
PROGRAM_ID         String(50)     FK, UNIQUE   Program ID (1:1 매핑)
PLC_NAME           String(255)    NOT NULL     PLC명
PLC_ID             String(50)     NOT NULL     PLC 식별자
UNIT               String(100)    NULL         호기
IS_ACTIVE          Boolean        NOT NULL     활성화 여부 (deprecated)
IS_DELETED         Boolean        NOT NULL     삭제 여부
DELETED_AT         DateTime       NULL         삭제 일시
DELETED_BY         String(50)     NULL         삭제자
METADATA_JSON      JSON           NULL         메타데이터
MAPPING_DT         DateTime       NULL         매핑 일시
MAPPING_USER       String(50)     NULL         매핑 사용자
CREATE_DT          DateTime       NOT NULL     생성 일시
CREATE_USER        String(50)     NOT NULL     생성자
UPDATE_DT          DateTime       NULL         수정 일시
UPDATE_USER        String(50)     NULL         수정자

인덱스:
- PLANT_ID
- PROCESS_ID
- LINE_ID
- PROGRAM_ID
- PLC_ID
- IS_DELETED

Foreign Keys:
- PLANT_ID → PLANT_MASTER.PLANT_ID
- PROCESS_ID → PROCESS_MASTER.PROCESS_ID
- LINE_ID → LINE_MASTER.LINE_ID
- PROGRAM_ID → PROGRAMS.PROGRAM_ID (UNIQUE)
```

## 데이터 흐름

### 1. 마스터 데이터 관리
```
운영자 입력
    │
    ├──→ PLANT_MASTER (공장 등록)
    ├──→ PROCESS_MASTER (공정 등록, Plant와 무관)
    └──→ LINE_MASTER (라인 등록, Process와 무관)
```

### 2. PLC 등록
```
사용자 입력
    │
    ├──→ Plant 선택 (PLANT_MASTER에서 드롭다운)
    ├──→ Process 선택 (PROCESS_MASTER에서 드롭다운)
    ├──→ Line 선택 (LINE_MASTER에서 드롭다운)
    ├──→ PLC명 입력
    ├──→ 호기 입력 (선택사항)
    └──→ PLC ID 입력
         │
         └──→ PLC 테이블에 저장
              (PLANT_ID, PROCESS_ID, LINE_ID 조합)
```

### 3. Program 매핑
```
PLC 등록 후
    │
    └──→ Program 선택
         │
         └──→ PLC.PROGRAM_ID 업데이트
              (1:1 매핑, UNIQUE 제약)
```

## 주요 특징 요약

1. **독립적인 마스터 테이블**
   - Plant, Process, Line이 서로 종속되지 않음
   - 재사용 가능한 구조

2. **PLC를 통한 계층 구성**
   - PLC 테이블이 모든 마스터를 참조
   - Plant + Process + Line 조합으로 계층 구조 형성

3. **Program과의 1:1 매핑**
   - PLC 1개당 Program 1개만 매핑 가능
   - UNIQUE 제약으로 보장

4. **소프트 삭제 지원**
   - IS_DELETED 플래그로 삭제 관리
   - IS_ACTIVE는 deprecated

