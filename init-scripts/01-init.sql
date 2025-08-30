-- PostgreSQL initialization script for KCDD Market
-- This script runs when the PostgreSQL container starts for the first time

-- Create extensions that might be useful
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE kcdd_market TO kcdd_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO kcdd_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kcdd_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kcdd_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO kcdd_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kcdd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kcdd_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO kcdd_user;
