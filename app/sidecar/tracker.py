import os
import time
import subprocess
import psycopg2
from datetime import datetime
import traceback

# Constants
REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

# Database credentials from env vars
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")

# Connect to PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST
    )

# Initialize table with commit_hash column
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP NOT NULL,
            author TEXT NOT NULL,
            commit_hash TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# Clone or update repo
def clone_or_pull_repo():
    if not os.path.exists(REPO_DIR):
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
    else:
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

# Get commit info
def get_latest_commit_info():
    result_author = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"],
        capture_output=True,
        text=True,
        check=True
    )
    author = result_author.stdout.strip()

    result_timestamp = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"],
        capture_output=True,
        text=True,
        check=True
    )
    timestamp = datetime.fromisoformat(result_timestamp.stdout.strip())

    result_hash = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%H"],
        capture_output=True,
        text=True,
        check=True
    )
    commit_hash = result_hash.stdout.strip()

    return timestamp, author, commit_hash

# Store change in DB
def store_change(timestamp, author, commit_hash):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO changes (timestamp, author, commit_hash)
        VALUES (%s, %s, %s)
    """, (timestamp, author, commit_hash))
    conn.commit()
    cur.close()
    conn.close()

# Get file hash for change detection
def file_hash():
    if not os.path.exists(os.path.join(REPO_DIR, FILE_TO_TRACK)):
        return None
    result = subprocess.run(
        ["sha256sum", os.path.join(REPO_DIR, FILE_TO_TRACK)],
        capture_output=True,
        text=True
    )
    return result.stdout.split()[0]

def main():
    init_db()
    last_hash = None

    while True:
        try:
            clone_or_pull_repo()
            current_hash = file_hash()

            if current_hash and current_hash != last_hash:
                timestamp, author, commit_hash = get_latest_commit_info()
                store_change(timestamp, author, commit_hash)
                print(f"[{timestamp}] Change detected by {author}, commit {commit_hash}")
                last_hash = current_hash

        except Exception as e:
            print("Error:", e)
            traceback.print_exc()

        time.sleep(10)  # Check every 10 seconds

if __name__ == "__main__":
    main()
