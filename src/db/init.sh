#!/bin/bash
set -e

# Read the flag from the physical file
FLAG=$(cat /flag.txt)

# Initialize the schema and insert the flag
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        role VARCHAR(20) DEFAULT 'user'
    );
    
    CREATE TABLE IF NOT EXISTS system_secrets (
        id SERIAL PRIMARY KEY,
        secret_name VARCHAR(50),
        secret_value VARCHAR(255)
    );
    
    INSERT INTO system_secrets (secret_name, secret_value) VALUES ('FLAG', '$FLAG');
EOSQL