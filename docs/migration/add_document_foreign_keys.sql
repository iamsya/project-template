-- ============================================================================
-- DOCUMENTS 테이블 Foreign Key 제약조건 재생성
-- ============================================================================
-- 목적: shared_core의 Document 모델로 생성된 DB를 
--       ai_backend의 Document 모델 구조(Foreign Key 포함)로 변경
--
-- 실행 순서:
-- 1. 기존 Foreign Key 제약조건 삭제
-- 2. 새로운 Foreign Key 제약조건 추가
-- ============================================================================

-- ============================================================================
-- 1단계: 기존 Foreign Key 제약조건 삭제
-- ============================================================================

-- 기존 제약조건 삭제 (IF EXISTS로 안전하게 처리)
ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS fk_documents_program_id;
ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS fk_documents_source_document_id;
ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS fk_documents_knowledge_reference_id;

-- 다른 이름으로 생성된 제약조건이 있을 수 있으므로 확인 후 삭제
-- (PostgreSQL에서 자동 생성된 제약조건명은 다를 수 있음)
-- 아래 쿼리로 제약조건명 확인 후 수동으로 삭제:
-- SELECT constraint_name 
-- FROM information_schema.table_constraints 
-- WHERE table_name = 'DOCUMENTS' 
--   AND constraint_type = 'FOREIGN KEY'
--   AND (constraint_name LIKE '%program%' 
--        OR constraint_name LIKE '%source%' 
--        OR constraint_name LIKE '%knowledge%');

-- ============================================================================
-- 2단계: 새로운 Foreign Key 제약조건 추가 (ai_backend 기준)
-- ============================================================================

-- PROGRAM_ID Foreign Key 추가
-- 참조: DOCUMENTS.PROGRAM_ID -> PROGRAMS.PROGRAM_ID
ALTER TABLE DOCUMENTS
ADD CONSTRAINT fk_documents_program_id
FOREIGN KEY (PROGRAM_ID)
REFERENCES PROGRAMS(PROGRAM_ID)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- SOURCE_DOCUMENT_ID Foreign Key 추가
-- 참조: DOCUMENTS.SOURCE_DOCUMENT_ID -> DOCUMENTS.DOCUMENT_ID
ALTER TABLE DOCUMENTS
ADD CONSTRAINT fk_documents_source_document_id
FOREIGN KEY (SOURCE_DOCUMENT_ID)
REFERENCES DOCUMENTS(DOCUMENT_ID)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- KNOWLEDGE_REFERENCE_ID Foreign Key 추가
-- 참조: DOCUMENTS.KNOWLEDGE_REFERENCE_ID -> KNOWLEDGE_REFERENCES.REFERENCE_ID
ALTER TABLE DOCUMENTS
ADD CONSTRAINT fk_documents_knowledge_reference_id
FOREIGN KEY (KNOWLEDGE_REFERENCE_ID)
REFERENCES KNOWLEDGE_REFERENCES(REFERENCE_ID)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- ============================================================================
-- 참고사항
-- ============================================================================
-- 1. orphan 레코드(참조되는 테이블에 없는 값)가 있으면 에러가 발생합니다.
--    에러 발생 시 해당 레코드의 Foreign Key 값을 NULL로 설정하거나 데이터를 정리하세요.
--
-- 2. ON DELETE SET NULL: 참조되는 레코드가 삭제되면 Foreign Key 값을 NULL로 설정
-- 3. ON UPDATE CASCADE: 참조되는 레코드의 Primary Key가 변경되면 Foreign Key도 함께 변경
-- ============================================================================

