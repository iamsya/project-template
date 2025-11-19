# 권한 그룹 기반 테이블 스키마

## 개요

사용자가 화면에서 직접 권한 그룹을 생성하고, 사용자와 매핑하는 구조입니다.

### 주요 특징

1. **권한 그룹**: super, plc 등 사용자가 화면에서 직접 생성
2. **메뉴 접근 권한**: 권한 그룹별로 접근 가능한 메뉴 관리 (기준정보, program 탭 등)
3. **공정 권한**: plc 권한그룹의 경우, 접근 가능한 공정을 그룹에 추가
4. **사용자 매핑**: 사용자는 여러 권한 그룹에 속할 수 있음

---

## 1. 권한 그룹 테이블

### 1.1 PERMISSION_GROUPS (권한 그룹)

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

-- 인덱스
CREATE INDEX idx_permission_group_active_deleted ON PERMISSION_GROUPS(IS_ACTIVE, IS_DELETED);
```

**MENU_PERMISSIONS 구조:**
```json
{
    "menus": ["기준정보", "program", "chat", "plc_management"]
}
```

**사용 방법:**
- 프론트엔드에서 사용자의 권한 그룹을 조회하여 `menu_permissions.menus` 배열을 받음
- 이 배열에 포함된 메뉴명만 화면에 표시
- 예: `["기준정보", "program"]`이면 "기준정보"와 "program" 메뉴만 표시

**권한 그룹 예시:**
```sql
-- super 권한 그룹 (기준정보 메뉴 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, MENU_PERMISSIONS, CREATE_USER)
VALUES 
    (
        'group_super',
        'Super 관리자',
        '{"menus": ["기준정보"]}'::json,
        'admin'
    );

-- plc 권한 그룹 (program 탭 등 여러 탭 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, MENU_PERMISSIONS, CREATE_USER)
VALUES 
    (
        'group_plc_001',
        'PLC 관리자 그룹1',
        '{"menus": ["program", "chat", "plc_management"]}'::json,
        'admin'
    );
```

---

## 2. 권한 그룹별 공정 권한 테이블

### 2.1 GROUP_PROCESS_PERMISSIONS (권한 그룹별 공정 권한)

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

-- 인덱스
CREATE UNIQUE INDEX idx_group_process_permission_unique 
    ON GROUP_PROCESS_PERMISSIONS(GROUP_ID, PROCESS_ID);
CREATE INDEX idx_group_process_permission_group_active 
    ON GROUP_PROCESS_PERMISSIONS(GROUP_ID, IS_ACTIVE);
CREATE INDEX idx_group_process_permission_process_active 
    ON GROUP_PROCESS_PERMISSIONS(PROCESS_ID, IS_ACTIVE);
```

**특징:**
- plc 권한그룹의 경우, 접근 가능한 공정을 여기에 추가
- super 권한그룹은 모든 공정에 접근 가능하므로 이 테이블에 데이터가 없을 수 있음

**공정 권한 추가 예시:**
```sql
-- plc 권한 그룹에 공정 권한 추가
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_plc_001', 'process_001', 'admin'),
    ('perm_002', 'group_plc_001', 'process_002', 'admin');
```

---

## 3. 사용자-권한 그룹 매핑 테이블

### 3.1 USER_GROUP_MAPPINGS (사용자-권한 그룹 매핑)

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

-- 인덱스
CREATE UNIQUE INDEX idx_user_group_mapping_unique 
    ON USER_GROUP_MAPPINGS(USER_ID, GROUP_ID);
CREATE INDEX idx_user_group_mapping_user_active 
    ON USER_GROUP_MAPPINGS(USER_ID, IS_ACTIVE);
CREATE INDEX idx_user_group_mapping_group_active 
    ON USER_GROUP_MAPPINGS(GROUP_ID, IS_ACTIVE);
```

**특징:**
- 사용자는 여러 권한 그룹에 속할 수 있음
- 사용자의 최종 권한은 속한 모든 그룹의 권한을 합집합

**사용자 매핑 예시:**
```sql
-- 사용자를 권한 그룹에 매핑
INSERT INTO USER_GROUP_MAPPINGS 
    (MAPPING_ID, USER_ID, GROUP_ID, CREATE_USER)
VALUES 
    ('mapping_001', 'user_001', 'group_super', 'admin'),
    ('mapping_002', 'user_002', 'group_plc_001', 'admin');
```

---

## 4. 권한 조회 로직

### 4.1 사용자의 메뉴 접근 권한 조회

```sql
-- 사용자가 접근 가능한 메뉴 목록 조회
SELECT DISTINCT 
    jsonb_array_elements_text(pg.MENU_PERMISSIONS->'menus') AS menu
FROM USERS u
INNER JOIN USER_GROUP_MAPPINGS ugm ON u.USER_ID = ugm.USER_ID
INNER JOIN PERMISSION_GROUPS pg ON ugm.GROUP_ID = pg.GROUP_ID
WHERE u.USER_ID = 'user_001'
    AND ugm.IS_ACTIVE = true
    AND pg.IS_ACTIVE = true
    AND pg.IS_DELETED = false;
```

### 4.2 사용자의 공정 접근 권한 조회

```sql
-- 사용자가 접근 가능한 공정 목록 조회
-- (super 권한 그룹에 속한 경우 모든 공정, plc 권한 그룹에 속한 경우 지정된 공정만)

-- 방법 1: 모든 공정에 접근 가능한 권한 그룹에 속한 경우
-- (GROUP_PROCESS_PERMISSIONS에 데이터가 없는 그룹은 모든 공정 접근 가능으로 간주)
SELECT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
WHERE pm.IS_ACTIVE = true
    AND EXISTS (
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

UNION

-- 방법 2: plc 권한 그룹에 속한 경우 지정된 공정만 반환
SELECT DISTINCT pm.PROCESS_ID, pm.PROCESS_NAME
FROM PROCESS_MASTER pm
INNER JOIN GROUP_PROCESS_PERMISSIONS gpp ON pm.PROCESS_ID = gpp.PROCESS_ID
INNER JOIN USER_GROUP_MAPPINGS ugm ON gpp.GROUP_ID = ugm.GROUP_ID
WHERE ugm.USER_ID = 'user_001'
    AND ugm.IS_ACTIVE = true
    AND gpp.IS_ACTIVE = true
    AND pm.IS_ACTIVE = true;
```

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

---

## 5. 관리자 편의성

### 5.1 권한 그룹 생성

```sql
-- super 권한 그룹 생성 (기준정보 메뉴만 접근 가능, 모든 공정 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, MENU_PERMISSIONS, CREATE_USER)
VALUES 
    (
        'group_super',
        'Super 관리자',
        '{"menus": ["기준정보"]}'::json,
        'admin'
    );

-- plc 권한 그룹 생성 (여러 메뉴 접근 가능, 특정 공정만 접근 가능)
INSERT INTO PERMISSION_GROUPS 
    (GROUP_ID, GROUP_NAME, MENU_PERMISSIONS, CREATE_USER)
VALUES 
    (
        'group_plc_001',
        'PLC 관리자 그룹1',
        '{"menus": ["program", "chat", "plc_management"]}'::json,
        'admin'
    );
```

### 5.2 권한 그룹에 공정 권한 추가

```sql
-- plc 권한 그룹에 공정 권한 추가
INSERT INTO GROUP_PROCESS_PERMISSIONS 
    (PERMISSION_ID, GROUP_ID, PROCESS_ID, CREATE_USER)
VALUES 
    ('perm_001', 'group_plc_001', 'process_001', 'admin'),
    ('perm_002', 'group_plc_001', 'process_002', 'admin');
```

### 5.3 사용자를 권한 그룹에 매핑

```sql
-- 사용자를 권한 그룹에 매핑
INSERT INTO USER_GROUP_MAPPINGS 
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

