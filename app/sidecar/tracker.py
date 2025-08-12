import os
import time
import subprocess
import psycopg2
import traceback
import hashlib

REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres.tracker-ns.svc.cluster.local")

last_hash = None  # To avoid duplicate inserts

def get_latest_commit_info():
    """Get author, timestamp, and changed files from the latest commit."""
    author = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"],
        capture_output=True, text=True, check=True
    ).stdout.strip()

    timestamp = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"],
        capture_output=True, text=True, check=True
    ).stdout.strip()

    changed_files = subprocess.run(
        ["git", "-C", REPO_DIR, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip().split("\n")

    return author, timestamp, changed_files

def insert_change(author, timestamp, content):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO changes (author, timestamp, content) VALUES (%s, %s, %s)",
        (author, timestamp, content)
    )
    conn.commit()
    conn.close()
    print(f"[INFO] Inserted change by {author} at {timestamp} into DB.")

if __name__ == "__main__":
    # Clone repo if not exists
    if not os.path.exists(os.path.join(REPO_DIR, ".git")):
        print("[INFO] Cloning repo...")
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "checkout", "main"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "branch", "--set-upstream-to=origin/main", "main"], check=True)
    else:
        print("[INFO] Repo already exists.")

    while True:
        try:
            # Always pull latest changes
            subprocess.run(["git", "-C", REPO_DIR, "fetch"], check=True)
            subprocess.run(["git", "-C", REPO_DIR, "pull", "--rebase"], check=True)

            author, timestamp, changed_files = get_latest_commit_info()
            print(f"[DEBUG] Latest commit changed files: {changed_files}")

            if FILE_TO_TRACK in changed_files:
                with open(os.path.join(REPO_DIR, FILE_TO_TRACK), 'r') as f:
                    content = f.read()

                file_hash = hashlib.sha256(content.encode()).hexdigest()
                if file_hash != last_hash:
                    insert_change(author, timestamp, content)
                    last_hash = file_hash
                else:
                    print("[INFO] File content unchanged, skipping DB insert.")
            else:
                print(f"[INFO] Latest commit did not change {FILE_TO_TRACK}, skipping.")
        except Exception:
            print("[ERROR] An exception occurred:")
            traceback.print_exc()

        time.sleep(30)
