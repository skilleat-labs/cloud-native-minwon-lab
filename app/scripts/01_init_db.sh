#!/bin/bash
# ============================================================
# 01_init_db.sh  —  DB VM 초기화 스크립트 (3차시 실습)
# 역할: MySQL 설치 → DB/계정/테이블 자동 생성
# 실행: DB VM에서 root로 실행
# ============================================================

set -e

# ── 설정값 (필요시 수정) ────────────────────────────────────
DB_NAME="complaints_db"
DB_USER="complaint_user"
DB_PASS="Minjeon2024!"   # 실제 수업에서는 강사가 지정한 값 사용
MYSQL_ROOT_PASS="Root2024!"

echo "==================================================="
echo " [1/4] MySQL 8.0 설치"
echo "==================================================="
sudo apt-get update -y
sudo apt-get install -y mysql-server

echo "==================================================="
echo " [2/4] MySQL 시작 및 자동 실행 설정"
echo "==================================================="
sudo systemctl start mysql
sudo systemctl enable mysql

echo "==================================================="
echo " [3/4] DB / 계정 / 테이블 생성"
echo "==================================================="
sudo mysql -u root <<EOF
-- DB 생성
CREATE DATABASE IF NOT EXISTS ${DB_NAME}
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 계정 생성 (어디서든 접속 허용)
CREATE USER IF NOT EXISTS '${DB_USER}'@'%' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;

-- 민원 테이블 생성
USE ${DB_NAME};
CREATE TABLE IF NOT EXISTS complaints (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(200)  NOT NULL,
    content     TEXT          NOT NULL,
    status      VARCHAR(20)   NOT NULL DEFAULT '접수',
    file_path   VARCHAR(500),
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4;

-- 샘플 데이터
INSERT INTO complaints (title, content, status) VALUES
  ('도로 포장 요청', '우리 동네 골목길이 많이 파손되어 보행에 불편함이 있습니다. 빠른 조치 부탁드립니다.', '접수'),
  ('가로등 고장 신고', '○○아파트 앞 가로등이 3일째 꺼져 있습니다. 야간 안전사고가 우려됩니다.', '처리중'),
  ('공원 시설 점검 요청', '어린이 공원의 시소가 파손되어 안전 위험이 있습니다. 점검을 요청드립니다.', '완료');

SELECT '테이블 생성 및 샘플 데이터 입력 완료' AS 결과;
EOF

echo "==================================================="
echo " [4/4] 외부 접속을 위한 MySQL 바인딩 설정"
echo "==================================================="
# 기본값 127.0.0.1 → 모든 인터페이스 허용
sudo sed -i 's/^bind-address\s*=.*/bind-address = 0.0.0.0/' /etc/mysql/mysql.conf.d/mysqld.cnf
sudo systemctl restart mysql

echo ""
echo "✅ 완료! App VM에서 아래 환경변수를 설정하세요:"
echo ""
echo "  export DB_HOST=$(hostname -I | awk '{print $1}')"
echo "  export DB_USER=${DB_USER}"
echo "  export DB_PASSWORD=${DB_PASS}"
echo "  export DB_NAME=${DB_NAME}"
echo ""
