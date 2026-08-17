# ============================================================
# Dockerfile  —  2일차 컨테이너 실습용
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# 의존성 먼저 복사 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# 업로드 디렉토리
RUN mkdir -p uploads

EXPOSE 8080

# 환경변수로 DB 연결 정보 주입 (docker run -e 또는 K8s Secret)
ENV DB_HOST=""
ENV DB_PORT="3306"
ENV DB_USER=""
ENV DB_PASSWORD=""
ENV DB_NAME="complaints_db"
ENV PORT="8080"

CMD ["python", "app.py"]
