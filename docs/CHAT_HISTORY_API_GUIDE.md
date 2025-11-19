# 채팅 히스토리 조회 API 가이드

채팅방의 대화 히스토리(메시지 목록)를 조회하는 API 가이드입니다.

## 목차

1. [대화 히스토리 조회](#1-대화-히스토리-조회)

---

## 1. 대화 히스토리 조회

채팅방의 대화 히스토리(메시지 목록)를 조회합니다.

### 엔드포인트

```
GET /v1/chat/{chat_id}/history
```

### 경로 파라미터

<table>
<thead>
<tr>
<th>파라미터</th>
<th>타입</th>
<th>필수</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>chat_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>조회할 채팅방의 고유 ID</td>
</tr>
</tbody>
</table>

### 조회 우선순위

1. **Redis 캐시에서 먼저 조회** (캐시 히트 시 즉시 반환)
2. Redis에 없거나 실패한 경우 **데이터베이스에서 조회**
3. 조회된 데이터를 **Redis에 캐시 저장** (TTL: 30분)

### 응답 형식

```json
{
  "type": "conversation_history",
  "history": [
    {
      "role": "user",
      "content": "사용자 메시지 내용",
      "timestamp": "2025-01-01T12:00:00+09:00",
      "cancelled": false,
      "message_id": "msg001",
      "plc_uuid": "plc-uuid-001",
      "plc_hierarchy": {
        "plant": {"id": "plant001", "code": "P001", "name": "공장1"},
        "process": {"id": "process001", "code": "PR001", "name": "공정1"},
        "line": {"id": "line001", "code": "L001", "name": "라인1"}
      },
      "plc_snapshot": {
        "plc_uuid": "plc-uuid-001",
        "plc_id": "M1CFB01000",
        "plc_name": "01_01_CELL_FABRICATOR",
        "plant_id": "plant001",
        "plant_name": "공장1",
        "plant_code": "P001",
        "process_id": "process001",
        "process_name": "공정1",
        "process_code": "PR001",
        "line_id": "line001",
        "line_name": "라인1",
        "line_code": "L001",
        "unit": "1",
        "create_dt": "2025-10-31 18:39:00"
      }
    },
    {
      "role": "assistant",
      "content": "AI 응답 내용",
      "timestamp": "2025-01-01T12:00:05+09:00",
      "cancelled": false,
      "message_id": "msg002",
      "plc_uuid": "plc-uuid-001",
      "plc_hierarchy": null,
      "plc_snapshot": null
    }
  ]
}
```

### 응답 필드 설명

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>type</code></td>
<td>string</td>
<td>응답 타입 (<code>"conversation_history"</code>)</td>
</tr>
<tr>
<td><code>history</code></td>
<td>array</td>
<td>메시지 목록 (시간순 정렬)</td>
</tr>
<tr>
<td><code>history[].role</code></td>
<td>string</td>
<td>메시지 역할 (<code>"user"</code>, <code>"assistant"</code>, <code>"system"</code>)</td>
</tr>
<tr>
<td><code>history[].content</code></td>
<td>string</td>
<td>메시지 내용 (텍스트)</td>
</tr>
<tr>
<td><code>history[].timestamp</code></td>
<td>string</td>
<td>메시지 생성 일시 (ISO 8601 형식, Asia/Seoul 타임존)</td>
</tr>
<tr>
<td><code>history[].cancelled</code></td>
<td>boolean</td>
<td>메시지 취소 여부</td>
</tr>
<tr>
<td><code>history[].message_id</code></td>
<td>string</td>
<td>메시지 고유 ID</td>
</tr>
<tr>
<td><code>history[].plc_uuid</code></td>
<td>string</td>
<td>관련 PLC UUID (선택적, null 가능)</td>
</tr>
<tr>
<td><code>history[].plc_hierarchy</code></td>
<td>object</td>
<td>PLC 계층 구조 정보 (선택적, null 가능)</td>
</tr>
<tr>
<td><code>history[].plc_hierarchy.plant</code></td>
<td>object</td>
<td>Plant 정보 (<code>id</code>, <code>code</code>, <code>name</code>)</td>
</tr>
<tr>
<td><code>history[].plc_hierarchy.process</code></td>
<td>object</td>
<td>Process 정보 (<code>id</code>, <code>code</code>, <code>name</code>)</td>
</tr>
<tr>
<td><code>history[].plc_hierarchy.line</code></td>
<td>object</td>
<td>Line 정보 (<code>id</code>, <code>code</code>, <code>name</code>)</td>
</tr>
<tr>
<td><code>history[].plc_snapshot</code></td>
<td>object</td>
<td>PLC 전체 스냅샷 정보 (선택적, null 가능)</td>
</tr>
</tbody>
</table>

### PLC 정보 반환 규칙

#### 1. PLC가 활성화된 경우 (`is_active=true`)

메시지 생성 시점의 PLC 정보를 스냅샷으로 반환합니다:

```json
{
  "plc_uuid": "plc-uuid-001",
  "plc_hierarchy": {
    "plant": {"id": "plant001", "code": "P001", "name": "공장1"},
    "process": {"id": "process001", "code": "PR001", "name": "공정1"},
    "line": {"id": "line001", "code": "L001", "name": "라인1"}
  },
  "plc_snapshot": {
    "plc_uuid": "plc-uuid-001",
    "plc_id": "M1CFB01000",
    "plc_name": "01_01_CELL_FABRICATOR",
    "plant_id": "plant001",
    "plant_name": "공장1",
    "plant_code": "P001",
    "process_id": "process001",
    "process_name": "공정1",
    "process_code": "PR001",
    "line_id": "line001",
    "line_name": "라인1",
    "line_code": "L001",
    "unit": "1",
    "create_dt": "2025-10-31 18:39:00"
  }
}
```

#### 2. PLC가 비활성화된 경우 (`is_active=false`)

PLC 정보를 빈 값(`null`)으로 반환합니다:

```json
{
  "plc_uuid": "plc-uuid-001",
  "plc_hierarchy": null,
  "plc_snapshot": null
}
```

**주의사항:**
- `plc_uuid`는 그대로 반환됩니다 (메시지와의 연결 정보 유지)
- `plc_hierarchy`와 `plc_snapshot`만 `null`로 반환됩니다
- 프론트엔드에서 `plc_hierarchy`와 `plc_snapshot`이 `null`이면 오른쪽 PLC 정보 폼을 비워야 합니다

### 메시지 역할 (`role`)

- `"user"`: 사용자 메시지
- `"assistant"`: AI 응답 메시지
- `"system"`: 시스템 메시지 (취소된 메시지 등)

### 정렬

- 메시지는 생성 일시(`timestamp`) 기준 **오름차순**으로 정렬됩니다
- 가장 오래된 메시지가 첫 번째, 가장 최근 메시지가 마지막에 위치합니다

### 캐싱

- **Redis 캐시 사용** 시 성능 향상
- 캐시 TTL: **30분**
- 캐시 미스 시 자동으로 DB에서 조회 후 캐시 갱신

### 사용 예시

#### 기본 조회
```
GET /v1/chat/chat001/history
```

#### 응답 예시 (활성화된 PLC)
```json
{
  "type": "conversation_history",
  "history": [
    {
      "role": "user",
      "content": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
      "timestamp": "2025-09-24T14:30:00+09:00",
      "cancelled": false,
      "message_id": "msg001",
      "plc_uuid": "plc-uuid-001",
      "plc_hierarchy": {
        "plant": {"id": "KY1", "code": "KY1", "name": "BOSK KY1"},
        "process": {"id": "process001", "code": "PRC1", "name": "공정"},
        "line": {"id": "line001", "code": "LN1", "name": "1라인"}
      },
      "plc_snapshot": {
        "plc_uuid": "plc-uuid-001",
        "plc_id": "M1CFB01000",
        "plc_name": "01_01_CELL_FABRICATOR",
        "plant_id": "KY1",
        "plant_name": "BOSK KY1",
        "plant_code": "KY1",
        "process_id": "process001",
        "process_name": "공정",
        "process_code": "PRC1",
        "line_id": "line001",
        "line_name": "1라인",
        "line_code": "LN1",
        "unit": "1",
        "create_dt": "2025-10-31 18:39:00"
      }
    }
  ]
}
```

#### 응답 예시 (비활성화된 PLC)
```json
{
  "type": "conversation_history",
  "history": [
    {
      "role": "user",
      "content": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
      "timestamp": "2025-09-24T14:30:00+09:00",
      "cancelled": false,
      "message_id": "msg001",
      "plc_uuid": "plc-uuid-001",
      "plc_hierarchy": null,
      "plc_snapshot": null
    }
  ]
}
```

### 에러 응답

```json
{
  "status": "error",
  "code": "ERROR_CODE",
  "message": "에러 메시지",
  "detail": "상세 에러 정보"
}
```

### 주요 에러 코드

- `CHAT_SESSION_NOT_FOUND`: 유효하지 않은 chat_id
- `CHAT_HISTORY_LOAD_ERROR`: 히스토리 조회 중 오류 발생

### 프론트엔드 처리 가이드

#### PLC 정보 표시 로직

```javascript
// 채팅 히스토리 조회
const response = await fetch(`/v1/chat/${chatId}/history`);
const data = await response.json();

// 각 메시지의 PLC 정보 확인
data.history.forEach(msg => {
  if (msg.plc_uuid) {
    if (msg.plc_hierarchy && msg.plc_snapshot) {
      // PLC가 활성화된 경우: PLC 정보 폼에 데이터 표시
      displayPlcInfo(msg.plc_snapshot);
    } else {
      // PLC가 비활성화된 경우: PLC 정보 폼 비우기
      clearPlcInfoForm();
    }
  }
});
```

#### PLC 정보 폼 표시 예시

```javascript
function displayPlcInfo(plcSnapshot) {
  // Plant 드롭다운
  document.getElementById('plantSelect').value = plcSnapshot.plant_id;
  
  // 공정 드롭다운
  document.getElementById('processSelect').value = plcSnapshot.process_id;
  
  // Line 드롭다운
  document.getElementById('lineSelect').value = plcSnapshot.line_id;
  
  // PLC ID
  document.getElementById('plcIdInput').value = plcSnapshot.plc_id;
  
  // PLC 명
  document.getElementById('plcNameInput').value = plcSnapshot.plc_name;
  
  // 등록일시
  document.getElementById('registrationDateInput').value = plcSnapshot.create_dt;
}

function clearPlcInfoForm() {
  // 모든 PLC 정보 필드 초기화
  document.getElementById('plantSelect').value = '';
  document.getElementById('processSelect').value = '';
  document.getElementById('lineSelect').value = '';
  document.getElementById('plcIdInput').value = '';
  document.getElementById('plcNameInput').value = '';
  document.getElementById('registrationDateInput').value = '';
}
```

---

## 참고사항

1. **PLC 스냅샷**: 메시지 생성 시점의 PLC 정보를 저장하므로, 이후 PLC 정보가 변경되어도 히스토리에는 원래 정보가 표시됩니다.
2. **비활성화된 PLC**: `is_active=false`인 PLC는 보안상의 이유로 정보를 표시하지 않습니다. `plc_uuid`만 유지하여 메시지와의 연결 정보를 보존합니다.
3. **캐싱**: Redis 캐시를 사용하면 성능이 향상되지만, 최신 데이터가 필요할 경우 캐시를 무효화해야 할 수 있습니다.
4. **정렬**: 메시지는 항상 시간순으로 정렬되므로, 프론트엔드에서 별도 정렬이 필요 없습니다.

