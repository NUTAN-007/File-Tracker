import os
import time
import subprocess
import psycopg2
from datetime import datetime
import traceback
import hashlib

# ====== Configuration ======
REPO_DIR = "/repo"
FILE_TO_TRACK = "tracked-file.txt"
GIT_REPO_URL = "https://github.com/NUTAN-007/File-Tracker.git"

DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres.tracker-ns.svc.cluster.local")

# ====== Git Helpers ======
def get_latest_commit_info():
    """Get author and timestamp from the latest commit."""
    result_author = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%an"],
        capture_output=True, text=True, check=True
    )
    author = result_author.stdout.strip()

    result_timestamp = subprocess.run(
        ["git", "-C", REPO_DIR, "log", "-1", "--pretty=format:%aI"],
        capture_output=True, text=True, check=True
    )
    timestamp = result_timestamp.stdout.strip()
    return author, timestamp

def file_has_changed():
    """Check if tracked-file.txt has changed on remote compared to local."""
    subprocess.run(["git", "-C", REPO_DIR, "fetch"], check=True)

    diff_result = subprocess.run(
        ["git", "-C", REPO_DIR, "diff", "HEAD..origin/main", "--name-only", FILE_TO_TRACK],
        capture_output=True, text=True, check=True
    )

    changed_files = diff_result.stdout.strip().split("\n") if diff_result.stdout.strip() else []
    print(f"[DEBUG] Changed files: {changed_files}")

    return FILE_TO_TRACK in changed_files

# ====== Database ======
def insert_change(author, timestamp, content):
    """Insert change into PostgreSQL DB."""
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
    print("[INFO] Inserted change into database.")

# ====== Main ======
if __name__ == "__main__":
    last_hash = None

    # Clone repo if not exists
    if not os.path.exists(os.path.join(REPO_DIR, ".git")):
        print("[INFO] Cloning repo into /repo...")
        subprocess.run(["git", "clone", GIT_REPO_URL, REPO_DIR], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "checkout", "main"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "branch", "--set-upstream-to=origin/main", "main"], check=True)
        print("[INFO] Repo cloned successfully.")
    else:
        print("[INFO] Repo already exists. Starting to monitor changes...")

    while True:
        try:
            if file_has_changed():
                with open(os.path.join(REPO_DIR, FILE_TO_TRACK), 'r') as f:
                    content = f.read()

                file_hash = hashlib.sha256(content.encode()).hexdigest()

                if file_hash == last_hash:
                    print("[INFO] File change detected in Git but content is identical — skipping DB insert.")
                else:
                    print("[INFO] Pulling latest changes from Git...")
                    subprocess.run(["git", "-C", REPO_DIR, "pull", "--rebase"], check=True)

                    author, timestamp = get_latest_commit_info()
                    print(f"[INFO] Change by {author} at {timestamp}")

                    insert_change(author, timestamp, content)
                    last_hash = file_hash
            else:
                print("[INFO] No change detected in tracked-file.txt.")
        except Exception as e:
            print("[ERROR] An exception occurred:")
            traceback.print_exc()

        time.sleep(30)
