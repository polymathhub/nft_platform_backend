-- PostgreSQL Setup Script for NFT Platform Backend
-- Run this in pgAdmin or psql as an admin user

-- Step 1: Create nft_user if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_user WHERE usename = 'nft_user') THEN
        CREATE USER nft_user WITH PASSWORD 'GiftedForge';
        RAISE NOTICE 'Created user: nft_user';
    ELSE
        RAISE NOTICE 'User nft_user already exists';
    END IF;
END
$$;

-- Step 2: Create nft_db database if it doesn't exist
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

-- Step 3: Grant privileges to nft_user
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;

-- Step 4: Connect to nft_db and grant schema privileges
\c nft_db;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO nft_user;

-- Verify user and database
SELECT 'User created:' as status, usename FROM pg_user WHERE usename = 'nft_user'
UNION ALL
SELECT 'Database created:' as status, datname FROM pg_database WHERE datname = 'nft_db';
