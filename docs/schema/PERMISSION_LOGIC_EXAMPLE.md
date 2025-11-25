# 권한 체크 로직 상세 설명 (데이터 예시)

## 1. 테이블 데이터 예시

### 1.1 USERS 테이블

| USER_ID | EMPLOYEE_ID | NAME | IS_ACTIVE | IS_DELETED |
|---------|-------------|------|-----------|------------|
| user_sys_admin | SO10001 | 김관리 | true | false |
| user_integrated_admin | SO10002 | 이통합 | true | false |
| user_process_manager_001 | SO10003 | 박모듈 | true | false |
| user_process_manager_002 | SO10004 | 최화성 | true | false |
| user_normal | SO10005 | 정일반 | true | false |

### 1.2 PROCESS_MASTER 테이블

| PROCESS_ID | PROCESS_NAME | IS_ACTIVE |
|------------|--------------|-----------|
| prc_module | 모듈 | true |
| prc_hwaseong | 화성 | true |
| prc_electrode | 전극 | true |
| prc_assembly | 조립 | true |

### 1.3 ROLE_MASTER 테이블

| ROLE_ID | ROLE_NAME | DESCRIPTION | DISPLAY_ORDER | IS_ACTIVE |
|---------|-----------|-------------|---------------|-----------|
| system_admin | 시스템 관리자 | 기준정보 + 사용자관리 + 모든 공정 접근 가능 | 1 | true |
| integrated_admin | 통합관리자 | 모든 공정 접근 가능 | 2 | true |
| process_manager | 공정 관리자 | 지정한 공정만 접근 가능 | 3 | true |

### 1.4 GROUPS 테이블

| GROUP_ID | GROUP_NAME | ROLE_ID | IS_ACTIVE | IS_DELETED |
|----------|------------|---------|-----------|------------|
| group_system_admin | 시스템 관리자 | system_admin | true | false |
| group_integrated_admin | 통합관리자 | integrated_admin | true | false |
| group_process_manager_001 | 공정 관리자 그룹1 | process_manager | true | false |
| group_process_manager_002 | 공정 관리자 그룹2 | process_manager | true | false |

**참고:** 
- 화면에 보이는 Role은 3개뿐: 시스템 관리자, 통합관리자, 공정 관리자
- 공정 관리자 그룹은 여러 개 생성 가능하며, 각 그룹에 여러 공정을 지정할 수 있음
- ROLE_ID는 ROLE_MASTER 테이블을 참조

### 1.5 USER_GROUPS 테이블

| MAPPING_ID | USER_ID | GROUP_ID | IS_ACTIVE |
|------------|---------|----------|-----------|
| mapping_001 | user_sys_admin | group_system_admin | true |
| mapping_002 | user_integrated_admin | group_integrated_admin | true |
| mapping_003 | user_process_manager_001 | group_process_manager_001 | true |
| mapping_004 | user_process_manager_002 | group_process_manager_002 | true |

**참고:** 
- `user_normal`은 이 테이블에 없음 (일반 사용자)
- 사용자는 여러 그룹에 속할 수 있지만, 예시에서는 하나의 그룹에만 속하도록 설정

### 1.6 GROUP_PROCESSES 테이블

| PERMISSION_ID | GROUP_ID | PROCESS_ID | IS_ACTIVE |
|---------------|----------|------------|-----------|
| perm_001 | group_process_manager_001 | prc_module | true |
| perm_002 | group_process_manager_001 | prc_hwaseong | true |
| perm_003 | group_process_manager_002 | prc_electrode | true |
| perm_004 | group_process_manager_002 | prc_assembly | true |

**참고:** 
- `group_system_admin`, `group_integrated_admin`는 이 테이블에 데이터 없음 (모든 공정 접근 가능)
- `group_process_manager_001`: 모듈, 화성 공정 접근 가능 (2개 공정 지정)
- `group_process_manager_002`: 전극, 조립 공정 접근 가능 (2개 공정 지정)
- **하나의 공정 관리자 그룹에 여러 공정을 조합하여 지정할 수 있음**

---

## 2. 메뉴 접근 권한 체크 로직

### 2.1 기준정보 관리 메뉴 접근 체크

**로직:**
```python
def can_access_master_management(user_id: str) -> bool:
    # 1. 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(UserGroupMapping.user_id == user_id)
        .filter(UserGroupMapping.is_active == True)
        .filter(PermissionGroup.is_active == True)
        .filter(PermissionGroup.is_deleted == False)
        .all()
    )
    
    # 2. 그룹 중 하나라도 system_admin role이 있으면 접근 가능
    return any(group.role == PermissionGroup.ROLE_SYSTEM_ADMIN for group in groups)
```

**예시 1: user_sys_admin (시스템 관리자)**
```
1. USER_GROUPS 조회
   → mapping_001: user_sys_admin → group_system_admin (IS_ACTIVE=true)

2. GROUPS 조회
   → group_system_admin: ROLE = 'system_admin'

3. role == 'system_admin'? 
   → Yes ✅
   
결과: 기준정보 관리 메뉴 접근 가능
```

**예시 2: user_integrated_admin (통합관리자)**
```
1. USER_GROUPS 조회
   → mapping_002: user_integrated_admin → group_integrated_admin (IS_ACTIVE=true)

2. GROUPS 조회
   → group_integrated_admin: ROLE = 'integrated_admin'

3. role == 'system_admin'? 
   → No ❌
   
결과: 기준정보 관리 메뉴 접근 불가
```

**예시 3: user_normal (일반 사용자)**
```
1. USER_GROUPS 조회
   → 조회 결과 없음 (테이블에 없음)

2. groups = [] (빈 리스트)

3. any(...) 
   → False ❌
   
결과: 기준정보 관리 메뉴 접근 불가
```

### 2.2 사용자 관리 메뉴 접근 체크

**로직:** 기준정보 관리와 동일 (system_admin만 접근 가능)

**예시:**
- `user_sys_admin`: ✅ 접근 가능
- `user_integrated_admin`: ❌ 접근 불가
- `user_process_manager_001`: ❌ 접근 불가
- `user_normal`: ❌ 접근 불가

### 2.3 공정 관련 메뉴 접근 체크

**로직:**
```python
def can_access_process_menu(user_id: str) -> bool:
    # 1. 사용자가 속한 활성 그룹 조회
    groups = get_user_groups(user_id)
    
    # 2. 그룹이 없으면 접근 불가 (일반 사용자)
    if not groups:
        return False
    
    # 3. system_admin, integrated_admin, process_manager 중 하나라도 있으면 접근 가능
    valid_roles = [
        PermissionGroup.ROLE_SYSTEM_ADMIN,
        PermissionGroup.ROLE_INTEGRATED_ADMIN,
        PermissionGroup.ROLE_PROCESS_MANAGER
    ]
    return any(group.role in valid_roles for group in groups)
```

**예시:**
- `user_sys_admin`: ✅ 접근 가능 (system_admin)
- `user_integrated_admin`: ✅ 접근 가능 (integrated_admin)
- `user_process_manager_001`: ✅ 접근 가능 (process_manager)
- `user_normal`: ❌ 접근 불가 (그룹 없음)

---

## 3. 공정 접근 권한 체크 로직

### 3.1 사용자가 접근 가능한 공정 목록 조회

**로직:** `get_accessible_process_ids(user_id)`

```python
def get_accessible_process_ids(user_id: str) -> Optional[List[str]]:
    # 1. 사용자가 속한 활성 그룹 조회
    groups = (
        db.query(PermissionGroup)
        .join(UserGroupMapping, PermissionGroup.group_id == UserGroupMapping.group_id)
        .filter(UserGroupMapping.user_id == user_id)
        .filter(UserGroupMapping.is_active == True)
        .filter(PermissionGroup.is_active == True)
        .filter(PermissionGroup.is_deleted == False)
        .all()
    )
    
    # 2. 그룹이 없으면 접근 불가
    if not groups:
        return []  # 일반 사용자: 접근 불가
    
    # 3. 시스템 관리자 또는 통합 관리자: 모든 공정 접근 가능
    for group in groups:
        if group.role in [ROLE_SYSTEM_ADMIN, ROLE_INTEGRATED_ADMIN]:
            return None  # None = 모든 공정 접근 가능
    
    # 4. 공정 관리자: GROUP_PROCESS_PERMISSIONS에 지정된 공정만
    accessible_process_ids = set()
    for group in groups:
        if group.role == ROLE_PROCESS_MANAGER:
            process_permissions = (
                db.query(GroupProcessPermission)
                .filter(GroupProcessPermission.group_id == group.group_id)
                .filter(GroupProcessPermission.is_active == True)
                .all()
            )
            accessible_process_ids.update([pp.process_id for pp in process_permissions])
    
    return list(accessible_process_ids) if accessible_process_ids else []
```

**예시 1: user_sys_admin (시스템 관리자)**
```
1. USER_GROUPS 조회
   → mapping_001: user_sys_admin → group_system_admin

2. GROUPS 조회
   → group_system_admin: ROLE = 'system_admin'

3. role in [system_admin, integrated_admin]?
   → Yes ✅
   
4. return None (모든 공정 접근 가능)

결과: None (모든 공정 접근 가능)
   → prc_module, prc_hwaseong, prc_electrode, prc_assembly 모두 접근 가능
```

**예시 2: user_integrated_admin (통합관리자)**
```
1. USER_GROUPS 조회
   → mapping_002: user_integrated_admin → group_integrated_admin

2. GROUPS 조회
   → group_integrated_admin: ROLE = 'integrated_admin'

3. role in [system_admin, integrated_admin]?
   → Yes ✅
   
4. return None (모든 공정 접근 가능)

결과: None (모든 공정 접근 가능)
   → prc_module, prc_hwaseong, prc_electrode, prc_assembly 모두 접근 가능
```

**예시 3: user_process_manager_001 (공정 관리자 - 하나의 그룹에 여러 공정 지정)**
```
1. USER_GROUPS 조회
   → mapping_003: user_process_manager_001 → group_process_manager_001

2. GROUPS 조회
   → group_process_manager_001: ROLE_ID = 'process_manager'

3. role_id in [system_admin, integrated_admin]?
   → No ❌

4. 공정 관리자 처리:
   - GROUP_PROCESS_PERMISSIONS 조회
     → perm_001: group_process_manager_001 → prc_module
     → perm_002: group_process_manager_001 → prc_hwaseong
   - accessible_process_ids = {'prc_module', 'prc_hwaseong'}

5. return ['prc_module', 'prc_hwaseong']

결과: ['prc_module', 'prc_hwaseong'] (2개 공정 접근 가능)
   → 하나의 공정 관리자 그룹에 여러 공정을 조합하여 지정할 수 있음
```

**예시 4: user_process_manager_002 (공정 관리자 - 다른 그룹)**
```
1. USER_GROUPS 조회
   → mapping_004: user_process_manager_002 → group_process_manager_002

2. GROUPS 조회
   → group_process_manager_002: ROLE = 'process_manager'

3. role in [system_admin, integrated_admin]?
   → No ❌

4. 공정 관리자 처리:
   - GROUP_PROCESS_PERMISSIONS 조회
     → perm_003: group_process_manager_002 → prc_electrode
     → perm_004: group_process_manager_002 → prc_assembly
   - accessible_process_ids = {'prc_electrode', 'prc_assembly'}

5. return ['prc_electrode', 'prc_assembly']

결과: ['prc_electrode', 'prc_assembly'] (2개 공정 접근 가능)
```

**예시 5: user_normal (일반 사용자)**
```
1. USER_GROUPS 조회
   → 조회 결과 없음 (테이블에 없음)

2. groups = [] (빈 리스트)

3. if not groups: return []

결과: [] (접근 가능한 공정 없음)
```

### 3.2 특정 공정 접근 권한 체크

**로직:** `can_access_process(user_id, process_id)`

```python
def can_access_process(user_id: str, process_id: str) -> bool:
    # 1. 접근 가능한 공정 목록 조회
    accessible_process_ids = get_accessible_process_ids(user_id)
    
    # 2. None이면 모든 공정 접근 가능
    if accessible_process_ids is None:
        return True
    
    # 3. 빈 리스트면 접근 불가
    if not accessible_process_ids:
        return False
    
    # 4. 해당 공정이 목록에 있는지 확인
    return process_id in accessible_process_ids
```

**예시 1: user_sys_admin가 prc_module 접근 시도**
```
1. get_accessible_process_ids('user_sys_admin')
   → None (모든 공정 접근 가능)

2. if accessible_process_ids is None: return True

결과: ✅ 접근 허용
```

**예시 2: user_process_manager_001이 prc_hwaseong 접근 시도**
```
1. get_accessible_process_ids('user_process_manager_001')
   → ['prc_module', 'prc_hwaseong']

2. if accessible_process_ids is None: False
3. if not accessible_process_ids: False
4. return 'prc_hwaseong' in ['prc_module', 'prc_hwaseong']
   → True

결과: ✅ 접근 허용
```

**예시 3: user_process_manager_001이 prc_electrode 접근 시도**
```
1. get_accessible_process_ids('user_process_manager_001')
   → ['prc_module', 'prc_hwaseong']

2. return 'prc_electrode' in ['prc_module', 'prc_hwaseong']
   → False

결과: ❌ 접근 거부
```

---

## 4. 전체 권한 체크 흐름도 (데이터 예시)

### 4.1 사용자 관리 메뉴 접근 시도

```
사용자: user_integrated_admin
요청: GET /api/user-management/users

1. USER_GROUPS 조회
   → mapping_002: user_integrated_admin → group_integrated_admin

2. GROUPS 조회
   → group_integrated_admin: ROLE = 'integrated_admin'

3. role == 'system_admin'?
   → No ❌

결과: 403 Forbidden
   "사용자 관리 기능에 접근할 권한이 없습니다. 시스템 관리자만 접근 가능합니다."
```

### 4.2 공정 데이터 조회 시도

```
사용자: user_process_manager_001
요청: GET /api/programs?process_id=prc_module

1. get_accessible_process_ids('user_process_manager_001')
   → ['prc_module', 'prc_hwaseong']

2. can_access_process('user_process_manager_001', 'prc_module')
   → 'prc_module' in ['prc_module', 'prc_hwaseong']
   → True ✅

결과: 200 OK (프로그램 목록 반환)
```

```
사용자: user_process_manager_001
요청: GET /api/programs?process_id=prc_electrode

1. get_accessible_process_ids('user_process_manager_001')
   → ['prc_module', 'prc_hwaseong']

2. can_access_process('user_process_manager_001', 'prc_electrode')
   → 'prc_electrode' in ['prc_module', 'prc_hwaseong']
   → False ❌

결과: 403 Forbidden
   "해당 공정에 접근할 권한이 없습니다."
```

```
사용자: user_process_manager_002
요청: GET /api/programs?process_id=prc_electrode

1. get_accessible_process_ids('user_process_manager_002')
   → ['prc_electrode', 'prc_assembly']

2. can_access_process('user_process_manager_002', 'prc_electrode')
   → 'prc_electrode' in ['prc_electrode', 'prc_assembly']
   → True ✅

결과: 200 OK (프로그램 목록 반환)
```

### 4.3 일반 사용자 채팅 접근 시도

```
사용자: user_normal
요청: GET /api/chat/rooms

1. USER_GROUPS 조회
   → 조회 결과 없음

2. groups = []

3. 공정 메뉴 접근 체크
   → any(...) = False ❌

결과: 공정 관련 메뉴는 접근 불가

하지만 채팅 API는 별도 권한 체크 없이 접근 가능
→ 200 OK (채팅방 목록 반환)
```

---

## 5. 권한 체크 요약표

| 사용자 | 기준정보 | 사용자관리 | 공정 메뉴 | 접근 가능한 공정 |
|--------|---------|-----------|-----------|-----------------|
| user_sys_admin | ✅ | ✅ | ✅ | 모든 공정 (None) |
| user_integrated_admin | ❌ | ❌ | ✅ | 모든 공정 (None) |
| user_process_manager_001 | ❌ | ❌ | ✅ | prc_module, prc_hwaseong (2개) |
| user_process_manager_002 | ❌ | ❌ | ✅ | prc_electrode, prc_assembly (2개) |
| user_normal | ❌ | ❌ | ❌ | 없음 ([]) |

---

## 6. 코드 실행 예시

### 6.1 user_sys_admin의 권한 체크

```python
# 1. 메뉴 접근 권한
can_access_master_management('user_sys_admin')
→ True ✅

can_access_user_management('user_sys_admin')
→ True ✅

can_access_process_menu('user_sys_admin')
→ True ✅

# 2. 공정 접근 권한
get_accessible_process_ids('user_sys_admin')
→ None (모든 공정 접근 가능)

can_access_process('user_sys_admin', 'prc_module')
→ True ✅

can_access_process('user_sys_admin', 'prc_electrode')
→ True ✅
```

### 6.2 user_process_manager_001의 권한 체크

```python
# 1. 메뉴 접근 권한
can_access_master_management('user_process_manager_001')
→ False ❌

can_access_user_management('user_process_manager_001')
→ False ❌

can_access_process_menu('user_process_manager_001')
→ True ✅

# 2. 공정 접근 권한
get_accessible_process_ids('user_process_manager_001')
→ ['prc_module', 'prc_hwaseong']

can_access_process('user_process_manager_001', 'prc_module')
→ True ✅

can_access_process('user_process_manager_001', 'prc_hwaseong')
→ True ✅

can_access_process('user_process_manager_001', 'prc_electrode')
→ False ❌
```

### 6.3 user_normal의 권한 체크

```python
# 1. 메뉴 접근 권한
can_access_master_management('user_normal')
→ False ❌

can_access_user_management('user_normal')
→ False ❌

can_access_process_menu('user_normal')
→ False ❌

# 2. 공정 접근 권한
get_accessible_process_ids('user_normal')
→ [] (접근 불가)

can_access_process('user_normal', 'prc_module')
→ False ❌
```

---

## 7. 핵심 포인트

1. **화면에 보이는 Role은 3개뿐**
   - 시스템 관리자 (`system_admin`): 기준정보 + 사용자관리 + 모든 공정 접근 가능
   - 통합관리자 (`integrated_admin`): 모든 공정 접근 가능
   - 공정 관리자 (`process_manager`): 지정한 공정만 접근 가능
   - 일반 사용자 (그룹 없음): 모든 메뉴 접근 불가, 채팅만 가능

2. **메뉴 접근 권한은 ROLE로 판단**
   - `system_admin`: 기준정보 + 사용자관리 + 공정 메뉴 접근 가능
   - `integrated_admin`: 공정 메뉴만 접근 가능
   - `process_manager`: 공정 메뉴만 접근 가능
   - 일반 사용자 (그룹 없음): 모든 메뉴 접근 불가

3. **공정 접근 권한은 ROLE + GROUP_PROCESS_PERMISSIONS로 판단**
   - `system_admin`, `integrated_admin`: 모든 공정 접근 가능 (GROUP_PROCESS_PERMISSIONS 확인 불필요)
   - `process_manager`: **하나의 그룹에 여러 공정을 조합하여 지정 가능** (GROUP_PROCESS_PERMISSIONS에 여러 공정 추가)
   - 일반 사용자: 접근 불가

4. **공정 관리자 그룹은 여러 개 생성 가능**
   - 각 그룹마다 다른 공정 조합을 지정할 수 있음
   - 사용자가 여러 그룹에 속한 경우, 공정 접근 권한은 합집합

5. **일반 사용자는 USER_GROUP_MAPPINGS에 없음**
   - 모든 권한 체크에서 False 반환
   - 채팅 기능만 별도 권한 체크 없이 접근 가능

