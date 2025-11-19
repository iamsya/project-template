# Chat API 가이드

채팅 관련 API 가이드입니다.

## 목차

1. [메시지 전송 및 AI 응답 (비스트리밍)](#1-메시지-전송-및-ai-응답-비스트리밍)
2. [메시지 전송 및 AI 응답 (스트리밍)](#2-메시지-전송-및-ai-응답-스트리밍)
3. [대화 히스토리 조회](#3-대화-히스토리-조회)

---

## 1. 메시지 전송 및 AI 응답 (비스트리밍)

사용자 메시지를 전송하고 AI 응답을 받습니다. 응답은 완전히 생성된 후 한 번에 반환됩니다.

### 엔드포인트

```
POST /v1/chat/{chat_id}/message
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
<td>채팅방의 고유 ID</td>
</tr>
</tbody>
</table>

### 요청 Body

```json
{
  "type": "user_message",
  "message": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
  "user_id": "user001",
  "plc_uuid": "plc-uuid-001"
}
```

### 요청 필드

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>필수</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>type</code></td>
<td>string</td>
<td>아니오</td>
<td>메시지 타입 (기본값: <code>"user_message"</code>)</td>
</tr>
<tr>
<td><code>message</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>사용자 메시지 (1~4000자)</td>
</tr>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td>아니오</td>
<td>사용자 ID (기본값: <code>"user"</code>)</td>
</tr>
<tr>
<td><code>plc_uuid</code></td>
<td>string</td>
<td>아니오</td>
<td>PLC UUID (PLC 테이블의 PLC_UUID, 선택사항)</td>
</tr>
</tbody>
</table>

### 응답 형식

```json
{
  "message_id": "msg001",
  "content": "AI 응답 내용이 여기에 표시됩니다...",
  "user_id": "ai",
  "timestamp": "2025-01-01T12:00:05+09:00"
}
```

### 응답 필드

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
<td><code>message_id</code></td>
<td>string</td>
<td>AI 응답 메시지의 고유 ID</td>
</tr>
<tr>
<td><code>content</code></td>
<td>string</td>
<td>AI 응답 내용</td>
</tr>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td>사용자 ID (항상 <code>"ai"</code>)</td>
</tr>
<tr>
<td><code>timestamp</code></td>
<td>string</td>
<td>응답 생성 일시 (ISO 8601 형식, Asia/Seoul 타임존)</td>
</tr>
</tbody>
</table>

### 동작 방식

1. 사용자 메시지가 데이터베이스에 저장됩니다
2. AI가 메시지를 처리하고 응답을 생성합니다
3. AI 응답이 완전히 생성된 후 한 번에 반환됩니다
4. AI 응답도 데이터베이스에 저장됩니다

### 사용 예시

```bash
curl -X POST "http://localhost:8000/v1/chat/chat001/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
    "user_id": "user001",
    "plc_uuid": "plc-uuid-001"
  }'
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
- `MESSAGE_PROCESSING_ERROR`: 메시지 처리 중 오류 발생
- `VALIDATION_ERROR`: 입력값 검증 오류 (메시지 길이 등)

---

## 2. 메시지 전송 및 AI 응답 (스트리밍)

사용자 메시지를 전송하고 AI 응답을 스트리밍 방식으로 받습니다 (Server-Sent Events, SSE). 응답이 생성되는 동안 실시간으로 청크 단위로 받을 수 있습니다.

### 엔드포인트

```
POST /v1/chat/{chat_id}/stream
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
<td>채팅방의 고유 ID</td>
</tr>
</tbody>
</table>

### 요청 Body

```json
{
  "type": "user_message",
  "message": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
  "user_id": "user001",
  "plc_uuid": "plc-uuid-001"
}
```

### 요청 필드

<table>
<thead>
<tr>
<th>필드</th>
<th>타입</th>
<th>필수</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>type</code></td>
<td>string</td>
<td>아니오</td>
<td>메시지 타입 (기본값: <code>"user_message"</code>)</td>
</tr>
<tr>
<td><code>message</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>사용자 메시지 (1~4000자)</td>
</tr>
<tr>
<td><code>user_id</code></td>
<td>string</td>
<td>아니오</td>
<td>사용자 ID (기본값: <code>"user"</code>)</td>
</tr>
<tr>
<td><code>plc_uuid</code></td>
<td>string</td>
<td>아니오</td>
<td>PLC UUID (PLC 테이블의 PLC_UUID, 선택사항)</td>
</tr>
</tbody>
</table>

### 응답 형식 (SSE)

응답은 Server-Sent Events (SSE) 형식으로 스트리밍됩니다. 각 이벤트는 `data: ` 접두사와 함께 JSON 형식으로 전송됩니다.

#### 1. 사용자 메시지 이벤트

```
data: {"type":"user_message","message_id":"msg001","content":"사용자 메시지 내용","user_id":"user001","timestamp":"2025-01-01T12:00:00+09:00"}

```

#### 2. Heartbeat 이벤트 (10초마다)

처리 시간이 길어질 경우, 10초마다 진행 상황을 알리는 heartbeat 메시지가 전송됩니다.

```
data: {"type":"heartbeat","message":"사용자의 의도를 파악하고 있습니다...","timestamp":"2025-01-01T12:00:10+09:00"}

```

Heartbeat 메시지:
- 10초: "사용자의 의도를 파악하고 있습니다..."
- 30초: "정확한 답변을 찾기 위해 노력하고 있습니다..."
- 50초 이후: "거의 다 완료되었습니다. 조금만 기다려주세요..."

#### 3. AI 응답 청크 이벤트

AI 응답이 생성되는 동안 청크 단위로 전송됩니다.

```
data: {"type":"ai_response_chunk","content":"AI","message_id":"msg002","timestamp":"2025-01-01T12:00:05+09:00"}

data: {"type":"ai_response_chunk","content":" 응답","message_id":"msg002","timestamp":"2025-01-01T12:00:05+09:00"}

data: {"type":"ai_response_chunk","content":" 내용","message_id":"msg002","timestamp":"2025-01-01T12:00:05+09:00"}

```

#### 4. AI 응답 완료 이벤트

AI 응답이 완전히 생성되면 완료 이벤트가 전송됩니다.

```
data: {"type":"ai_response","message_id":"msg002","content":"AI 응답 내용이 여기에 표시됩니다...","user_id":"ai","timestamp":"2025-01-01T12:00:05+09:00"}

```

#### 5. 에러 이벤트

에러가 발생하면 에러 이벤트가 전송됩니다.

```
data: {"type":"error","code":1001,"message":"에러 메시지","content":"사용자에게 표시할 에러 내용","timestamp":"2025-01-01T12:00:05+09:00","chat_id":"chat001"}

```

### 이벤트 타입

<table>
<thead>
<tr>
<th>타입</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>user_message</code></td>
<td>사용자 메시지 저장 완료</td>
</tr>
<tr>
<td><code>heartbeat</code></td>
<td>진행 상황 알림 (10초마다)</td>
</tr>
<tr>
<td><code>ai_response_chunk</code></td>
<td>AI 응답 청크 (부분 응답)</td>
</tr>
<tr>
<td><code>ai_response</code></td>
<td>AI 응답 완료</td>
</tr>
<tr>
<td><code>error</code></td>
<td>에러 발생</td>
</tr>
</tbody>
</table>

### 동작 방식

1. 사용자 메시지가 데이터베이스에 저장됩니다
2. 사용자 메시지 이벤트가 전송됩니다
3. AI가 메시지를 처리하기 시작합니다
4. 처리 시간이 길어지면 heartbeat 메시지가 10초마다 전송됩니다
5. AI 응답이 생성되는 동안 청크 단위로 전송됩니다
6. AI 응답이 완전히 생성되면 완료 이벤트가 전송됩니다
7. AI 응답이 데이터베이스에 저장됩니다

### 사용 예시

#### JavaScript

```javascript
const chatId = 'chat001';
const message = '선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘';
const userId = 'user001';
const plcUuid = 'plc-uuid-001';

// POST 요청으로 스트림 시작
const response = await fetch(`/v1/chat/${chatId}/stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: message,
    user_id: userId,
    plc_uuid: plcUuid
  })
});

// 스트림 읽기
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.substring(6));
      
      switch (data.type) {
        case 'user_message':
          console.log('사용자 메시지 저장됨:', data);
          break;
        case 'heartbeat':
          console.log('진행 상황:', data.message);
          break;
        case 'ai_response_chunk':
          // 청크를 화면에 추가
          appendToChat(data.content);
          break;
        case 'ai_response':
          console.log('AI 응답 완료:', data);
          break;
        case 'error':
          console.error('에러 발생:', data);
          break;
      }
    }
  }
}
```

#### cURL

```bash
curl -X POST "http://localhost:8000/v1/chat/chat001/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "선택한 PLC Ladder ○○○ 기능이 구현되어 있는지 확인해줘",
    "user_id": "user001",
    "plc_uuid": "plc-uuid-001"
  }' \
  --no-buffer
```

### 주의사항

1. **연결 유지**: 스트리밍 연결은 AI 응답이 완료될 때까지 유지됩니다
2. **Heartbeat**: 처리 시간이 길어지면 10초마다 heartbeat 메시지가 전송되어 연결이 끊어지지 않도록 합니다
3. **에러 처리**: 에러가 발생해도 스트림이 끊어지지 않고 에러 이벤트가 전송됩니다
4. **청크 누적**: `ai_response_chunk` 이벤트의 `content`를 누적하여 완전한 응답을 구성해야 합니다

---

## 3. 대화 히스토리 조회

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
        "plant": {"id": "plant001", "name": "공장1"},
        "process": {"id": "process001", "name": "공정1"},
        "line": {"id": "line001", "name": "라인1"}
      },
      "plc_snapshot": {
        "plc_uuid": "plc-uuid-001",
        "plc_id": "M1CFB01000",
        "plc_name": "01_01_CELL_FABRICATOR",
        "plant_id": "plant001",
        "plant_name": "공장1",
        "process_id": "process001",
        "process_name": "공정1",
        "line_id": "line001",
        "line_name": "라인1",
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
<td><code>history[].plc_snapshot</code></td>
<td>object</td>
<td>PLC 전체 스냅샷 정보 (선택적, null 가능)</td>
</tr>
</tbody>
</table>

### PLC 정보 반환 규칙

#### 1. PLC가 활성화된 경우 (`is_deleted=false`)

메시지 생성 시점의 PLC 정보를 스냅샷으로 반환합니다.

```json
{
  "plc_uuid": "plc-uuid-001",
  "plc_hierarchy": {
    "plant": {"id": "plant001", "name": "공장1"},
    "process": {"id": "process001", "name": "공정1"},
    "line": {"id": "line001", "name": "라인1"}
  },
  "plc_snapshot": {
    "plc_uuid": "plc-uuid-001",
    "plc_id": "M1CFB01000",
    "plc_name": "01_01_CELL_FABRICATOR",
    "plant_id": "plant001",
    "plant_name": "공장1",
    "process_id": "process001",
    "process_name": "공정1",
    "line_id": "line001",
    "line_name": "라인1",
    "unit": "1",
    "create_dt": "2025-10-31 18:39:00"
  }
}
```

#### 2. PLC가 비활성화된 경우 (`is_deleted=true` 또는 `is_active=false`)

PLC 정보를 빈 값(`null`)으로 반환합니다.

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

```bash
curl -X GET "http://localhost:8000/v1/chat/chat001/history"
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

---

## 참고사항

1. **메시지 저장**: 사용자 메시지와 AI 응답은 모두 데이터베이스에 자동으로 저장됩니다
2. **PLC 정보**: `plc_uuid`를 제공하면 메시지와 함께 PLC 정보가 저장됩니다
3. **스트리밍 vs 비스트리밍**: 
   - **비스트리밍**: 응답이 완전히 생성된 후 한 번에 받습니다 (간단하지만 대기 시간이 길 수 있음)
   - **스트리밍**: 응답이 생성되는 동안 실시간으로 받습니다 (사용자 경험이 좋지만 구현이 복잡함)
4. **PLC 스냅샷**: 메시지 생성 시점의 PLC 정보를 저장하므로, 이후 PLC 정보가 변경되어도 히스토리에는 원래 정보가 표시됩니다
5. **비활성화된 PLC**: `is_deleted=true`인 PLC는 보안상의 이유로 정보를 표시하지 않습니다. `plc_uuid`만 유지하여 메시지와의 연결 정보를 보존합니다
6. **캐싱**: Redis 캐시를 사용하면 성능이 향상되지만, 최신 데이터가 필요할 경우 캐시를 무효화해야 할 수 있습니다
