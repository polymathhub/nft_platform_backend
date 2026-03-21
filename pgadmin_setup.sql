-- SQL Script for setting up nft_user and nft_db
-- ✅ SECURITY: Replace '<PASSWORD_HERE>' with a secure password before running
-- Copy and paste this into pgAdmin Query Tool

-- Create nft_user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'nft_user') THEN
        CREATE USER nft_user WITH PASSWORD '<PASSWORD_HERE>';
        RAISE NOTICE 'Created user: nft_user';
    ELSE
        RAISE NOTICE 'User nft_user already exists - updating password';
        ALTER USER nft_user WITH PASSWORD '<PASSWORD_HERE>';
    END IF;
END
$$;

-- Create nft_db if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'nft_db') THEN
        CREATE DATABASE nft_db OWNER nft_user;
        RAISE NOTICE 'Created database: nft_db';
    ELSE
        RAISE NOTICE 'Database nft_db already exists';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO nft_user;

-- Verify
SELECT 'Setup Status' as check_name, 'Complete' as result
UNION ALL
SELECT 'User', usename FROM pg_user WHERE usename = 'nft_user'
UNION ALL
SELECT 'Database', datname FROM pg_database WHERE datname = 'nft_db';
