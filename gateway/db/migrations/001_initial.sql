-- Initial CyberWar-Room Database Schema
-- Audits all incidents, scans, virtual patches, and Git PR records

CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    target VARCHAR(255) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL, -- OPEN, VERIFYING, MITIGATED, RESOLVED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scans (
    id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) REFERENCES incidents(id) ON DELETE CASCADE,
    target VARCHAR(255) NOT NULL,
    tool VARCHAR(64) NOT NULL, -- nmap, nuclei
    raw_output TEXT,
    parsed_findings JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exploit_verifications (
    id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) REFERENCES incidents(id) ON DELETE CASCADE,
    agent VARCHAR(64) NOT NULL,
    payload TEXT NOT NULL,
    evidence TEXT NOT NULL,
    is_exploitable BOOLEAN NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS remediations (
    id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) REFERENCES incidents(id) ON DELETE CASCADE,
    patch_type VARCHAR(64) NOT NULL, -- VIRTUAL_PATCH, GITHUB_PR
    rule_content TEXT,
    github_pr_url VARCHAR(512),
    status VARCHAR(32) NOT NULL, -- PROPOSED, APPROVED, APPLIED, REJECTED
    applied_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(64),
    actor VARCHAR(64) NOT NULL, -- Human or Agent Name
    channel VARCHAR(64),
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
