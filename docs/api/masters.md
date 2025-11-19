# Masters API 가이드

Masters 라우터의 모든 API 엔드포인트 가이드입니다.

## 목차

1. [권한 기반 마스터 데이터 조회 (드롭다운용)](#1-권한-기반-마스터-데이터-조회-드롭다운용)
2. [공정 목록 조회](#2-공정-목록-조회)

---

## 1. 권한 기반 마스터 데이터 조회 (드롭다운용)

사용자 권한에 따라 접근 가능한 마스터 데이터를 조회합니다.

### 엔드포인트

```
GET /v1/masters
```

### 쿼리 파라미터

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
<td><code>user_id</code></td>
<td>string</td>
<td><strong>예</strong></td>
<td>사용자 ID (권한 기반 필터링용)</td>
</tr>
</tbody>
</table>

### 권한 기반 필터링

- `user_id`는 필수 파라미터입니다
- 사용자의 권한 그룹에 따라 접근 가능한 공정의 마스터 데이터만 조회됩니다
  - **super 권한 그룹**: 모든 활성 Process 반환
  - **plc 권한 그룹**: 지정된 Process만 반환
  - **권한이 없으면**: Process 목록이 비어있음
- Plant와 Line은 모든 활성 데이터를 반환합니다
- Process는 권한에 따라 필터링됩니다

### 응답 형식

```json
{
  "plants": [
    {
      "id": "plant_001",
      "code": "plant_001",
      "name": "Plant 1"
    },
    {
      "id": "plant_002",
      "code": "plant_002",
      "name": "Plant 2"
    }
  ],
  "processesByPlant": {
    "plant_001": [
      {
        "id": "process_001",
        "code": "process_001",
        "name": "모듈"
      },
      {
        "id": "process_002",
        "code": "process_002",
        "name": "전극"
      }
    ],
    "plant_002": [
      {
        "id": "process_003",
        "code": "process_003",
        "name": "조립"
      }
    ]
  },
  "linesByProcess": {
    "process_001": [
      {
        "id": "line_001",
        "code": "line_001",
        "name": "1라인"
      },
      {
        "id": "line_002",
        "code": "line_002",
        "name": "2라인"
      }
    ],
    "process_002": [
      {
        "id": "line_003",
        "code": "line_003",
        "name": "1라인"
      }
    ]
  }
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
<td><code>plants</code></td>
<td>array</td>
<td>Plant 목록 (모든 활성 Plant)</td>
</tr>
<tr>
<td><code>plants[].id</code></td>
<td>string</td>
<td>Plant ID</td>
</tr>
<tr>
<td><code>plants[].code</code></td>
<td>string</td>
<td>Plant 코드 (id와 동일)</td>
</tr>
<tr>
<td><code>plants[].name</code></td>
<td>string</td>
<td>Plant 이름</td>
</tr>
<tr>
<td><code>processesByPlant</code></td>
<td>object</td>
<td>Plant ID를 키로 하는 Process 목록 맵 (권한 필터링 적용)</td>
</tr>
<tr>
<td><code>processesByPlant[plant_id]</code></td>
<td>array</td>
<td>해당 Plant의 Process 목록 (권한에 따라 필터링됨)</td>
</tr>
<tr>
<td><code>processesByPlant[plant_id][].id</code></td>
<td>string</td>
<td>Process ID</td>
</tr>
<tr>
<td><code>processesByPlant[plant_id][].code</code></td>
<td>string</td>
<td>Process 코드 (id와 동일)</td>
</tr>
<tr>
<td><code>processesByPlant[plant_id][].name</code></td>
<td>string</td>
<td>Process 이름</td>
</tr>
<tr>
<td><code>linesByProcess</code></td>
<td>object</td>
<td>Process ID를 키로 하는 Line 목록 맵</td>
</tr>
<tr>
<td><code>linesByProcess[process_id]</code></td>
<td>array</td>
<td>해당 Process의 Line 목록</td>
</tr>
<tr>
<td><code>linesByProcess[process_id][].id</code></td>
<td>string</td>
<td>Line ID</td>
</tr>
<tr>
<td><code>linesByProcess[process_id][].code</code></td>
<td>string</td>
<td>Line 코드 (id와 동일)</td>
</tr>
<tr>
<td><code>linesByProcess[process_id][].name</code></td>
<td>string</td>
<td>Line 이름</td>
</tr>
</tbody>
</table>

### 프론트엔드 사용 흐름

#### 1. API 호출
```javascript
const response = await fetch('/v1/masters?user_id=user001');
const data = await response.json();
```

#### 2. Plant 드롭다운 구성
```javascript
// Plant 드롭다운에 데이터 추가
const plantSelect = document.getElementById('plantSelect');
data.plants.forEach(plant => {
  const option = document.createElement('option');
  option.value = plant.id;
  option.textContent = plant.name;
  plantSelect.appendChild(option);
});
```

#### 3. Plant 선택 시 Process 드롭다운 업데이트
```javascript
plantSelect.addEventListener('change', (e) => {
  const selectedPlantId = e.target.value;
  const processes = data.processesByPlant[selectedPlantId] || [];
  
  // Process 드롭다운 업데이트
  const processSelect = document.getElementById('processSelect');
  processSelect.innerHTML = '<option value="">선택하세요</option>';
  
  processes.forEach(process => {
    const option = document.createElement('option');
    option.value = process.id;
    option.textContent = process.name;
    processSelect.appendChild(option);
  });
});
```

#### 4. Process 선택 시 Line 드롭다운 업데이트
```javascript
processSelect.addEventListener('change', (e) => {
  const selectedProcessId = e.target.value;
  const lines = data.linesByProcess[selectedProcessId] || [];
  
  // Line 드롭다운 업데이트
  const lineSelect = document.getElementById('lineSelect');
  lineSelect.innerHTML = '<option value="">선택하세요</option>';
  
  lines.forEach(line => {
    const option = document.createElement('option');
    option.value = line.id;
    option.textContent = line.name;
    lineSelect.appendChild(option);
  });
});
```

### 사용 예시

#### 기본 조회
```bash
curl -X GET "http://localhost:8000/v1/masters?user_id=user001"
```

#### JavaScript 예시
```javascript
async function loadMastersForDropdown(userId) {
  try {
    const response = await fetch(`/v1/masters?user_id=${userId}`);
    const data = await response.json();
    
    // Plant 드롭다운 구성
    populateDropdown('plantSelect', data.plants);
    
    // Plant 변경 시 Process 드롭다운 업데이트
    document.getElementById('plantSelect').addEventListener('change', (e) => {
      const plantId = e.target.value;
      const processes = data.processesByPlant[plantId] || [];
      populateDropdown('processSelect', processes);
    });
    
    // Process 변경 시 Line 드롭다운 업데이트
    document.getElementById('processSelect').addEventListener('change', (e) => {
      const processId = e.target.value;
      const lines = data.linesByProcess[processId] || [];
      populateDropdown('lineSelect', lines);
    });
  } catch (error) {
    console.error('마스터 데이터 조회 실패:', error);
  }
}

function populateDropdown(selectId, items) {
  const select = document.getElementById(selectId);
  select.innerHTML = '<option value="">선택하세요</option>';
  items.forEach(item => {
    const option = document.createElement('option');
    option.value = item.id;
    option.textContent = item.name;
    select.appendChild(option);
  });
}
```

### 화면 용도

이 API는 다음 화면에서 사용됩니다:

1. **PLC 관리 화면**
   - Plant, 공정, Line 드롭다운
   - PLC 등록/수정 시 계층 구조 선택

2. **Program 등록 화면**
   - 공정 드롭다운 필터
   - 권한에 따라 접근 가능한 공정만 표시

3. **PLC-PGM 매핑 화면**
   - Plant, 공정, Line 드롭다운
   - 매핑할 PLC를 선택하기 위한 계층 구조

### 특징

1. **권한 기반 필터링**: 사용자 권한에 따라 접근 가능한 공정만 반환
2. **계층 구조 최적화**: 프론트엔드에서 연쇄 드롭다운 구현에 최적화된 구조
3. **성능 최적화**: 한 번의 API 호출로 모든 계층 구조 데이터 조회
4. **일관성**: 모든 화면에서 동일한 API 사용

### 에러 응답

모든 API는 다음과 같은 에러 응답 형식을 사용합니다:

```json
{
  "detail": "마스터 데이터 조회 중 오류가 발생했습니다: [에러 메시지]"
}
```

### 주요 에러 상황

- `500 Internal Server Error`: 데이터베이스 쿼리 오류 또는 서버 내부 오류
- `422 Unprocessable Entity`: 필수 파라미터(`user_id`) 누락

### 주의사항

1. **권한 필터링**: `user_id`는 필수이며, 권한이 없으면 Process 목록이 비어있을 수 있습니다
2. **Plant와 Process 관계**: Process는 모든 Plant에서 공통으로 사용되므로, 모든 Plant에 동일한 Process 목록이 표시됩니다
3. **Process와 Line 관계**: Line도 모든 Process에서 공통으로 사용되므로, 모든 Process에 동일한 Line 목록이 표시됩니다
4. **활성 데이터만 반환**: `is_active=true`인 마스터 데이터만 반환됩니다

---

## 2. 공정 목록 조회

공정 기준정보 목록을 조회합니다.

### 엔드포인트

```
GET /v1/masters/processes
```

### 쿼리 파라미터

<table>
<thead>
<tr>
<th>파라미터</th>
<th>타입</th>
<th>필수</th>
<th>기본값</th>
<th>설명</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>include_inactive</code></td>
<td>boolean</td>
<td>아니오</td>
<td>false</td>
<td>비활성 공정 포함 여부</td>
</tr>
<tr>
<td><code>sort_by</code></td>
<td>string</td>
<td>아니오</td>
<td>process_name</td>
<td>정렬 기준 (process_id, process_name, create_dt)</td>
</tr>
<tr>
<td><code>sort_order</code></td>
<td>string</td>
<td>아니오</td>
<td>asc</td>
<td>정렬 순서 (asc, desc)</td>
</tr>
</tbody>
</table>

### 정렬 옵션

- **sort_by**: 정렬 기준
  - `process_id`: 공정 ID로 정렬
  - `process_name`: 공정명으로 정렬 (기본값)
  - `create_dt`: 생성일시로 정렬

- **sort_order**: 정렬 순서
  - `asc`: 오름차순 (기본값)
  - `desc`: 내림차순

### 응답 형식

```json
{
  "items": [
    {
      "process_id": "process_001",
      "process_name": "모듈",
      "description": "모듈 공정",
      "is_active": true,
      "create_dt": "2025-01-15T10:00:00",
      "create_user": "admin",
      "update_dt": "2025-01-20T14:30:00",
      "update_user": "admin"
    },
    {
      "process_id": "process_002",
      "process_name": "전극",
      "description": "전극 공정",
      "is_active": true,
      "create_dt": "2025-01-16T09:00:00",
      "create_user": "admin",
      "update_dt": null,
      "update_user": null
    }
  ],
  "total_count": 2
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
<td><code>items</code></td>
<td>array</td>
<td>공정 목록</td>
</tr>
<tr>
<td><code>items[].process_id</code></td>
<td>string</td>
<td>공정 ID (Primary Key)</td>
</tr>
<tr>
<td><code>items[].process_name</code></td>
<td>string</td>
<td>공정명</td>
</tr>
<tr>
<td><code>items[].description</code></td>
<td>string</td>
<td>공정 설명 (선택사항)</td>
</tr>
<tr>
<td><code>items[].is_active</code></td>
<td>boolean</td>
<td>활성화 여부</td>
</tr>
<tr>
<td><code>items[].create_dt</code></td>
<td>datetime</td>
<td>생성일시</td>
</tr>
<tr>
<td><code>items[].create_user</code></td>
<td>string</td>
<td>생성 사용자</td>
</tr>
<tr>
<td><code>items[].update_dt</code></td>
<td>datetime</td>
<td>수정일시 (수정되지 않은 경우 null)</td>
</tr>
<tr>
<td><code>items[].update_user</code></td>
<td>string</td>
<td>수정 사용자 (수정되지 않은 경우 null)</td>
</tr>
<tr>
<td><code>total_count</code></td>
<td>integer</td>
<td>전체 개수</td>
</tr>
</tbody>
</table>

### 사용 예시

#### 활성 공정만 조회 (기본)
```bash
curl -X GET "http://localhost:8000/v1/masters/processes"
```

#### 모든 공정 조회 (비활성 포함)
```bash
curl -X GET "http://localhost:8000/v1/masters/processes?include_inactive=true"
```

#### 공정명 내림차순 정렬
```bash
curl -X GET "http://localhost:8000/v1/masters/processes?sort_by=process_name&sort_order=desc"
```

#### 공정 ID 오름차순 정렬
```bash
curl -X GET "http://localhost:8000/v1/masters/processes?sort_by=process_id&sort_order=asc"
```

#### 생성일시 내림차순 정렬 (최신순)
```bash
curl -X GET "http://localhost:8000/v1/masters/processes?sort_by=create_dt&sort_order=desc"
```

### JavaScript 예시

```javascript
async function getProcessList(includeInactive = false, sortBy = 'process_name', sortOrder = 'asc') {
  try {
    const params = new URLSearchParams({
      include_inactive: includeInactive,
      sort_by: sortBy,
      sort_order: sortOrder
    });
    
    const response = await fetch(`/v1/masters/processes?${params}`);
    const data = await response.json();
    
    // 공정 목록 표시
    const processList = document.getElementById('processList');
    processList.innerHTML = '';
    
    data.items.forEach(process => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${process.process_id}</td>
        <td>${process.process_name}</td>
        <td>${process.description || '-'}</td>
        <td>${process.is_active ? '활성' : '비활성'}</td>
        <td>${new Date(process.create_dt).toLocaleString()}</td>
      `;
      processList.appendChild(row);
    });
    
    console.log(`총 ${data.total_count}개의 공정이 조회되었습니다.`);
  } catch (error) {
    console.error('공정 목록 조회 실패:', error);
  }
}

// 활성 공정만 조회
getProcessList();

// 모든 공정 조회 (비활성 포함)
getProcessList(true);

// 공정명 내림차순 정렬
getProcessList(false, 'process_name', 'desc');
```

### 화면 용도

이 API는 다음 화면에서 사용됩니다:

1. **그룹 관리 화면**
   - 공정 선택 드롭다운
   - 권한 그룹에 공정 할당 시 공정 목록 표시

2. **공정 기준정보 관리 화면**
   - 공정 목록 테이블
   - 공정 정보 조회 및 관리

3. **공정별 통계 및 분석 화면**
   - 공정 목록 필터
   - 공정별 데이터 집계

### 특징

1. **필터링 옵션**: 활성/비활성 공정 필터링 지원
2. **정렬 기능**: 다양한 정렬 기준 및 순서 지원
3. **전체 정보**: 공정의 모든 메타데이터 포함
4. **간단한 구조**: 계층 구조 없이 단순 리스트 형태

### 에러 응답

모든 API는 다음과 같은 에러 응답 형식을 사용합니다:

```json
{
  "detail": "공정 목록 조회 중 오류가 발생했습니다: [에러 메시지]"
}
```

### 주요 에러 상황

- `500 Internal Server Error`: 데이터베이스 쿼리 오류 또는 서버 내부 오류

### 주의사항

1. **기본값**: `include_inactive=false`이므로 기본적으로 활성 공정만 반환됩니다
2. **정렬 기본값**: `sort_by=process_name`, `sort_order=asc`로 공정명 오름차순 정렬이 기본입니다
3. **Plant와 무관**: 이 API는 Plant와 무관하게 모든 공정을 조회합니다 (Plant별 필터링 없음)

