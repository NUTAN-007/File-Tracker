import os
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
DB_HOST = os.getenv("POSTGRES_HOST")

def run_git_command(cmd):
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True
    ).stdout.strip()

def get_latest_commit_info_for_file():
    commit_hash = run_git_command(["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%H", "--", FILE_TO_TRACK])
    author = run_git_command(["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an", "--", FILE_TO_TRACK])
    timestamp = run_git_command(["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI", "--", FILE_TO_TRACK])
    return commit_hash, author, timestamp

def clone_or_pull_repo():
    if not os.path.exists(REPO_DIR):
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
    else:
        subprocess.run(["git", "-C", REPO_DIR, "fetch", "origin"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "reset", "--hard", "origin/main"], check=True)

def get_last_commit_from_db(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT commit_hash FROM changes ORDER BY id DESC LIMIT 1;")
        row = cur.fetchone()
        return row[0] if row else None

def insert_change_to_db(conn, commit_hash, author, timestamp):
    with conn.cursor() as cur:
        cur.execute("INSERT INTO changes (commit_hash, author, timestamp) VALUES (%s, %s, %s);",
                    (commit_hash, author, timestamp))
    conn.commit()

def main():
    try:
        clone_or_pull_repo()

        commit_hash, author, timestamp = get_latest_commit_info_for_file()

        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST
        )

        last_commit_in_db = get_last_commit_from_db(conn)

        if commit_hash != last_commit_in_db:
            insert_change_to_db(conn, commit_hash, author, timestamp)
            print(f"Inserted new change: {commit_hash}, {author}, {timestamp}")
        else:
            print("No change in tracked file — skipping insert.")

        conn.close()

    except Exception as e:
        print("Error:", e)
        traceback.print_exc()

if __name__ == "__main__":
    main()
