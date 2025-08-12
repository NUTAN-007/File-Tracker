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
DB_HOST = os.getenv("POSTGRES_HOST")

def init_repo():
    if not os.path.exists(REPO_DIR):
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
    else:
        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

def get_latest_commit_info():
    result_author = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an", "--", FILE_TO_TRACK],
        capture_output=True,
        text=True,
        check=True
    )
    author = result_author.stdout.strip()
    result_timestamp = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI", "--", FILE_TO_TRACK],
        capture_output=True,
        text=True,
        check=True
    )
    timestamp = result_timestamp.stdout.strip()
    return author, timestamp

def has_file_changed():
    result = subprocess.run(
        ["git", "-C", REPO_DIR, "fetch"], capture_output=True, text=True
    )
    subprocess.run(["git", "-C", REPO_DIR, "fetch"], check=True)
    diff_result = subprocess.run(
        ["git", "-C", REPO_DIR, "diff", "HEAD..origin/main", "--name-only", "--", FILE_TO_TRACK],
        capture_output=True,
        text=True
    )
    return FILE_TO_TRACK in diff_result.stdout.strip().split("\n")

def store_change_in_db(author, timestamp):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO changes (author, timestamp) VALUES (%s, %s)",
        (author, timestamp)
    )
    conn.commit()
    cur.close()
    conn.close()

def main():
    init_repo()
    last_author, last_timestamp = get_latest_commit_info()
    while True:
        try:
            if has_file_changed():
                subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
                author, timestamp = get_latest_commit_info()
                if author != last_author or timestamp != last_timestamp:
                    store_change_in_db(author, timestamp)
                    last_author, last_timestamp = author, timestamp
            time.sleep(10)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            time.sleep(10)

if __name__ == "__main__":
    main()
