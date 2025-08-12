import os
import time
import subprocess
import psycopg2
from datetime import datetime
import traceback

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")

def run_git_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout.strip()

def get_last_file_commit():
    commit_hash = run_git_command(["git", "-C", REPO_DIR, "log", "-n", "1", "--pretty=format:%H", "--", FILE_TO_TRACK])
    return commit_hash

def get_commit_info(commit_hash):
    author = run_git_command(["git", "-C", REPO_DIR, "show", "-s", "--pretty=format:%an", commit_hash])
    timestamp = run_git_command(["git", "-C", REPO_DIR, "show", "-s", "--pretty=format:%aI", commit_hash])
    return author, timestamp

def clone_or_pull_repo():
    if not os.path.exists(REPO_DIR):
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
    else:
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

def connect_db():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST
    )

def store_change(timestamp, author):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO changes (timestamp, author) VALUES (%s, %s)", (timestamp, author))
    conn.commit()
    cur.close()
    conn.close()

def main():
    clone_or_pull_repo()
    last_commit = get_last_file_commit()
    while True:
        try:
            subprocess.run(["git", "-C", REPO_DIR, "fetch"], check=True)
            current_commit = get_last_file_commit()
            if current_commit != last_commit:
                author, timestamp = get_commit_info(current_commit)
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                store_change(dt, author)
                last_commit = current_commit
            time.sleep(10)
        except Exception as e:
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    main()
