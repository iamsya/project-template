# 프로그램 등록 API 가이드

## 개요

PLC 프로그램을 등록하고 처리하는 API입니다. 3개의 파일(ZIP, XLSX, CSV)을 업로드하여 프로그램을 등록합니다.

**엔드포인트:** `POST /v1/programs/register`

**Content-Type:** `multipart/form-data`

---

## 요청 (Request)

### 필수 파라미터

<table>
<thead>
<tr>
<th>파라미터명</th>
<th>타입</th>
<th>설명</th>
<th>예시</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>ladder_zip</code></td>
<td>File</td>
<td>PLC ladder logic 파일들이 포함된 ZIP 압축 파일</td>
<td><code>ladder_files.zip</code></td>
</tr>
<tr>
<td><code>classification_xlsx</code></td>
<td>File</td>
<td>템플릿 분류체계 데이터 XLSX 파일</td>
<td><code>classification.xlsx</code></td>
</tr>
<tr>
<td><code>device_comment_csv</code></td>
<td>File</td>
<td>Device 설명 CSV 파일</td>
<td><code>device_comment.csv</code></td>
</tr>
<tr>
<td><code>program_title</code></td>
<td>String (Form)</td>
<td>프로그램 제목</td>
<td><code>"공정1 PLC 프로그램"</code></td>
</tr>
<tr>
<td><code>program_description</code></td>
<td>String (Form, Optional)</td>
<td>프로그램 설명</td>
<td><code>"공정1 라인용 PLC 프로그램"</code></td>
</tr>
<tr>
<td><code>user_id</code></td>
<td>String (Form)</td>
<td>사용자 ID (기본값: "user")</td>
<td><code>"user001"</code></td>
</tr>
</tbody>
</table>

### 파일 형식 요구사항

#### 1. `ladder_zip` (ZIP 파일)
- **형식:** ZIP 압축 파일
- **내용:** PLC ladder logic 파일들 (`.ld`, `.lsp` 등)
- **검증 항목:**
  - ZIP 파일 무결성 검사
  - 압축 해제 가능 여부
  - 내부 파일 존재 여부

#### 2. `classification_xlsx` (XLSX 파일)
- **형식:** Excel 파일 (.xlsx)
- **필수 컬럼:**
  - `FOLDER_ID`: 폴더 ID
  - `FOLDER_NAME`: 폴더명
  - `SUB_FOLDER_NAME`: 하위 폴더명
  - `LOGIC_ID`: 로직 ID
  - `LOGIC_NAME`: 로직명 (또는 `로직파일명` 컬럼)
- **첫 번째 행:** 헤더 (컬럼명)
- **두 번째 행부터:** 데이터
- **검증 항목:**
  - XLSX 파일 형식 검증
  - 필수 컬럼 존재 여부
  - 로직 파일명과 ZIP 내 파일 매칭 검증

#### 3. `device_comment_csv` (CSV 파일)
- **형식:** CSV 파일
- **내용:** Ladder 로직의 device에 대한 코멘트 정보
- **검증 항목:**
  - CSV 파일 형식 검증
  - 기본 컬럼 존재 여부

---

## 응답 (Response)

### 성공 응답 (200 OK)

```json
{
  "status": "success",
  "message": "파일 등록 요청하였습니다.",
  "data": {
    "program_id": "pgm_1234567890",
    "program_title": "공정1 PLC 프로그램",
    "program_description": "공정1 라인용 PLC 프로그램",
    "user_id": "user001",
    "status": "processing",
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "checked_files": [
      "ladder_file1.ld",
      "ladder_file2.ld"
    ],
    "message": "파일 등록 요청하였습니다.",
    "create_dt": "2025-01-15T10:30:00+09:00",
    "updated_at": null
  },
  "validation_result": {
    "is_valid": true,
    "errors": [],
    "warnings": [],
    "checked_files": [
      "ladder_file1.ld",
      "ladder_file2.ld"
    ],
    "file_count_in_zip": 10,
    "file_count_in_xlsx": 10,
    "matched_files": [
      "ladder_file1.ld",
      "ladder_file2.ld"
    ],
    "missing_files": []
  }
}
```

### 유효성 검사 실패 응답 (200 OK)

**참고:** 유효성 검사 실패 시에도 HTTP 상태 코드는 `200 OK`입니다. `status` 필드가 `"validation_failed"`로 반환됩니다.

**UI 표시 형식:**
- **타이틀:** "실패"
- **하위 섹션:** 섹션별로 그룹화된 에러 목록 (다건 가능)

```json
{
  "status": "validation_failed",
  "message": "유효성 검사를 통과하지 못했습니다.",
  "data": null,
  "validation_result": {
    "is_valid": false,
    "errors": [
      "11행의 Login ID 값이 누락되었습니다.",
      "14, 16행의 Logic Name 값이 누락되었습니다.",
      "Login ID 0000_11, 0000_12, 0000_14 PLC Ladder 파일이 존재하지 않습니다."
    ],
    "error_sections": {
      "분류체계 데이터 유효성 검사": [
        "11행의 Login ID 값이 누락되었습니다.",
        "14, 16행의 Logic Name 값이 누락되었습니다."
      ],
      "PLC Ladder 파일 유효성 검사": [
        "Login ID 0000_11, 0000_12, 0000_14 PLC Ladder 파일이 존재하지 않습니다."
      ]
    },
    "warnings": [],
    "checked_files": [],
    "file_count_in_zip": null,
    "file_count_in_xlsx": null,
    "matched_files": null,
    "missing_files": null
  }
}
```

#### 에러 섹션 구조

`error_sections`는 섹션명을 키로, 해당 섹션의 에러 목록을 값으로 하는 객체입니다:

- **"분류체계 데이터 유효성 검사"**: XLSX 파일 관련 에러
  - 예: "11행의 Login ID 값이 누락되었습니다."
  - 예: "14, 16행의 Logic Name 값이 누락되었습니다."
- **"PLC Ladder 파일 유효성 검사"**: ZIP 파일 및 교차 검증 에러
  - 예: "Login ID 0000_11, 0000_12, 0000_14 PLC Ladder 파일이 존재하지 않습니다."
- **"기타"**: 기타 에러 (해당되는 경우에만 포함)

**중요:** 각 섹션은 여러 개의 에러를 가질 수 있으며, 빈 섹션은 응답에 포함되지 않습니다.

---

## 처리 흐름

### 1. 유효성 검사 (동기 처리)
- 파일 형식 검증
- 필수 컬럼 검증
- 파일 간 교차 검증 (XLSX의 로직 파일명 ↔ ZIP 내 파일)
- **즉시 응답 반환**

### 2. 백그라운드 처리 (비동기)
유효성 검사를 통과한 경우, 다음 작업이 백그라운드에서 비동기로 처리됩니다:

1. **S3 업로드 및 압축 해제**
   - ZIP 파일을 S3에 업로드
   - S3에서 ZIP 압축 해제
   - 개별 로직 파일 분리

2. **템플릿 및 템플릿 데이터 생성**
   - `Template` 테이블에 템플릿 생성
   - `TemplateData` 테이블에 템플릿 데이터 생성
   - XLSX 파일의 분류체계 데이터 반영

3. **데이터 전처리 및 Document 생성**
   - 각 로직 파일을 JSON 형식으로 전처리
   - Device 코멘트 데이터 결합
   - `Document` 테이블에 문서 생성
   - `TemplateData.document_id` 연결

4. **Vector DB 인덱싱 요청**
   - 외부 Knowledge API에 임베딩 요청

---

## 예외 상황

### HTTP 400 Bad Request
- 파일 형식이 올바르지 않은 경우
- 필수 파라미터가 누락된 경우

### HTTP 500 Internal Server Error
- 서버 내부 오류
- 데이터베이스 연결 오류
- S3 업로드 실패

---

## 프론트엔드 구현 가이드

### 1. 파일 업로드 Form 구성

```javascript
const formData = new FormData();
formData.append('ladder_zip', ladderZipFile);
formData.append('classification_xlsx', classificationXlsxFile);
formData.append('device_comment_csv', deviceCommentCsvFile);
formData.append('program_title', '공정1 PLC 프로그램');
formData.append('program_description', '공정1 라인용 PLC 프로그램');
formData.append('user_id', 'user001');
```

### 2. API 호출 예시 (JavaScript/Fetch)

```javascript
async function registerProgram(files, programTitle, programDescription, userId) {
  const formData = new FormData();
  formData.append('ladder_zip', files.ladderZip);
  formData.append('classification_xlsx', files.classificationXlsx);
  formData.append('device_comment_csv', files.deviceCommentCsv);
  formData.append('program_title', programTitle);
  formData.append('program_description', programDescription || '');
  formData.append('user_id', userId || 'user');

  try {
    const response = await fetch('/v1/programs/register', {
      method: 'POST',
      body: formData,
      // Content-Type 헤더는 자동으로 설정됨 (multipart/form-data)
    });

    const data = await response.json();

    if (data.status === 'success') {
      console.log('프로그램 등록 성공:', data.data.program_id);
      // 성공 처리
      return {
        success: true,
        programId: data.data.program_id,
        message: data.message
      };
    } else if (data.status === 'validation_failed') {
      console.error('유효성 검사 실패:', data.validation_result.errors);
      // 에러 표시
      return {
        success: false,
        errors: data.validation_result.errors,
        validationResult: data.validation_result
      };
    }
  } catch (error) {
    console.error('API 호출 실패:', error);
    return {
      success: false,
      error: error.message
    };
  }
}
```

### 3. 에러 표시 예시 (모달 다이얼로그)

```javascript
function displayValidationErrors(validationResult) {
  // API 응답에서 이미 그룹화된 error_sections 사용
  const errorSections = validationResult.error_sections || {};
  
  // 모달 다이얼로그 표시
  // 타이틀: "실패"
  // 하위에 섹션별로 에러 목록 표시
  
  if (Object.keys(errorSections).length === 0) {
    // error_sections가 없으면 errors 배열을 사용 (하위 호환성)
    console.warn('error_sections가 없습니다. errors 배열을 사용합니다.');
    return;
  }
  
  // 섹션별로 에러 표시
  Object.keys(errorSections).forEach((sectionName, sectionIndex) => {
    const errors = errorSections[sectionName];
    
    // 섹션 헤더: "분류체계 데이터 유효성 검사", "PLC Ladder 파일 유효성 검사" 등
    console.log(`[${sectionName}]`);
    
    // 각 에러를 번호와 함께 표시
    errors.forEach((error, errorIndex) => {
      // "1) 11행의 Login ID 값이 누락되었습니다." 형식
      console.log(`  ${errorIndex + 1}) ${error}`);
    });
  });
}
```

#### React 컴포넌트 예시

```jsx
function ValidationErrorModal({ validationResult }) {
  const errorSections = validationResult?.error_sections || {};
  
  return (
    <Modal title="실패">
      <div className="error-content">
        {Object.keys(errorSections).map((sectionName, sectionIndex) => (
          <div key={sectionIndex} className="error-section">
            <h3>{sectionName}</h3>
            <ul>
              {errorSections[sectionName].map((error, errorIndex) => (
                <li key={errorIndex}>
                  {errorIndex + 1}) {error}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <button onClick={handleClose}>확인</button>
    </Modal>
  );
}
```

### 4. 프로그레스 확인

프로그램 등록 후 백그라운드 처리 상태를 확인하려면:

**API:** `GET /v1/programs/{program_id}`

```javascript
async function checkProgramStatus(programId) {
  const response = await fetch(`/v1/programs/${programId}`);
  const data = await response.json();
  
  // status 값:
  // - "uploading": 업로드 중
  // - "processing": 전처리 중
  // - "embedding": 임베딩 중
  // - "completed": 완료
  // - "failed": 실패
  // - "indexing_failed": 인덱싱 실패
  
  return data.status;
}
```

---

## 주의사항

1. **파일 크기 제한**
   - 서버 설정에 따라 파일 크기 제한이 있을 수 있습니다.
   - 대용량 파일 업로드 시 타임아웃 주의

2. **비동기 처리**
   - 유효성 검사 통과 후 즉시 응답이 반환됩니다.
   - 실제 파일 처리(S3 업로드, 전처리 등)는 백그라운드에서 진행됩니다.
   - 처리 상태는 별도 API로 확인해야 합니다.

3. **에러 처리**
   - 유효성 검사 실패 시에도 HTTP 200 응답이 반환됩니다.
   - `status` 필드를 확인하여 성공/실패를 판단하세요.

4. **파일명 인코딩**
   - 한글 파일명이 포함된 경우 올바르게 처리됩니다.
   - 프론트엔드에서 특별한 인코딩 처리는 필요 없습니다.

---

## 테스트 예시

### cURL 예시

```bash
curl -X POST "http://localhost:8000/v1/programs/register" \
  -H "Content-Type: multipart/form-data" \
  -F "ladder_zip=@ladder_files.zip" \
  -F "classification_xlsx=@classification.xlsx" \
  -F "device_comment_csv=@device_comment.csv" \
  -F "program_title=공정1 PLC 프로그램" \
  -F "program_description=공정1 라인용 PLC 프로그램" \
  -F "user_id=user001"
```

### Postman 설정

1. **Method:** POST
2. **URL:** `http://localhost:8000/v1/programs/register`
3. **Body:** form-data
4. **파일 필드:**
   - `ladder_zip`: File 선택
   - `classification_xlsx`: File 선택
   - `device_comment_csv`: File 선택
5. **텍스트 필드:**
   - `program_title`: Text 입력
   - `program_description`: Text 입력 (선택)
   - `user_id`: Text 입력

---

## 관련 API

- **프로그램 목록 조회:** `GET /v1/programs`
- **프로그램 상세 조회:** `GET /v1/programs/{program_id}`
- **프로그램 삭제:** `DELETE /v1/programs/{program_id}`
- **실패 파일 재시도:** `POST /v1/programs/{program_id}/retry`

---

## 문의

API 사용 중 문제가 발생하면 백엔드 팀에 문의하세요.

