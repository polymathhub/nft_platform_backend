import subprocess
import sys
from pathlib import Path
def run_sql_via_psql_file(sql_commands):
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
    sql_file.unlink()
    return result
def main():
