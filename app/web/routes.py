import os
import uuid
import subprocess
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory

from app.downloader.core import download_mp3
from app.common.config import DOWNLOAD_DIR, FLASK_HOST, FLASK_PORT

app = Flask(__name__, template_folder="templates")

_jobs: dict = {}
_jobs_lock = threading.Lock()

HOME = os.path.expanduser("~")
MUSL_BIN = "/data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code-linux-arm64-musl/claude"


def ask_claude(message):
    result = subprocess.run(
        ["proot-distro", "login", "alpine", "--bind", f"{HOME}:/root", "--", MUSL_BIN, "-p", message],
        capture_output=True, text=True, timeout=120,
    )
    stderr_clean = "\n".join(l for l in result.stderr.splitlines() if not l.startswith("proot warning"))
    if result.returncode != 0:
        raise RuntimeError(stderr_clean or "claude CLI 오류")
    return result.stdout.strip()


def _run_job(job_id: str, url: str):
    def on_progress(stage: str):
        with _jobs_lock:
            job = _jobs[job_id]
            if stage == "analyzing":
                job["stage"] = "analyzing"; job["progress"] = 0
            elif stage == "converting":
                job["stage"] = "converting"; job["progress"] = 99
            elif stage == "duplicate":
                job["stage"] = "duplicate"; job["progress"] = 100
            elif stage.startswith("downloading:"):
                pct_str = stage.split(":", 1)[1].replace("%", "").strip()
                try:
                    pct = float(pct_str)
                except ValueError:
                    pct = 0
                job["stage"] = "downloading"; job["progress"] = round(pct, 1)

    result = download_mp3(url, on_progress=on_progress)
    with _jobs_lock:
        if result.success:
            _jobs[job_id].update({"status": "done", "stage": "done", "progress": 100,
                                   "title": result.title, "filename": os.path.basename(result.filepath)})
        else:
            _jobs[job_id].update({"status": "error", "stage": "error", "error": result.error})


# ── 미디어 노드 라우트 ──────────────────────────────────────────────────────

@app.route("/")
def index():
    files = sorted(os.listdir(DOWNLOAD_DIR), reverse=True) if os.path.isdir(DOWNLOAD_DIR) else []
    seen = set(); mp3_files = []
    for f in files:
        if f.endswith(".mp3") and f not in seen:
            seen.add(f); mp3_files.append(f)
    return render_template("index.html", files=mp3_files)


@app.route("/download", methods=["POST"])
def start_download():
    url = (request.json or {}).get("url", "").strip()
    if not url:
        return jsonify({"error": "URL이 없습니다."}), 400
    job_id = str(uuid.uuid4())[:8]
    with _jobs_lock:
        _jobs[job_id] = {"status": "running", "stage": "queued", "progress": 0}
    threading.Thread(target=_run_job, args=(job_id, url), daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/status/<job_id>")
def job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if job is None:
        return jsonify({"error": "없는 작업"}), 404
    return jsonify(job)


@app.route("/files/<filename>", methods=["GET"])
def serve_file(filename: str):
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)


@app.route("/files/<filename>", methods=["DELETE"])
def delete_file(filename: str):
    safe = os.path.basename(filename)
    path = os.path.join(DOWNLOAD_DIR, safe)
    if not os.path.isfile(path):
        return jsonify({"error": "파일 없음"}), 404
    os.remove(path)
    return jsonify({"deleted": safe})


# ── Claude 채팅 라우트 ──────────────────────────────────────────────────────

@app.route("/claude")
def claude_index():
    return render_template("claude.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = (request.json or {}).get("message", "").strip()
    if not user_message:
        return jsonify({"error": "메시지를 입력해주세요."}), 400
    try:
        return jsonify({"reply": ask_claude(user_message)})
    except FileNotFoundError:
        return jsonify({"error": "claude CLI를 찾을 수 없습니다."}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "응답 시간 초과 (120초)"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api", methods=["POST"])
def api():
    if request.is_json:
        data = request.json or {}
        user_message = (data.get("msg") or data.get("message") or "").strip()
    else:
        user_message = (request.form.get("msg") or request.form.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "메시지를 입력해주세요."}), 400
    try:
        reply = ask_claude(user_message)
        if request.args.get("format") == "text":
            return reply, 200, {"Content-Type": "text/plain; charset=utf-8"}
        return jsonify({"reply": reply})
    except FileNotFoundError:
        return jsonify({"error": "claude CLI를 찾을 수 없습니다."}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "응답 시간 초과 (120초)"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run():
    app.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True)
