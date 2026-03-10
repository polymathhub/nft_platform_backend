"""
Check and setup PostgreSQL for NFT Platform Backend
"""
import asyncio
import asyncpg
import sys

async def main():
    try:
        # Connect as postgres user (no password prompt if using peer auth or trust)
        print("[1/4] Connecting to PostgreSQL...")
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            database='postgres'
        )
        print("✓ PostgreSQL connection successful")
        
        # Check if nft_user exists
        print("\n[2/4] Checking for nft_user...")
        user_exists = await conn.fetchval(
            "SELECT 1 FROM pg_user WHERE usename = $1",
            'nft_user'
        )
        
        if user_exists:
            print("✓ User nft_user exists")
        else:
            print("✗ User nft_user NOT found")
            print("  Creating user nft_user with password 'GiftedForge'...")
            try:
                await conn.execute(
                    "CREATE USER nft_user WITH PASSWORD 'GiftedForge'"
                )
                print("✓ User nft_user created")
            except Exception as e:
                print(f"  Error creating user: {e}")
        
        # Check if nft_db database exists
        print("\n[3/4] Checking for nft_db database...")
        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            'nft_db'
        )
        
        if db_exists:
            print("✓ Database nft_db exists")
        else:
            print("✗ Database nft_db NOT found")
            print("  Creating database nft_db...")
            try:
                await conn.execute(
                    "CREATE DATABASE nft_db OWNER nft_user"
                )
                print("✓ Database nft_db created")
            except Exception as e:
                print(f"  Error creating database: {e}")
        
        await conn.close()
        
        # Try to connect as nft_user
        print("\n[4/4] Testing connection as nft_user...")
        try:
            nft_conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='nft_user',
                password='GiftedForge',
                database='nft_db'
            )
            version = await nft_conn.fetchval('SELECT version()')
            print("✓ Connection as nft_user successful!")
            print(f"  PostgreSQL: {version[:60]}...")
            await nft_conn.close()
            return 0
        except asyncpg.InvalidPasswordError:
            print("✗ Password authentication failed")
            print("  The password 'GiftedForge' is incorrect")
            print("  Please verify the password in your .env file")
            return 1
        except asyncpg.PostgresError as e:
            print(f"✗ PostgreSQL Error: {e}")
            return 1
            
    except ConnectionRefusedError:
        print("✗ Cannot connect to PostgreSQL on localhost:5432")
        print("  Is PostgreSQL running?")
        return 1
    except asyncpg.InvalidPasswordError:
        print("✗ Cannot connect as postgres user")
        print("  PostgreSQL may require a password or use different auth method")
        print("  Try running this in PostgreSQL admin mode")
        return 1
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
