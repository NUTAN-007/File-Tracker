from flask import Flask, render_template_string, jsonify
import os
import psycopg2

app = Flask(__name__)

# Securely read values from Kubernetes Secret & ConfigMap (no fallbacks)
DB_HOST = os.environ["DB_HOST"]               # From ConfigMap
DB_NAME = os.environ["POSTGRES_DB"]           # From Secret
DB_USER = os.environ["POSTGRES_USER"]         # From Secret
DB_PASS = os.environ["POSTGRES_PASSWORD"]     # From Secret

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Tracked File Viewer</title>
    <meta http-equiv="refresh" content="30"> <!-- Refresh every 30s -->
</head>
<body>
    <h1>File Content</h1>
    <pre>{{ content }}</pre>
    <h2>Last Update</h2>
    <p><strong>Author:</strong> {{ author or 'Unknown' }}</p>
    <p><strong>Timestamp:</strong> {{ timestamp or 'Unknown' }}</p>
</body>
</html>
"""

@app.route("/")
def index():
    try:
        with open("/repo/tracked-file.txt") as f:
            content = f.read()
    except Exception as e:
        content = f"Error reading file: {e}"

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("SELECT author, timestamp FROM changes ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        author = row[0] if row else None
        timestamp = row[1] if row else None
    except Exception as e:
        author = None
        timestamp = None
        content += f"\n\n(DB error: {e})"

    return render_template_string(HTML_TEMPLATE, content=content, author=author, timestamp=timestamp)

@app.route("/api")
def api():
    try:
        with open("/repo/tracked-file.txt") as f:
            content = f.read()
    except Exception as e:
        content = f"Error reading file: {e}"

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor()
        cur.execute("SELECT author, timestamp FROM changes ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        author = row[0] if row else None
        timestamp = row[1] if row else None
    except Exception as e:
        author = None
        timestamp = None

    return jsonify({
        "content": content,
        "author": author,
        "timestamp": timestamp
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
