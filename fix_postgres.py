"""
PostgreSQL setup using Windows authentication
Works even without knowing the postgres password
"""
import subprocess
import tempfile
import sys
from pathlib import Path

def setup_via_windows_auth():
    """Try to setup using Windows authentication"""
    sql_commands = """
CREATE USER IF NOT EXISTS nft_user WITH PASSWORD 'GiftedForge';
CREATE DATABASE IF NOT EXISTS nft_db OWNER nft_user;
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;
"""
    
    # Write SQL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
        f.write(sql_commands)
        sql_file = f.name
    
    try:
        # Try connecting as Windows user (no password)
        print("Attempting setup via Windows authentication...")
        result = subprocess.run(
            [
                "C:\\Program Files\\PostgreSQL\\18\\bin\\psql.exe",
                "-U", "postgres",
                "-h", "localhost",
                "-w",  # Don't prompt for password
                "-d", "postgres",
                "-f", sql_file
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        Path(sql_file).unlink()  # Clean up
        
        if result.returncode == 0:
            print("✓ Setup successful via Windows auth!")
            print(result.stdout)
            return True
        else:
            print("✗ Windows auth failed")
            print("Error:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        Path(sql_file).unlink() if Path(sql_file).exists() else None
        return False

def show_pgadmin_instructions():
    """Show how to use pgAdmin"""
    print()
    print("=" * 70)
    print("SOLUTION: Use pgAdmin to create database and user")
    print("=" * 70)
    print()
    print("Step-by-step instructions:")
    print()
    print("1. OPEN pgAdmin 4")
    print("   - Windows Start Menu → Search 'pgAdmin' → Click 'pgAdmin 4'")
    print("   - It will open in your browser at http://localhost:5050")
    print()
    print("2. CONNECT TO POSTGRESQL")
    print("   - Left panel: expand 'Servers'")
    print("   - Double-click 'PostgreSQL 18' to connect")
    print("   - If password is needed, try:")
    print("     a) Leave blank and press OK")
    print("     b) Your Windows login password")
    print("     c) Password from PostgreSQL installation")
    print()
    print("3. CREATE DATABASE (if not exists)")
    print("   - Right-click 'Databases' → Create → Database")
    print("   - Name: nft_db")
    print("   - Owner: (select from dropdown or leave as postgres)")
    print("   - Click 'Save'")
    print()
    print("4. CREATE USER AND GRANT PRIVILEGES")
    print("   - Top menu: Tools → Query Tool")
    print("   - Paste the following SQL:")
    print()
    print("   " + "-" * 60)
    sql = """CREATE USER IF NOT EXISTS nft_user WITH PASSWORD 'GiftedForge';
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO nft_user;"""
    for line in sql.split('\n'):
        print("   " + line)
    print("   " + "-" * 60)
    print()
    print("   - Click Execute button (▶️ icon) at top")
    print("   - You should see 'Query succeeded'")
    print()
    print("5. CLOSE pgAdmin")
    print()
    print("6. TEST THE CONNECTION")
    print("   PowerShell:")
    print("   >>> python test_connection.py")
    print()
    print("7. START THE APP")
    print("   PowerShell:")
    print("   >>> python startup.py")
    print()
    print("=" * 70)

def main():
    print("NFT Platform Backend - PostgreSQL Setup")
    print()
    
    # Try Windows auth first
    if setup_via_windows_auth():
        print()
        print("Testing connection now...")
        result = subprocess.run(
            ["python", "test_connection.py"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode == 0:
            print()
            print("✓ SUCCESS! You can now run:")
            print("  >>> python startup.py")
            return 0
    
    # If Windows auth failed, show pgAdmin instructions
    show_pgadmin_instructions()
    print()
    print("After following these steps, run:")
    print("  >>> python test_connection.py")
    print()
    return 1

if __name__ == "__main__":
    sys.exit(main())
