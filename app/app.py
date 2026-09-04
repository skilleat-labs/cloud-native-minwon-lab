import os
import socket
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "민원서비스-교육용-키")

# ── DB 설정 (환경변수로 주입) ──────────────────────────────────────────────
DB_CONFIG = {
    "host":   os.environ.get("DB_HOST", ""),
    "port":   int(os.environ.get("DB_PORT", "3306")),
    "user":   os.environ.get("DB_USER", ""),
    "password": os.environ.get("DB_PASSWORD", ""),
    "db":     os.environ.get("DB_NAME", "complaints_db"),
    "charset": "utf8mb4",
}

# ── Object Storage 설정 (Day-1 5차시 실습용) ────────────────────────────────
OBJECT_STORAGE_URL       = os.environ.get("OBJECT_STORAGE_URL", "")
OBJECT_STORAGE_CONTAINER = os.environ.get("OBJECT_STORAGE_CONTAINER", "minwon-attachments")
OS_USERNAME              = os.environ.get("OS_USERNAME", "")
OS_PASSWORD              = os.environ.get("OS_PASSWORD", "")
OBJECT_STORAGE_ENABLED   = bool(OBJECT_STORAGE_URL and OS_USERNAME and OS_PASSWORD)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB


# ── DB 연결 헬퍼 ────────────────────────────────────────────────────────────
def get_db_connection():
    """DB_HOST가 설정된 경우에만 연결을 시도합니다."""
    if not DB_CONFIG["host"]:
        return None
    try:
        import pymysql
        conn = pymysql.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            db=DB_CONFIG["db"],
            charset=DB_CONFIG["charset"],
            connect_timeout=3,
        )
        return conn
    except Exception:
        return None


def db_status():
    """DB 연결 상태 확인"""
    if not DB_CONFIG["host"]:
        return {"connected": False, "reason": "DB_HOST 환경변수가 설정되지 않았습니다"}
    conn = get_db_connection()
    if conn:
        conn.close()
        return {"connected": True, "host": DB_CONFIG["host"], "port": DB_CONFIG["port"]}
    return {"connected": False, "reason": f"{DB_CONFIG['host']} 에 연결할 수 없습니다"}


def init_db():
    """테이블이 없으면 자동 생성"""
    conn = get_db_connection()
    if not conn:
        return
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS complaints (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    title       VARCHAR(200) NOT NULL,
                    content     TEXT NOT NULL,
                    status      VARCHAR(20)  NOT NULL DEFAULT '접수',
                    file_path   VARCHAR(500),
                    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) CHARACTER SET utf8mb4
            """)
        conn.commit()
    finally:
        conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_os_token():
    """NHN Cloud Object Storage 인증 토큰 발급"""
    import urllib.request, json as _json
    auth_url = "https://api-identity.infrastructure.cloud.toast.com/v2.0/tokens"

    if not OBJECT_STORAGE_URL:
        logging.warning("[ObjectStorage] OBJECT_STORAGE_URL 환경변수가 설정되지 않았습니다.")
        return None
    if not OS_USERNAME:
        logging.warning("[ObjectStorage] OS_USERNAME 환경변수가 설정되지 않았습니다.")
        return None
    if not OS_PASSWORD:
        logging.warning("[ObjectStorage] OS_PASSWORD 환경변수가 설정되지 않았습니다.")
        return None

    try:
        tenant_id = OBJECT_STORAGE_URL.split("AUTH_")[1].rstrip("/")
    except IndexError:
        logging.error("[ObjectStorage] OBJECT_STORAGE_URL에서 Tenant ID를 추출할 수 없습니다: %s", OBJECT_STORAGE_URL)
        return None

    logging.info("[ObjectStorage] 토큰 발급 시도 — tenant_id=%s, username=%s", tenant_id, OS_USERNAME)

    payload = _json.dumps({
        "auth": {
            "tenantId": tenant_id,
            "passwordCredentials": {
                "username": OS_USERNAME,
                "password": OS_PASSWORD,
            }
        }
    }).encode("utf-8")
    req = urllib.request.Request(auth_url, data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = _json.loads(resp.read())
            token = data["access"]["token"]["id"]
            logging.info("[ObjectStorage] 토큰 발급 성공")
            return token
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        logging.error("[ObjectStorage] 토큰 발급 실패 — HTTP %s: %s", e.code, body)
        return None
    except Exception as e:
        logging.error("[ObjectStorage] 토큰 발급 중 오류: %s", e)
        return None


def upload_to_object_storage(file_obj, filename):
    """Object Storage에 파일 업로드 후 URL 반환. 실패 시 None 반환."""
    import urllib.request
    token = get_os_token()
    if not token:
        logging.error("[ObjectStorage] 토큰 없음 — 업로드 중단")
        return None
    url = f"{OBJECT_STORAGE_URL.rstrip('/')}/{OBJECT_STORAGE_CONTAINER}/{filename}"
    logging.info("[ObjectStorage] 업로드 시도 — %s", url)
    data = file_obj.read()
    req = urllib.request.Request(url, data=data, method="PUT",
                                 headers={"X-Auth-Token": token})
    try:
        with urllib.request.urlopen(req, timeout=10):
            logging.info("[ObjectStorage] 업로드 성공 — %s", url)
            return url
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        logging.error("[ObjectStorage] 업로드 실패 — HTTP %s: %s", e.code, body)
        return None
    except Exception as e:
        logging.error("[ObjectStorage] 업로드 중 오류: %s", e)
        return None


# ── 라우트 ─────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    status = db_status()
    complaints = []
    if status["connected"]:
        init_db()
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, title, status, created_at FROM complaints ORDER BY id DESC LIMIT 50"
                )
                complaints = cur.fetchall()
        finally:
            conn.close()
    sip = get_server_ip()
    return render_template("index.html", status=status, complaints=complaints,
                           server_ip=sip, lb=lb_status(), sv_color=server_color(sip))


@app.route("/submit", methods=["GET", "POST"])
def submit():
    status = db_status()
    if request.method == "POST":
        title   = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        if not title or not content:
            flash("제목과 내용을 모두 입력해주세요.", "danger")
            return render_template("submit.html", status=status, lb=lb_status(), server_ip=get_server_ip())

        file_path = None
        f = request.files.get("attachment")
        if f and f.filename and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            if OBJECT_STORAGE_ENABLED:
                # Object Storage에 업로드 (5차시)
                file_path = upload_to_object_storage(f.stream, filename)
                if not file_path:
                    flash("Object Storage 업로드 실패 — 로컬에 저장합니다.", "warning")
                    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                    f.save(save_path)
                    file_path = filename
            else:
                # Object Storage 미설정 시 로컬 저장
                save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
                f.save(save_path)
                file_path = filename

        if status["connected"]:
            init_db()
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO complaints (title, content, file_path) VALUES (%s, %s, %s)",
                        (title, content, file_path),
                    )
                conn.commit()
                flash("민원이 접수되었습니다.", "success")
            finally:
                conn.close()
        else:
            flash("DB에 연결되지 않아 저장되지 않았습니다. (DB 연결 후 재시도하세요)", "warning")

        return redirect(url_for("index"))

    return render_template("submit.html", status=status, lb=lb_status(), server_ip=get_server_ip())


@app.route("/complaint/<int:cid>")
def detail(cid):
    status = db_status()
    complaint = None
    if status["connected"]:
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM complaints WHERE id = %s", (cid,))
                complaint = cur.fetchone()
        finally:
            conn.close()
    return render_template("detail.html", status=status, complaint=complaint, cid=cid,
                           lb=lb_status(), server_ip=get_server_ip())


# ── 로컬 업로드 파일 서빙 ────────────────────────────────────────────────────
@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    from flask import send_from_directory
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ── Load Balancer 헬스체크 엔드포인트 ────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "server": get_server_ip()}), 200


# ── DB 상태 API (교육용: 브라우저에서 직접 확인 가능) ───────────────────────
@app.route("/api/db-status")
def api_db_status():
    return jsonify(db_status())


SERVER_IP = None

def get_server_ip():
    global SERVER_IP
    if SERVER_IP:
        return SERVER_IP
    try:
        # 실제 외부 통신에 사용하는 인터페이스 IP (루프백 127.x 제외)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        SERVER_IP = s.getsockname()[0]
        s.close()
    except Exception:
        try:
            SERVER_IP = socket.gethostbyname(socket.gethostname())
        except Exception:
            SERVER_IP = "unknown"
    return SERVER_IP


def server_color(ip):
    """서버 IP 마지막 옥텟으로 색상 결정 — 서버마다 다른 색이 나와 LB 분산을 시각화"""
    colors = ["sv-blue", "sv-green", "sv-orange", "sv-purple", "sv-red", "sv-teal"]
    try:
        idx = int(ip.split(".")[-1]) % len(colors)
    except Exception:
        idx = 0
    return colors[idx]


def lb_status():
    """LB 경유 여부를 요청 헤더로 감지"""
    xff = request.headers.get("X-Forwarded-For", "")
    proto = request.headers.get("X-Forwarded-Proto", "")
    port  = request.headers.get("X-Forwarded-Port", "")
    if xff:
        client_ip = xff.split(",")[0].strip()
        return {"connected": True, "client_ip": client_ip,
                "proto": proto or "http", "port": port or "80"}
    # K8s 환경에서는 L4 LB라 X-Forwarded-For 헤더가 없지만 실제로는 LB 경유 중
    if os.environ.get("KUBERNETES_SERVICE_HOST"):
        return {"connected": True, "client_ip": "K8s Service (L4 LB)",
                "proto": "http", "port": "80"}
    return {"connected": False}


@app.after_request
def disable_keepalive(response):
    # 매 요청마다 새 TCP 연결을 맺도록 강제 → LB 라운드로빈 분산 효과 확인 가능
    response.headers["Connection"] = "close"
    return response


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

