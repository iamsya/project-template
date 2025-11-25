# 권한 그룹 기반 테이블 스키마

## 개요

사용자가 화면에서 직접 권한 그룹을 생성하고, 사용자와 매핑하는 구조입니다.

### 주요 특징

1. **권한 그룹**: 시스템 관리자, 통합 관리자, 공정 관리자 등 사용자가 화면에서 직접 생성
2. **Role 권한**: 시스템 관리자, 통합 관리자, 공정 관리자 중 단수 선택
3. **공정 권한**: 공정 관리자의 경우, 접근 가능한 공정을 그룹에 추가
4. **사용자 매핑**: 사용자는 여러 권한 그룹에 속할 수 있음
5. **일반 사용자**: 그룹에 속하지 않음 (메뉴 접근 불가, 채팅만 가능)

---

## 1. Role 마스터 테이블

### 1.1 ROLE_MASTER (Role 마스터)

```sql
CREATE TABLE ROLE_MASTER (
    ROLE_ID VARCHAR(50) PRIMARY KEY,  -- system_admin, integrated_admin, process_manager
    ROLE_NAME VARCHAR(100) NOT NULL,   -- 시스템 관리자, 통합관리자, 공정 관리자
    DESCRIPTION TEXT,
    DISPLAY_ORDER INTEGER NOT NULL DEFAULT 0,
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_role_master_active_order 
    ON ROLE_MASTER(IS_ACTIVE, DISPLAY_ORDER);
```

**Role 정보:**
- `system_admin`: 시스템 관리자
  - 기준정보 관리 접근 가능 (조회/편집)
  - 사용자 관리 접근 가능 (조회/편집)
  - 모든 공정 접근 가능 (조회/편집)
  
- `integrated_admin`: 통합관리자
  - 모든 공정 접근 가능 (조회/편집)
  - 기준정보 관리 접근 불가
  - 사용자 관리 접근 불가
  
- `process_manager`: 공정 관리자
  - 그룹에서 지정한 특정 공정만 접근 가능 (조회/편집)
  - 기준정보 관리 접근 불가
  - 사용자 관리 접근 불가

---

## 2. 그룹 테이블

### 2.1 GROUPS (그룹)

```sql
CREATE TABLE GROUPS (
    GROUP_ID VARCHAR(50) PRIMARY KEY,
    GROUP_NAME VARCHAR(100) NOT NULL,
    DESCRIPTION TEXT,
    ROLE_ID VARCHAR(50) NOT NULL REFERENCES ROLE_MASTER(ROLE_ID),  -- Role ID (FK)
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50),
    IS_DELETED BOOLEAN NOT NULL DEFAULT false,
    DELETED_AT TIMESTAMP,
    DELETED_BY VARCHAR(50)
);

-- 인덱스
CREATE INDEX idx_group_active_deleted ON GROUPS(IS_ACTIVE, IS_DELETED);
CREATE INDEX idx_group_role ON GROUPS(ROLE_ID);
```

**Role 타입:**
- `system_admin`: 시스템 관리자
  - 기준정보 관리 접근 가능 (조회/편집)
  - 사용자 관리 접근 가능 (조회/편집)
  - 모든 공정 접근 가능 (조회/편집)
  
- `integrated_admin`: 통합 관리자
  - 모든 공정 접근 가능 (조회/편집)
  - 기준정보 관리 접근 불가
  - 사용자 관리 접근 불가
  
- `process_manager`: 공정 관리자
  - 그룹에서 지정한 특정 공정만 접근 가능 (조회/편집)
  - 기준정보 관리 접근 불가
  - 사용자 관리 접근 불가

**메뉴 접근 권한:**
- 메뉴 접근 권한은 ROLE_ID로 판단합니다
- ROLE_MASTER 테이블에서 Role 정보를 조회합니다

**Role 마스터 초기 데이터:**
```sql
INSERT INTO ROLE_MASTER 
    (ROLE_ID, ROLE_NAME, DESCRIPTION, DISPLAY_ORDER, CREATE_USER)
VALUES 
    (
        'system_admin',
        '시스템 관리자',
        '기준정보 + 사용자관리 + 모든 공정 접근 가능',
        1,
        'admin'
    ),
    (
        'integrated_admin',
        '통합관리자',
        '모든 공정 접근 가능',
        2,
        'admin'
    ),
    (
        'process_manager',
        '공정 관리자',
        '지정한 공정만 접근 가능',
        3,
        'admin'
    );
```

**그룹 예시:**
```sql
-- 시스템 관리자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_system_admin',
        '시스템 관리자',
        'system_admin',
        '시스템 관리자 그룹 - 사용자 관리 및 모든 공정 접근 가능',
        'admin'
    );

-- 통합관리자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_integrated_admin',
        '통합관리자',
        'integrated_admin',
        '통합관리자 그룹 - 모든 공정 접근 가능',
        'admin'
    );

-- 공정 관리자 그룹
INSERT INTO GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE_ID, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_process_manager_001',
        '공정 관리자 그룹1',
        'process_manager',
        '공정 관리자 그룹 - 지정한 공정만 접근 가능',
        'admin'
    );
```

---

## 3. 그룹별 공정 권한 테이블

### 3.1 GROUP_PROCESSES (그룹별 공정 권한)

```sql
CREATE TABLE GROUP_PROCESSES (
    PERMISSION_ID VARCHAR(50) PRIMARY KEY,
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES GROUPS(GROUP_ID),
    PROCESS_ID VARCHAR(50) NOT NULL REFERENCES PROCESS_MASTER(PROCESS_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_group_process_unique 
    ON GROUP_PROCESSES(GROUP_ID, PROCESS_ID);
CREATE INDEX idx_group_process_group_active 
    ON GROUP_PROCESSES(GROUP_ID, IS_ACTIVE);
CREATE INDEX idx_group_process_process_active 
    ON GROUP_PROCESSES(PROCESS_ID, IS_ACTIVE);
```

**특징:**
- plc 권한그룹의 경우, 접근 가능한 공정을 여기에 추가
- super 권한그룹은 모든 공정에 접근 가능하므로 이 테이블에 데이터가 없을 수 있음

**공정 권한 추가 예시:**
```sql
-- plc 권한 그룹에 공정 권한 추가
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_plc_001', 'process_001', 'admin'),
    ('perm_002', 'group_plc_001', 'process_002', 'admin');
```

---

## 4. 사용자-그룹 매핑 테이블

### 4.1 USER_GROUPS (사용자-그룹 매핑)

```sql
CREATE TABLE USER_GROUPS (
    MAPPING_ID VARCHAR(50) PRIMARY KEY,
    USER_ID VARCHAR(50) NOT NULL REFERENCES USERS(USER_ID),
    GROUP_ID VARCHAR(50) NOT NULL REFERENCES GROUPS(GROUP_ID),
    IS_ACTIVE BOOLEAN NOT NULL DEFAULT true,
    CREATE_DT TIMESTAMP NOT NULL DEFAULT NOW(),
    CREATE_USER VARCHAR(50) NOT NULL,
    UPDATE_DT TIMESTAMP,
    UPDATE_USER VARCHAR(50)
);

-- 인덱스
CREATE UNIQUE INDEX idx_user_group_unique 
    ON USER_GROUPS(USER_ID, GROUP_ID);
CREATE INDEX idx_user_group_user_active 
    ON USER_GROUPS(USER_ID, IS_ACTIVE);
CREATE INDEX idx_user_group_group_active 
    ON USER_GROUPS(GROUP_ID, IS_ACTIVE);
```

**특징:**
- 사용자는 여러 권한 그룹에 속할 수 있음
- 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합

**사용자 매핑 예시:**
```sql
-- 사용자를 권한 그룹에 매핑
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_001', 'group_super', 'admin'),
    ('mapping_002', 'user_002', 'group_plc_001', 'admin');
```

---

## 4. 권한 조회 로직

### 4.1 사용자의 Role 확인

```sql
-- 사용자가 속한 그룹의 Role 확인
SELECT DISTINCT pg.ROLE_ID
FROM USERS u
INNER JOIN USER_GROUPS ugm ON u.USER_ID = ugm.USER_ID
INNER JOIN GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
WHERE u.USER_ID = 'user_001'
    AND ugm.IS_ACTIVE = true
    AND pg.IS_ACTIVE = true
    AND pg.IS_DELETED = false;
```

**메뉴 접근 권한:**
- 메뉴 접근 권한은 ROLE로 판단합니다
- `system_admin`: 기준정보 + 사용자관리 + 모든 공정 접근 가능
- `integrated_admin`: 모든 공정 접근 가능
- `process_manager`: 지정한 공정만 접근 가능
- 일반 사용자 (그룹 없음): 메뉴 접근 불가, 채팅만 가능

### 4.2 사용자의 공정 접근 권한 조회

```sql
-- 사용자가 접근 가능한 공정 목록 조회
-- (시스템 관리자/통합 관리자: 모든 공정, 공정 관리자: 지정된 공정만)

-- 방법 1: 시스템 관리자 또는 통합 관리자인 경우 모든 공정 반환
SELECT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
WHERE pm.IS_ACTIVE = true
    AND EXISTS (
        SELECT 1
        FROM USER_GROUPS ugm
        INNER JOIN GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
        WHERE ugm.USER_ID = 'user_001'
            AND ugm.IS_ACTIVE = true
            AND pg.IS_ACTIVE = true
            AND pg.IS_DELETED = false
            AND pg.ROLE_ID IN ('system_admin', 'integrated_admin')
    )

UNION

-- 방법 2: 공정 관리자인 경우 지정된 공정만 반환
SELECT DISTINCT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
INNER JOIN GROUP_PROCESSES gpp ON pm.PROCESS_ID = gpp.PROCESS_ID
INNER JOIN USER_GROUPS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
INNER JOIN GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
WHERE ugm.USER_ID = 'user_001'
    AND ugm.IS_ACTIVE = true
    AND gpp.IS_ACTIVE = true
    AND pm.IS_ACTIVE = true
    AND pg.ROLE_ID = 'process_manager';
```
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
read_file

### 4.3 사용자 권한 기반 PLC 목록 조회

```sql
-- 사용자가 접근 가능한 PLC 목록 조회
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
WHERE p.IS_ACTIVE = true
    AND pm.IS_ACTIVE = true
    AND prm.IS_ACTIVE = true
    AND lm.IS_ACTIVE = true
    AND (
        -- 시스템 관리자 또는 통합 관리자인 경우 모든 공정의 PLC
        EXISTS (
            SELECT 1
            FROM USER_GROUP_MAPPINGS ugm
            INNER JOIN PERMISSION_GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
            WHERE ugm.USER_ID = 'user_001'
                AND ugm.IS_ACTIVE = true
                AND pg.IS_ACTIVE = true
                AND pg.IS_DELETED = false
                AND pg.ROLE IN ('system_admin', 'integrated_admin')
        )
        OR
        -- 공정 관리자인 경우 지정된 공정의 PLC만
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

## 5. 관리자 편의성

### 5.1 권한 그룹 생성

```sql
-- 시스템 관리자 그룹 생성 (기준정보 + 사용자관리 + 모든 공정 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_system_admin',
        '시스템 관리자',
        'system_admin',
        '시스템 관리자 그룹 - 사용자 관리 및 모든 공정 접근 가능',
        'admin'
    );

-- 통합 관리자 그룹 생성 (모든 공정 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_integrated_admin',
        '통합 관리자',
        'integrated_admin',
        '통합 관리자 그룹 - 모든 공정 접근 가능',
        'admin'
    );

-- 공정 관리자 그룹 생성 (지정한 공정만 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, ROLE, DESCRIPTION, CREATE_USER)
VALUES 
    (
        'group_process_manager_001',
        '공정 관리자 그룹1',
        'process_manager',
        '공정 관리자 그룹 - 지정한 공정만 접근 가능',
        'admin'
    );
```

### 5.2 권한 그룹에 공정 권한 추가

```sql
-- 공정 관리자 그룹에 공정 권한 추가
INSERT INTO GROUP_PROCESSES 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_process_manager_001', 'process_001', 'admin'),
    ('perm_002', 'group_plc_001', 'process_002', 'admin');
```

### 5.3 사용자를 권한 그룹에 매핑

```sql
-- 사용자를 권한 그룹에 매핑
INSERT INTO USER_GROUPS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_001', 'group_super', 'admin');
```

---

## 6. 주요 특징

1. **권한 그룹 기반 관리**: 사용자가 화면에서 직접 권한 그룹을 생성하고 관리
2. **메뉴 접근 권한**: 권한 그룹별로 접근 가능한 메뉴를 JSON으로 관리
3. **공정 권한**: plc 권한그룹의 경우, 접근 가능한 공정을 그룹에 추가
4. **사용자 매핑**: 사용자는 여러 권한 그룹에 속할 수 있으며, 모든 그룹의 권한을 합집합으로 가짐
5. **모든 공정 접근**: GROUP_PROCESS_PERMISSIONS에 데이터가 없는 권한 그룹은 모든 공정에 접근 가능

---

## 7. 기존 테이블과의 관계

### 7.1 USERS 테이블
- 기존 USERS 테이블 유지
- USER_GROUP_MAPPINGS를 통해 권한 그룹과 매핑

### 7.2 삭제된 테이블
- **USER_PROCESS_PERMISSIONS**: 권한 그룹 기반 구조로 변경되어 삭제됨

