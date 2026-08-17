#!/bin/bash
# ============================================================
# 02_install_app.sh  —  App VM 배포 스크립트 (4차시 실습)
# 역할: Python/Flask 설치 → 앱 실행
# 실행: App VM에서 실행 (사용자 스크립트 or SSH 직접 실행)
# ============================================================

set -e

# ── DB 연결 정보 (환경변수로 받거나 직접 지정) ──────────────
DB_HOST="${DB_HOST:-}"        # 예: 192.168.0.20
DB_PORT="${DB_PORT:-3306}"
DB_USER="${DB_USER:-complaint_user}"
DB_PASSWORD="${DB_PASSWORD:-Minjeon2024!}"
DB_NAME="${DB_NAME:-complaints_db}"
APP_PORT="${APP_PORT:-8080}"

APP_DIR="/opt/complaint-app"

echo "==================================================="
echo " [1/4] 패키지 설치"
echo "==================================================="
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip git

echo "==================================================="
echo " [2/4] 앱 소스 배포"
echo "==================================================="
sudo mkdir -p ${APP_DIR}
sudo cp -r /tmp/complaint-app/. ${APP_DIR}/   # 실습에서는 scp 또는 git clone 사용
sudo pip3 install -r ${APP_DIR}/requirements.txt --break-system-packages 2>/dev/null || \
  pip3 install -r ${APP_DIR}/requirements.txt

echo "==================================================="
echo " [3/4] 환경변수 파일 생성"
echo "==================================================="
sudo tee ${APP_DIR}/.env > /dev/null <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
PORT=${APP_PORT}
EOF

echo "==================================================="
echo " [4/4] systemd 서비스 등록 및 시작"
echo "==================================================="
sudo tee /etc/systemd/system/complaint-app.service > /dev/null <<EOF
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

sudo systemctl daemon-reload
sudo systemctl enable complaint-app
sudo systemctl restart complaint-app

echo ""
echo "✅ 완료! 서비스 상태:"
sudo systemctl status complaint-app --no-pager -l
echo ""
echo "🌐 접속 주소: http://$(hostname -I | awk '{print $1}'):${APP_PORT}"
