-- ============================================================================
-- DOCUMENTS 테이블 관련 Foreign Key 제약조건 제거
-- ============================================================================
-- 목적: Document 테이블과 관련된 모든 Foreign Key 제약조건을 제거
--       비동기 파이프라인 특성상 FK 제약이 방해될 수 있어 제거
--       Soft delete + 백엔드 검증 + 정기 검증 Job으로 정합성 관리
--
-- 실행 전 확인:
-- 1. 현재 스키마 확인: SELECT current_schema();
-- 2. 제약조건 확인: 아래 쿼리로 현재 FK 제약조건 확인
-- ============================================================================

-- ============================================================================
-- 현재 Foreign Key 제약조건 확인 쿼리 (실행 전 확인용)
-- ============================================================================
/*
SELECT 
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND (
        tc.table_name = 'DOCUMENTS'
        OR ccu.table_name = 'DOCUMENTS'
    )
ORDER BY tc.table_name, tc.constraint_name;
*/

-- ============================================================================
-- 1단계: DOCUMENTS 테이블에서 나가는 Foreign Key 제약조건 제거
-- ============================================================================

-- DOCUMENTS.PROGRAM_ID → PROGRAMS.PROGRAM_ID
ALTER TABLE DOCUMENTS 
DROP CONSTRAINT IF EXISTS fk_documents_program_id;

-- DOCUMENTS.SOURCE_DOCUMENT_ID → DOCUMENTS.DOCUMENT_ID (자기 참조)
ALTER TABLE DOCUMENTS 
DROP CONSTRAINT IF EXISTS fk_documents_source_document_id;

-- DOCUMENTS.KNOWLEDGE_REFERENCE_ID → KNOWLEDGE_REFERENCES.REFERENCE_ID
ALTER TABLE DOCUMENTS 
DROP CONSTRAINT IF EXISTS fk_documents_knowledge_reference_id;

-- PostgreSQL에서 자동 생성된 제약조건명이 다를 수 있으므로 확인 후 제거
-- 아래 쿼리로 DOCUMENTS 테이블의 모든 FK 제약조건 확인:
/*
SELECT constraint_name, column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.table_name = 'DOCUMENTS'
    AND tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = current_schema();
*/

-- 자동 생성된 제약조건명으로 제거 (예시)
-- ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS documents_program_id_fkey;
-- ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS documents_source_document_id_fkey;
-- ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS documents_knowledge_reference_id_fkey;

-- ============================================================================
-- 2단계: 모든 DOCUMENTS 관련 FK 제약조건 일괄 제거 (안전한 방법)
-- ============================================================================

-- 동적으로 모든 FK 제약조건 찾아서 제거하는 스크립트
-- 주의: 이 스크립트는 실행 전에 반드시 확인 쿼리를 먼저 실행하세요!

DO $$
DECLARE
    r RECORD;
BEGIN
    -- DOCUMENTS 테이블에서 나가는 FK 제거
    FOR r IN
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'DOCUMENTS'
            AND constraint_type = 'FOREIGN KEY'
            AND table_schema = current_schema()
    LOOP
        EXECUTE 'ALTER TABLE DOCUMENTS DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
        RAISE NOTICE '제거됨: DOCUMENTS.%', r.constraint_name;
    END LOOP;
END $$;

-- ============================================================================
-- 최종 확인: 제거 후 FK 제약조건 확인
-- ============================================================================

-- 제거 후 확인 쿼리
SELECT 
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND (
        tc.table_name = 'DOCUMENTS'
        OR ccu.table_name = 'DOCUMENTS'
    )
    AND tc.table_schema = current_schema()
ORDER BY tc.table_name, tc.constraint_name;

-- 결과가 없으면 모든 FK 제약조건이 제거된 것입니다.

-- ============================================================================
-- 참고사항
-- ============================================================================
-- 1. 이 스크립트는 DOCUMENTS 테이블과 관련된 모든 FK 제약조건을 제거합니다.
-- 2. FK 제약조건 제거 후에도 컬럼과 인덱스는 그대로 유지됩니다.
-- 3. 데이터 정합성은 백엔드 레벨에서 검증하거나 정기 검증 Job으로 관리합니다.
-- 4. Soft delete를 사용하여 데이터 삭제 시 실제로는 삭제하지 않습니다.
-- ============================================================================

