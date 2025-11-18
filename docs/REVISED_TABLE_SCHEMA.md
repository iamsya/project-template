# 개정된 테이블 스키마

## 개요

요구사항에 맞춰 테이블 스키마를 재설계했습니다.

### 주요 변경사항

1. **권한 그룹 기반 관리**: `PERMISSION_GROUPS`, `GROUP_PROCESS_PERMISSIONS`, `USER_GROUP_MAPPINGS` 테이블 추가
2. **채팅 메시지 Hierarchy 스냅샷**: `CHAT_MESSAGES`에 `plc_hierarchy_snapshot` 필드 추가
3. **PLC Hierarchy 구조**: plant → 공정 → line → plc명 → 호기 → plc_id

---

## 1. 마스터 테이블 (기준정보)

### 1.1 PLANT_MASTER (공장 마스터)

```sql
CREATE TABLE PLANT_MASTER (
    PLANT_ID VARCHAR(50) PRIMARY KEY,
    PLANT_CODE VARCHAR(50) UNIQUE NOT NULL,
    PLANT_NAME VARCHAR(255) NOT NULL,
    DESCRIPTION TEXT,
    DISPLAY_ORDER INTEGER DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    METADATA_JSON JSON,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_plant_master_active_order ON PLANT_MASTER(IS_ACTIVE, DISPLAY_ORDER);
CREATE INDEX idx_plant_master_active ON PLANT_MASTER(IS_ACTIVE);
```

**관리자 쿼리 예시:**
```sql
-- 추가
INSERT INTO PLANT_MASTER (PLANT_ID, PLANT_CODE, PLANT_NAME, CREATE_USER)
VALUES ('plant_001', 'P001', '공장1', 'admin');

-- 변경
UPDATE PLANT_MASTER 
SET PLANT_NAME = '공장1-수정', UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PLANT_ID = 'plant_001';

-- 삭제 (소프트 삭제)
UPDATE PLANT_MASTER 
SET IS_ACTIVE = false, UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PLANT_ID = 'plant_001';
```

### 1.2 PROCESS_MASTER (공정 마스터)

```sql
CREATE TABLE PROCESS_MASTER (
    PROCESS_ID VARCHAR(50) PRIMARY KEY,
    PROCESS_CODE VARCHAR(50) UNIQUE NOT NULL,
    PROCESS_NAME VARCHAR(255) NOT NULL,
    PLANT_ID VARCHAR(50) NOT NULL REFERENCES PLANT_MASTER(PLANT_ID),
    DESCRIPTION TEXT,
    DISPLAY_ORDER INTEGER DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    METADATA_JSON JSON,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_process_master_plant_active ON PROCESS_MASTER(PLANT_ID, IS_ACTIVE);
CREATE INDEX idx_process_master_active_order ON PROCESS_MASTER(IS_ACTIVE, DISPLAY_ORDER);
CREATE INDEX idx_process_master_active ON PROCESS_MASTER(IS_ACTIVE);
```

**관리자 쿼리 예시:**
```sql
-- 추가
INSERT INTO PROCESS_MASTER (PROCESS_ID, PROCESS_CODE, PROCESS_NAME, PLANT_ID, CREATE_USER)
VALUES ('process_001', 'PR001', '공정1', 'plant_001', 'admin');

-- 변경
UPDATE PROCESS_MASTER 
SET PROCESS_NAME = '공정1-수정', UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PROCESS_ID = 'process_001';

-- 삭제 (소프트 삭제)
UPDATE PROCESS_MASTER 
SET IS_ACTIVE = false, UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PROCESS_ID = 'process_001';
```

### 1.3 LINE_MASTER (라인 마스터)

```sql
CREATE TABLE LINE_MASTER (
    LINE_ID VARCHAR(50) PRIMARY KEY,
    LINE_CODE VARCHAR(50) UNIQUE NOT NULL,
    LINE_NAME VARCHAR(255) NOT NULL,
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    DESCRIPTION TEXT,
    DISPLAY_ORDER INTEGER DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    METADATA_JSON JSON,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_line_master_active_order ON LINE_MASTER(IS_ACTIVE, DISPLAY_ORDER);
CREATE INDEX idx_line_master_active ON LINE_MASTER(IS_ACTIVE);
```

**관리자 쿼리 예시:**
```sql
-- 추가
INSERT INTO LINE_MASTER (LINE_ID, LINE_NAME, CREATE_USER)
VALUES ('line_001', '라인1', 'admin');

-- 변경
UPDATE LINE_MASTER 
SET LINE_NAME = '라인1-수정', UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE LINE_ID = 'line_001';

-- 삭제 (소프트 삭제)
UPDATE LINE_MASTER 
SET IS_ACTIVE = false, UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE LINE_ID = 'line_001';
```

---

## 2. 권한 그룹 테이블

### 2.1 PERMISSION_GROUPS (권한 그룹)

```sql
CREATE TABLE PERMISSION_GROUPS (
    GROUP_ID VARCHAR(50) PRIMARY KEY,
    GROUP_NAME VARCHAR(100) NOT NULL,
    DESCRIPTION TEXT,
    MENU_PERMISSIONS JSON,  -- 접근 가능한 메뉴명 리스트
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50),
    IS_DELETED BOOLEAN NOT NULL DEFAULT false,
    DELETED_AT TIMESTAMP,
    DELETED_BY VARCHAR(50)
);
```

**특징:**
- 사용자가 화면에서 직접 권한 그룹을 생성
- `MENU_PERMISSIONS`: 접근 가능한 메뉴명 리스트 (JSON)
  - 예: `{"menus": ["기준정보", "program", "chat"]}`
  - 프론트엔드에서 이 값을 받아서 해당 메뉴들만 표시

### 2.2 GROUP_PROCESS_PERMISSIONS (권한 그룹별 공정 권한)

```sql
CREATE TABLE GROUP_PROCESS_PERMISSIONS (
    PERMISSION_ID VARCHAR(50) PRIMARY KEY,
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES PERMISSION_GROUPS(GROUP_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);
```

**특징:**
- 권한 그룹에 접근 가능한 공정을 여기에 추가
- 이 테이블에 데이터가 없는 권한 그룹은 모든 공정에 접근 가능

### 2.3 USER_GROUP_MAPPINGS (사용자-권한 그룹 매핑)

```sql
CREATE TABLE USER_GROUP_MAPPINGS (
    MAPPING_ID VARCHAR(50) PRIMARY KEY,
    USER_ID VARCHAR(50) NOT NULL REFERENCES USERS(USER_ID),
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES PERMISSION_GROUPS(GROUP_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);
```

**특징:**
- 사용자는 여러 권한 그룹에 속할 수 있음
- 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합

---

## 3. 사용자 권한 테이블 (삭제됨)

### 3.1 USER_PROCESS_PERMISSIONS (삭제됨)

**변경 사항:**
- 권한 그룹 기반 구조로 변경되어 삭제됨
- 대신 `PERMISSION_GROUPS`, `GROUP_PROCESS_PERMISSIONS`, `USER_GROUP_MAPPINGS` 테이블 사용

---

## 4. PLC 테이블

### 4.1 PLC (PLC 기준 정보)

```sql
CREATE TABLE PLC (
    PLC_UUID VARCHAR(50) PRIMARY KEY,
    
    -- Hierarchy: Plant → 공정 → Line (마스터 데이터, 드롭다운 선택)
    PLANT_ID VARCHAR(50) NOT NULL REFERENCES PLANT_MASTER(PLANT_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    LINE_ID VARCHAR(50) NOT NULL REFERENCES LINE_MASTER(LINE_ID),
    
    -- Hierarchy: PLC명 → 호기 → PLC ID (사용자 직접 입력)
    PLC_NAME VARCHAR(255) NOT NULL,
    UNIT VARCHAR(100),
    PLC_ID VARCHAR(50) NOT NULL,
    
    -- Program 매핑
    PROGRAM_ID VARCHAR(50) REFERENCES PROGRAMS(PROGRAM_ID) UNIQUE,
    MAPPING_DT TIMESTAMP,
    MAPPING_USER VARCHAR(50),
    
    -- 활성화 여부 (deprecated: is_deleted 사용)
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    
    -- 삭제 관리
    IS_DELETED BOOLEAN NOT NULL DEFAULT false,
    DELETED_AT TIMESTAMP,
    DELETED_BY VARCHAR(50),
    
    -- 메타데이터
    METADATA_JSON JSON,
    
    -- 등록 정보
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_plc_plant_id ON PLC(PLANT_ID);
CREATE INDEX idx_plc_process_id ON PLC(PROCESS_ID);
CREATE INDEX idx_plc_line_id ON PLC(LINE_ID);
CREATE INDEX idx_plc_plc_id ON PLC(PLC_ID);
CREATE INDEX idx_plc_program_id ON PLC(PROGRAM_ID);
```

**Hierarchy 구조:**
- **마스터 데이터 (드롭다운 선택)**: Plant → 공정 → Line
- **사용자 입력**: PLC명 → 호기(Unit) → PLC ID
- **Line이 마지막 depth**

**PLC 등록 예시:**
```sql
-- 사용자가 화면에서 입력
-- 1. Plant 드롭다운에서 선택: 'plant_001'
-- 2. 공정 드롭다운에서 선택: 'process_001'
-- 3. Line 드롭다운에서 선택: 'line_001'
-- 4. PLC명 입력: 'MAS PLC'
-- 5. 호기 입력: '1'
-- 6. PLC ID 입력: 'PLC001'

INSERT INTO PLC 
    (PLC_UUID, PLANT_ID, PROCESS_ID, LINE_ID, PLC_NAME, UNIT, PLC_ID, CREATE_USER)
VALUES 
    ('plc_uuid_001', 'plant_001', 'process_001', 'line_001', 'MAS PLC', '1', 'PLC001', 'user_001');
```

---

## 5. 채팅 테이블

### 5.1 CHAT_MESSAGES (채팅 메시지)

```sql
CREATE TABLE CHAT_MESSAGES (
    MESSAGE_ID VARCHAR(50) PRIMARY KEY,
    CHAT_ID VARCHAR(50) NOT NULL REFERENCES CHATS(CHAT_ID),
    USER_ID VARCHAR(50) NOT NULL,
    MESSAGE TEXT NOT NULL,
    MESSAGE_TYPE VARCHAR(20) NOT NULL,
    STATUS VARCHAR(20),
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    IS_DELETED BOOLEAN NOT NULL DEFAULT false,
    IS_CANCELLED BOOLEAN NOT NULL DEFAULT false,
    
    -- PLC 연결
    PLC_UUID VARCHAR(50) REFERENCES PLC(PLC_UUID),
    
    -- Hierarchy 스냅샷 (채팅 메시지 저장 시점의 hierarchy 정보)
    -- plant, 공정, line은 업데이트될 수 있지만, 채팅 메시지에는 그때 사용했던 정보를 저장
    PLC_HIERARCHY_SNAPSHOT JSON,
    
    -- External API 노드 처리 결과
    EXTERNAL_API_NODES JSON
);

-- 인덱스
CREATE INDEX idx_chat_messages_chat_id ON CHAT_MESSAGES(CHAT_ID);
CREATE INDEX idx_chat_messages_plc_uuid ON CHAT_MESSAGES(PLC_UUID);
```

**PLC_HIERARCHY_SNAPSHOT 구조:**
```json
{
    "plant_id": "plant_001",
    "plant_name": "공장1",
    "process_id": "process_001",
    "process_name": "공정1",
    "line_id": "line_001",
    "line_name": "라인1",
    "plc_name": "MAS PLC",
    "unit": "1",
    "plc_id": "PLC001"
}
```

**채팅 메시지 저장 예시:**
```sql
-- 채팅 메시지 저장 시 hierarchy 스냅샷도 함께 저장
INSERT INTO CHAT_MESSAGES 
    (MESSAGE_ID, CHAT_ID, USER_ID, MESSAGE, MESSAGE_TYPE, PLC_UUID, PLC_HIERARCHY_SNAPSHOT)
VALUES 
    (
        'msg_001',
        'chat_001',
        'user_001',
        'PLC 프로그램을 확인해주세요',
        'user',
        'plc_uuid_001',
        '{
            "plant_id": "plant_001",
            "plant_name": "공장1",
            "process_id": "process_001",
            "process_name": "공정1",
            "line_id": "line_001",
            "line_name": "라인1",
            "plc_name": "MAS PLC",
            "unit": "1",
            "plc_id": "PLC001"
        }'::json
    );
```

---

## 6. 조회 권한 필터링

### 6.1 권한 그룹 기반 조회

**PLC 목록 조회 (권한이 있는 공정만):**
```sql
SELECT 
    p.PLC_UUID,
    p.PLC_ID,
    p.PLC_NAME,
    p.UNIT,
    pm.PLANT_NAME,
    prm.PROCESS_NAME,
    lm.LINE_NAME
FROM PLC p
INNER JOIN PLANT_MASTER pm ON p.PLANT_ID = pm.PLANT_ID
INNER JOIN PROCESS_MASTER prm ON p.PROCESS_ID = prm.PROCESS_ID
INNER JOIN LINE_MASTER lm ON p.LINE_ID = lm.LINE_ID
WHERE p.IS_DELETED = false
    AND pm.IS_ACTIVE = true
    AND prm.IS_ACTIVE = true
    AND lm.IS_ACTIVE = true
    AND (
        -- 모든 공정에 접근 가능한 권한 그룹에 속한 경우
        -- (GROUP_PROCESS_PERMISSIONS에 데이터가 없는 그룹은 모든 공정 접근 가능)
        EXISTS (
            SELECT 1
            FROM USER_GROUP_MAPPINGS ugm
            INNER JOIN PERMISSION_GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
            LEFT JOIN GROUP_PROCESS_PERMISSIONS gpp ON pg.GROUP_ID = gpp.GROUP_ID
            WHERE ugm.USER_ID = 'user_001'
                AND ugm.IS_ACTIVE = true
                AND pg.IS_ACTIVE = true
                AND pg.IS_DELETED = false
                AND gpp.PERMISSION_ID IS NULL  -- 공정 권한이 없으면 모든 공정 접근 가능
        )
        OR
        -- plc 권한 그룹에 속한 경우 지정된 공정의 PLC만
        EXISTS (
            SELECT 1
            FROM GROUP_PROCESS_PERMISSIONS gpp
            INNER JOIN USER_GROUP_MAPPINGS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
            WHERE ugm.USER_ID = 'user_001'
                AND ugm.IS_ACTIVE = true
                AND gpp.PROCESS_ID = p.PROCESS_ID
                AND gpp.IS_ACTIVE = true
        )
    );
```

**프로그램 목록 조회 (권한이 있는 공정만):**
```sql
SELECT 
    pr.PROGRAM_ID,
    pr.PROGRAM_NAME,
    pr.DESCRIPTION,
    p.PLC_ID,
    p.PLC_NAME
FROM PROGRAMS pr
INNER JOIN PLC p ON pr.PROGRAM_ID = p.PROGRAM_ID
WHERE pr.IS_DELETED = false
    AND p.IS_DELETED = false
    AND (
        -- super 권한 그룹에 속한 경우 모든 공정의 프로그램
        EXISTS (
            SELECT 1
            FROM USER_GROUP_MAPPINGS ugm
            INNER JOIN PERMISSION_GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
            WHERE ugm.USER_ID = 'user_001'
                AND ugm.IS_ACTIVE = true
                AND pg.GROUP_TYPE = 'super'
                AND pg.IS_ACTIVE = true
                AND pg.IS_DELETED = false
        )
        OR
        -- plc 권한 그룹에 속한 경우 지정된 공정의 프로그램만
        EXISTS (
            SELECT 1
            FROM GROUP_PROCESS_PERMISSIONS gpp
            INNER JOIN USER_GROUP_MAPPINGS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
            WHERE ugm.USER_ID = 'user_001'
                AND ugm.IS_ACTIVE = true
                AND gpp.PROCESS_ID = p.PROCESS_ID
                AND gpp.IS_ACTIVE = true
        )
    );
```

---

## 7. 관리자 편의성

### 7.1 마스터 데이터 관리 쿼리

**공장 추가:**
```sql
INSERT INTO PLANT_MASTER (PLANT_ID, PLANT_CODE, PLANT_NAME, CREATE_USER)
VALUES ('plant_002', 'P002', '공장2', 'admin');
```

**공정 추가:**
```sql
INSERT INTO PROCESS_MASTER (PROCESS_ID, PROCESS_CODE, PROCESS_NAME, PLANT_ID, CREATE_USER)
VALUES ('process_002', 'PR002', '공정2', 'plant_001', 'admin');
```

**라인 추가:**
```sql
INSERT INTO LINE_MASTER (LINE_ID, LINE_NAME, CREATE_USER)
VALUES ('line_002', '라인2', 'admin');
```

**공정 이름 변경:**
```sql
UPDATE PROCESS_MASTER 
SET PROCESS_NAME = '공정1-신규명', UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PROCESS_ID = 'process_001';
```

**공정 비활성화 (소프트 삭제):**
```sql
UPDATE PROCESS_MASTER 
SET IS_ACTIVE = false, UPDATE_USER = 'admin', UPDATE_DT = NOW()
WHERE PROCESS_ID = 'process_001';
```

---

## 8. 주요 특징

1. **권한 그룹 기반 관리**: 사용자가 화면에서 직접 권한 그룹을 생성하고 관리
2. **메뉴 접근 권한**: 권한 그룹별로 접근 가능한 메뉴를 JSON으로 관리
3. **공정 권한**: plc 권한그룹의 경우, 접근 가능한 공정을 그룹에 추가
4. **사용자 매핑**: 사용자는 여러 권한 그룹에 속할 수 있으며, 모든 그룹의 권한을 합집합으로 가짐
5. **모든 공정 접근**: GROUP_PROCESS_PERMISSIONS에 데이터가 없는 권한 그룹은 모든 공정에 접근 가능
6. **Hierarchy 구조**: plant → 공정 → line (마스터) → plc명 → 호기 → plc_id (사용자 입력)
7. **채팅 메시지 스냅샷**: 채팅 메시지 저장 시점의 hierarchy 정보를 JSON으로 저장하여, 이후 마스터 데이터가 변경되어도 당시 정보를 유지
8. **관리자 편의성**: 마스터 테이블은 단순한 구조로 관리자가 쿼리로 쉽게 추가/변경/삭제 가능

