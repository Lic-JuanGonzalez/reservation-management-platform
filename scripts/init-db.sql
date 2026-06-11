-- Initial database setup script
-- Runs automatically on first PostgreSQL container start

-- Create test database
CREATE DATABASE reservation_platform_test WITH OWNER postgres;

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE reservation_platform TO postgres;
GRANT ALL PRIVILEGES ON DATABASE reservation_platform_test TO postgres;

-- Enable required extensions
\c reservation_platform
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

\c reservation_platform_test
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
