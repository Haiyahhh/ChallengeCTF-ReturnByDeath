#!/bin/bash
set -e

# Read the flag from the physical file
FLAG=$(cat /flag.txt)

# Generate a random, never-logged password for each seeded staff account so
# no valid credential for them ever exists in the codebase.
random_password() {
    head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 32
}
RAM_PW=$(random_password)
REM_PW=$(random_password)
PETRA_PW=$(random_password)
FREDERICA_PW=$(random_password)

# Initialize the schema and insert the flag
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        bio TEXT,
        internal_notes TEXT
    );

    CREATE TABLE IF NOT EXISTS system_secrets (
        id SERIAL PRIMARY KEY,
        secret_name VARCHAR(50),
        secret_value VARCHAR(255)
    );

    CREATE TABLE IF NOT EXISTS config_audit_log (
        id SERIAL PRIMARY KEY,
        event VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
    );

    INSERT INTO system_secrets (secret_name, secret_value) VALUES ('FLAG', '$FLAG');

    -- Seed household staff directory (flavor NPCs with randomly generated,
    -- never-exposed passwords -- these accounts are not meant to be logged into)
    INSERT INTO users (username, password, role, bio, internal_notes) VALUES
        ('ram', '$RAM_PW', 'user', 'Head of Household Operations. Keeps the estate cluster running on schedule &mdash; do not ask about her sister''s uptime metrics.', 'HR: Exemplary performance. Flagged for Watchdog lead promotion next quarter. No disciplinary history.'),
        ('rem', '$REM_PW', 'user', 'Junior Systems Steward. Handles kitchen inventory and overnight batch jobs. Still memorizing the incident runbook.', 'HR: Still on probationary review period. Manager notes strong potential, recommends pairing with a senior steward.'),
        ('petra', '$PETRA_PW', 'user', 'Herbal & Resource Logistics. New hire, very earnest, reports every anomaly twice.', 'HR: Recently onboarded via the Kalten estate transfer program. Mentor assigned: Frederica.'),
        ('frederica', '$FREDERICA_PW', 'user', 'Senior Estate Manager. Oversees the Pleiades Watchdog rotation and staff onboarding.', 'HR: Approved for expanded scheduling authority. Handles all new Watchdog onboarding paperwork.')
    ON CONFLICT (username) DO NOTHING;
EOSQL