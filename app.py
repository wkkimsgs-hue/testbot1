import subprocess
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

MUSL_BIN = "/data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code-linux-arm64-musl/claude"


def ask_claude(message):
    result = subprocess.run(
        [MUSL_BIN, "-p", message],
        capture_output=True,
        text=True,
        timeout=120,
    )
    stderr_clean = "\n".join(l for l in result.stderr.splitlines() if not l.startswith("proot warning"))
    if result.returncode != 0:
        raise RuntimeError(stderr_clean or "claude CLI 오류")
    return result.stdout.strip()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
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
    # JSON 또는 폼 데이터 모두 허용, 필드명 msg / message 둘 다 허용
    if request.is_json:
        data = request.json or {}
        user_message = (data.get("msg") or data.get("message") or "").strip()
    else:
        user_message = (request.form.get("msg") or request.form.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "메시지를 입력해주세요."}), 400

    try:
        reply = ask_claude(user_message)
        # 봇 앱이 plain text를 원하면 ?format=text 쿼리 파라미터 사용
        if request.args.get("format") == "text":
            return reply, 200, {"Content-Type": "text/plain; charset=utf-8"}
        return jsonify({"reply": reply})
    except FileNotFoundError:
        return jsonify({"error": "claude CLI를 찾을 수 없습니다."}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "응답 시간 초과 (120초)"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5000)
