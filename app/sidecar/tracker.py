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
DB_HOST = os.getenv("DB_HOST", "postgres")

def get_latest_commit_info():
    try:
        result = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%H|%an|%ai"],
            capture_output=True, text=True, check=True
        )
        commit_hash, author, timestamp = result.stdout.split("|", 2)
        return commit_hash, author, timestamp
    except Exception:
        return None, None, None

def file_changed_in_latest_commit(file_path):
    try:
        result = subprocess.run(
            ["git", "-C", REPO_DIR, "show", "--name-only", "--pretty=format:", "HEAD"],
            capture_output=True, text=True, check=True
        )
        changed_files = result.stdout.strip().split("\n")
        return file_path in changed_files
    except Exception:
        return False

def insert_change(content, author, timestamp):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO changes (content, author, timestamp) VALUES (%s, %s, %s)",
            (content, author, timestamp)
        )
        conn.commit()
        cur.close()
        conn.close()
        print("Change inserted into DB.")
    except Exception as e:
        print("Database error:", e)

if __name__ == "__main__":
    subprocess.run(["git", "-C", REPO_DIR, "pull"], check=False)

    commit_hash, author, timestamp = get_latest_commit_info()

    if file_changed_in_latest_commit(FILE_TO_TRACK):
        try:
            with open(os.path.join(REPO_DIR, FILE_TO_TRACK), "r") as f:
                content = f.read()
            insert_change(content, author, timestamp)
        except FileNotFoundError:
            print(f"{FILE_TO_TRACK} not found.")
    else:
        print(f"No changes detected in {FILE_TO_TRACK}. Skipping DB insert.")
