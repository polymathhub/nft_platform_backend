"""
Setup PostgreSQL using pgAdmin connection
Tries multiple approaches to create nft_user and nft_db
"""
import subprocess
import sys
from pathlib import Path

def run_sql_via_psql_file(sql_commands):
    """Write SQL to a file and execute via psql"""
    sql_file = Path("setup_commands.sql")
    sql_file.write_text(sql_commands)
    
    result = subprocess.run(
        [
            "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe",
            "-U", "postgres",
            "-h", "localhost",
            "-d", "postgres",
            "-f", str(sql_file)
        ],
        capture_output=True,
        text=True
    )
    
    sql_file.unlink()  # Delete temp file
    return result

def main():
    sql_commands = """
CREATE USER IF NOT EXISTS nft_user WITH PASSWORD 'GiftedForge';
CREATE DATABASE IF NOT EXISTS nft_db OWNER nft_user;
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO nft_user;
SELECT 'Database setup complete!' as status;
"""
    
    print("=" * 60)
    print("PostgreSQL Setup for NFT Platform Backend")
    print("=" * 60)
    print()
    print("Attempting to create nft_user and nft_db...")
    print()
    
    # Try executing via temp SQL file
    result = run_sql_via_psql_file(sql_commands)
    
    if result.returncode == 0:
        print("✓ Setup successful!")
        print()
        print("Output:")
        print(result.stdout)
        print()
        print("Database configuration:")
        print("  User: nft_user")
        print("  Password: GiftedForge")
        print("  Database: nft_db")
        print("  Host: localhost:5432")
        print()
        print("Testing connection...")
        
        # Now test the connection
        test_result = subprocess.run(
            [
                "python",
                "test_connection.py"
            ],
            capture_output=True,
            text=True
        )
        
        print(test_result.stdout)
        if test_result.returncode == 0:
            print()
            print("✓ Ready to run: python startup.py")
        
        return 0
    else:
        print("✗ Setup failed!")
        print()
        print("STDOUT:")
        print(result.stdout)
        print()
        print("STDERR:")
        print(result.stderr)
        print()
        print("=" * 60)
        print("ALTERNATIVE: Use pgAdmin")
        print("=" * 60)
        print("1. Open pgAdmin 4 (search 'pgAdmin' in Windows Start Menu)")
        print("2. Enter postgres password when prompted")
        print("3. Right-click 'Databases' -> Create -> Database")
        print("   - Name: nft_db")
        print("   - Owner: postgres")
        print("4. Tools -> Query Tool")
        print("5. Copy and paste:")
        print()
        print('CREATE USER nft_user WITH PASSWORD \'GiftedForge\';')
        print("GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;")
        print("GRANT ALL ON SCHEMA public TO nft_user;")
        print()
        print("6. Click Execute")
        print()
        print("Then run: python startup.py")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
