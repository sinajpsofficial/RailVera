-- Enable vector extension (run once)
CREATE EXTENSION IF NOT EXISTS vector;

-- Users and authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id VARCHAR(20) UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'employee',
    division VARCHAR(100),
    department VARCHAR(100),
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Employee knowledge profiles
CREATE TABLE employee_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    profile_data JSONB NOT NULL DEFAULT '{}',
    completeness_pct NUMERIC(5,2) DEFAULT 0,
    last_document_upload TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Rules repository (populated from rules.md)
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_id VARCHAR(50) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    source VARCHAR(50) DEFAULT 'rules.md',
    chapter VARCHAR(100),
    section VARCHAR(100),
    description TEXT NOT NULL,
    eligibility_conditions JSONB DEFAULT '[]',
    required_documents JSONB DEFAULT '[]',
    disqualifying_conditions JSONB DEFAULT '[]',
    exceptions JSONB DEFAULT '[]',
    decision_logic TEXT,
    authority VARCHAR(255),
    related_rules TEXT[] DEFAULT '{}',
    embedding vector(384),
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rules_domain ON rules(domain);
CREATE INDEX idx_rules_rule_id ON rules(rule_id);
CREATE INDEX idx_rules_embedding ON rules
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Cases (each eligibility check or question is a case)
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(100) NOT NULL,
    query_text TEXT,
    status VARCHAR(50) DEFAULT 'open',
    required_documents JSONB DEFAULT '[]',
    submitted_documents JSONB DEFAULT '[]',
    missing_documents JSONB DEFAULT '[]',
    extracted_facts JSONB DEFAULT '{}',
    decision VARCHAR(100),
    confidence VARCHAR(50),
    decision_reasoning TEXT,
    rules_applied TEXT[] DEFAULT '{}',
    -- HITL review fields (Phase 5)
    review_status VARCHAR(30) NOT NULL DEFAULT 'draft',   -- draft | pending_review | approved | rejected
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Uploaded documents
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE SET NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    document_type VARCHAR(100),
    classification_confidence NUMERIC(5,4),
    ocr_quality_score NUMERIC(5,4),
    is_readable BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    rejection_reason TEXT,
    extracted_facts JSONB DEFAULT '{}',
    raw_text TEXT,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    -- Background processing state: pending → processing → done | failed
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Conversations
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'text',
    rules_cited TEXT[] DEFAULT '{}',
    documents_cited UUID[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Document demand tracking
CREATE TABLE document_demands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    demanded_document VARCHAR(255) NOT NULL,
    reason TEXT NOT NULL,
    rule_citations TEXT[] DEFAULT '{}',
    demanded_at TIMESTAMPTZ DEFAULT NOW(),
    fulfilled_at TIMESTAMPTZ,
    fulfilled_by_document_id UUID REFERENCES documents(id),
    status VARCHAR(50) DEFAULT 'pending'
);

-- Eligibility reports
CREATE TABLE eligibility_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    domain VARCHAR(100),
    decision VARCHAR(100),
    eligibility_status VARCHAR(50),
    supporting_rules JSONB DEFAULT '[]',
    supporting_facts JSONB DEFAULT '[]',
    missing_information JSONB DEFAULT '[]',
    risk_indicators JSONB DEFAULT '[]',
    administrative_notes TEXT,
    confidence_level VARCHAR(50),
    report_pdf_path VARCHAR(500),
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
