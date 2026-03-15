import subprocess
import tempfile
import sys
from pathlib import Path
def setup_via_windows_auth():
GRANT ALL PRIVILEGES ON DATABASE nft_db TO nft_user;
GRANT ALL ON SCHEMA public TO nft_user;
