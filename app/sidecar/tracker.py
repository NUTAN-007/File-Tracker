import os
import subprocess
import psycopg2
import traceback

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"

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
        commit_hash, author, timestamp = result.stdout.strip().split("|", 2)
        return commit_hash, author, timestamp
    except Exception:
        return None, None, None

def insert_change(content, author, timestamp, commit_hash):
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO changes (content, author, timestamp, commit_hash) VALUES (%s, %s, %s, %s)",
            (content, author, timestamp, commit_hash)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"Inserted commit {commit_hash} by {author}")
    except Exception as e:
        print("DB error:", e)
        traceback.print_exc()

if __name__ == "__main__":
    subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)

    commit_hash, author, timestamp = get_latest_commit_info()

    try:
        with open(os.path.join(REPO_DIR, FILE_TO_TRACK), "r") as f:
            content = f.read()
        insert_change(content, author, timestamp, commit_hash)
    except FileNotFoundError:
        print(f"{FILE_TO_TRACK} not found.")
