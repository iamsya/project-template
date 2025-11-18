# PLC 계층 구조 스냅샷 설계 문서

## 문제 상황

PLC의 계층 구조(plant, process, line, equipment_group)가 시간에 따라 변경될 수 있습니다.
예를 들어:
- 3일 전: `bosk > 공정 > 1 > cfb`
- 현재: `bosk_ky > 공정 > 1 > cfb123`

채팅 메시지에서 PLC를 참조할 때:
- **과거 채팅**: 생성 시점의 계층 구조를 보존해야 함
- **현재 조회**: 최신 계층 구조를 표시해야 함

## 해결 방안

### 1. ChatMessage 테이블에 스냅샷 필드 추가

```sql
ALTER TABLE CHAT_MESSAGES 
ADD COLUMN PLC_HIERARCHY_SNAPSHOT JSON;
```

### 2. 데이터 저장 형식

```json
{
  "plant": {
    "id": "plant_001",
    "code": "bosk",
    "name": "보스크"
  },
  "process": {
    "id": "process_001",
    "code": "공정",
    "name": "공정"
  },
  "line": {
    "id": "line_001",
    "code": "1",
    "name": "라인 1"
  },
  "equipment_group": {
    "id": "equipment_001",
    "code": "cfb",
    "name": "CFB"
  }
}
```

### 3. 동작 방식

#### 메시지 생성 시
1. `plc_id`가 제공되면 PLC 테이블에서 현재 스냅샷 조회
2. PLC의 `*_snapshot` 필드에서 계층 구조 추출
3. `plc_hierarchy_snapshot` JSON 필드에 저장

#### 메시지 조회 시
1. `plc_hierarchy_snapshot`이 있으면 → **스냅샷 사용** (과거 계층 구조 보존)
2. `plc_hierarchy_snapshot`이 없으면 → PLC 테이블에서 현재 정보 조회 (하위 호환성)

### 4. 구현된 메서드

#### ChatCRUD
- `_get_plc_hierarchy_snapshot(plc_id)`: PLC의 현재 계층 구조 스냅샷 조회
- `create_message()`: `plc_hierarchy_snapshot` 파라미터 추가
- `save_user_message()`: 자동으로 스냅샷 저장
- `save_ai_message()`: 자동으로 스냅샷 저장
- `save_user_message_simple()`: 자동으로 스냅샷 저장
- `save_ai_message_generating()`: 자동으로 스냅샷 저장
- `get_messages_from_db()`: 조회 시 스냅샷 포함

## 사용 예시

### 메시지 생성
```python
# 자동으로 PLC 계층 구조 스냅샷 저장됨
chat_crud.save_user_message(
    message_id="msg_001",
    chat_id="chat_001",
    user_id="user_001",
    message="CFB 장비 상태 확인",
    plc_id="plc_001"  # 스냅샷 자동 저장
)
```

### 메시지 조회
```python
messages = chat_crud.get_messages_from_db("chat_001")
for msg in messages:
    if msg["plc_hierarchy"]:
        # 과거 채팅: 생성 시점의 계층 구조
        # 현재 조회: 최신 계층 구조
        print(msg["plc_hierarchy"])
        # {
        #   "plant": {"code": "bosk", "name": "보스크"},
        #   "process": {"code": "공정", "name": "공정"},
        #   "line": {"code": "1", "name": "라인 1"},
        #   "equipment_group": {"code": "cfb", "name": "CFB"}
        # }
```

## 장점

1. **과거 데이터 보존**: 채팅 메시지 생성 시점의 계층 구조를 영구 보존
2. **현재 정보 반영**: 최신 계층 구조 변경사항도 즉시 반영 가능
3. **하위 호환성**: 기존 메시지(스냅샷 없음)도 현재 PLC 정보로 조회 가능
4. **유연성**: JSON 필드로 확장 가능

## 주의사항

1. **PLC 테이블의 스냅샷 필드**: PLC 생성/수정 시점의 계층 구조가 저장되어야 함
2. **마이그레이션**: 기존 메시지는 스냅샷이 없으므로 조회 시 현재 PLC 정보 사용
3. **성능**: 메시지 생성 시 PLC 조회가 추가되지만, 조회 시에는 스냅샷만 사용하므로 빠름

## PLC 계층 구조가 여러 번 변경될 때

### 문제 상황
PLC의 계층 구조가 여러 번 변경되면:
- 1일차: `bosk > 공정 > 1 > cfb`
- 3일차: `bosk_ky > 공정 > 1 > cfb123`
- 7일차: `bosk_ky > 공정 > 2 > cfb456`

### 해결 방안

#### 1. ChatMessage 스냅샷 (이미 구현됨)
- **메시지 생성 시점의 계층 구조를 영구 보존**
- PLC가 여러 번 변경되어도 각 메시지는 생성 시점의 스냅샷을 유지
- **문제없음**: ChatMessage는 독립적으로 스냅샷을 저장하므로 PLC 변경과 무관

### 데이터 흐름

1. **메시지 생성 시**:
   - PLC 테이블에서 현재 계층 구조 조회
   - ChatMessage에 스냅샷 저장 (영구 보존)

2. **메시지 조회 시**:
   - ChatMessage의 스냅샷 사용 (생성 시점의 계층 구조)
   - PLC 변경과 무관하게 정확한 계층 구조 표시

### 장점

1. **과거 데이터 보존**: ChatMessage는 생성 시점의 계층 구조를 영구 보존
2. **독립성**: ChatMessage 스냅샷은 PLC 변경과 무관하게 유지
3. **PLC Hierarchy는 수정 불가**: 한번 입력된 PLC의 hierarchy는 수정되지 않음

