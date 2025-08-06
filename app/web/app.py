from flask import Flask, render_template_string, jsonify
import os
import psycopg2

app = Flask(__name__)

# Read credentials from environment variables
DB_HOST = os.environ.get("DB_HOST", "postgres")
DB_NAME = os.environ.get("DB_NAME", "trackdb")
DB_USER = os.environ.get("DB_USER", "tracker")
DB_PASS = os.environ.get("DB_PASS", "trackerpass")

@app.route("/")
def index():
    with open("/repo/tracked-file.txt") as f:
        content = f.read()

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    cur.execute("SELECT author, timestamp FROM changes ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    html = f"""
    <h1>File Content</h1><pre>{content}</pre>
    <h2>Last Update</h2>
    <p><b>Author:</b> {row[0]}</p>
    <p><b>Timestamp:</b> {row[1]}</p>
    """
    return html

@app.route("/api")
def api():
    with open("/repo/tracked-file.txt") as f:
        content = f.read()

    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    cur.execute("SELECT author, timestamp FROM changes ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    conn.close()

    return {
        "content": content,
        "author": row[0] if row else None,
        "timestamp": row[1] if row else None
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
