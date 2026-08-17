#!/bin/bash
# ============================================================
# 03_userdata_app.sh — App VM 사용자 스크립트 (4차시 실습)
# NHN Cloud 인스턴스 생성 시 "사용자 스크립트" 란에 붙여넣기
#
# 동작: 부팅 시 자동으로
#   1. GitHub에서 앱 소스 clone
#   2. 의존성 설치
#   3. systemd 서비스로 등록 및 시작
#
# ⚠️ DB_HOST는 반드시 실제 DB VM 사설 IP로 변경하세요
# ============================================================

#!/bin/bash
set -e

# ── ① 수정이 필요한 값 ──────────────────────────────────────
DB_HOST="192.168.1.10"        # ← DB VM 사설 IP로 변경
DB_PORT="3306"
DB_USER="complaint_user"
DB_PASSWORD="Minjeon2024!"
DB_NAME="complaints_db"
APP_PORT="8080"
GITHUB_REPO="https://github.com/skilleat-labs/cloud-native-minwon-lab.git"
APP_DIR="/opt/complaint-app"
# ────────────────────────────────────────────────────────────

echo "===== [1/5] 패키지 설치 ====="
apt-get update -y
apt-get install -y python3 python3-pip git

echo "===== [2/5] 소스 clone ====="
git clone "$GITHUB_REPO" /tmp/minwon-repo
mkdir -p "$APP_DIR"
cp -r /tmp/minwon-repo/app/. "$APP_DIR/"

echo "===== [3/5] 의존성 설치 ====="
pip3 install -r "$APP_DIR/requirements.txt" --break-system-packages 2>/dev/null || \
  pip3 install -r "$APP_DIR/requirements.txt"

echo "===== [4/5] 환경변수 파일 생성 ====="
cat > "$APP_DIR/.env" <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
PORT=${APP_PORT}
EOF

echo "===== [5/5] systemd 서비스 등록 ====="
cat > /etc/systemd/system/complaint-app.service <<EOF
[Unit]
Description=온라인 민원 서비스
After=network.target

[Service]
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=/usr/bin/python3 ${APP_DIR}/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable complaint-app
systemctl start complaint-app

echo "✅ 앱 배포 완료: http://$(hostname -I | awk '{print $1}'):${APP_PORT}"
