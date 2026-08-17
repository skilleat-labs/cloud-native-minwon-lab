# Day 1 · 4차시 — 준비된 민원 서비스를 자동으로 배포하라

**소요 시간**: 50분 (14:00~14:50)
**목표**: 사용자 스크립트로 DB를 초기화하고 앱을 자동 배포한 뒤, Load Balancer에 등록해 외부 접속을 확인한다

---

## 이번 차시에 하는 것

| STEP | 작업 |
|------|------|
| 01 | DB VM에서 DB 초기화 스크립트 실행 |
| 02 | App VM에 앱 배포 (사용자 스크립트 방식) |
| 03 | Load Balancer 멤버로 App VM 등록 |
| 04 | 헬스체크 통과 확인 |
| 05 | 브라우저에서 민원 서비스 접속 확인 |

---

## 개념 — 사용자 스크립트란

NHN Cloud 인스턴스는 생성 시 **사용자 스크립트(User Data)** 를 등록할 수 있습니다.
인스턴스가 처음 부팅될 때 **cloud-init**이 이 스크립트를 자동으로 실행합니다.

```
인스턴스 생성 클릭
      ↓
부팅 완료 (약 1~2분)
      ↓
cloud-init 실행 → 사용자 스크립트 자동 실행
      ↓
패키지 설치 → 소스 clone → 서비스 등록 → 시작
      ↓
서비스 자동 기동 완료
```

### 수동 설치 vs 사용자 스크립트 비교

| 구분 | 수동 설치 | 사용자 스크립트 |
|------|---------|--------------|
| 방법 | SSH 접속 → 명령 하나씩 실행 | 생성 시 스크립트 등록 |
| 서버 3대 | 같은 작업 3번 반복 | 스크립트 하나로 3대 동시 |
| 재현성 | 사람마다 결과가 다를 수 있음 | 항상 동일한 결과 |

!!! warning "사용자 스크립트는 최초 부팅 때 한 번만 실행"
    내용을 수정하려면 인스턴스를 다시 만들거나 서버에 SSH로 직접 접속해 실행해야 합니다.

---

## 이 과정의 앱 소스 위치

이 실습에서 사용하는 민원 서비스 소스코드는 GitHub 레포지토리에 있습니다.

```
https://github.com/skilleat-labs/cloud-native-minwon-lab
└── app/
    ├── app.py               # Flask 웹 앱
    ├── requirements.txt     # Python 의존성
    ├── templates/           # HTML 템플릿
    ├── static/              # CSS, JS
    └── scripts/
        ├── 01_init_db.sh    # DB 초기화 스크립트
        ├── 02_install_app.sh# 앱 수동 배포 스크립트
        └── 03_userdata_app.sh  # ← 사용자 스크립트 (인스턴스 생성 시 사용)
```

---

## STEP 01 — DB 초기화 스크립트 실행

DB VM에 SSH로 접속한 뒤 스크립트를 실행합니다.

```bash
# GitHub에서 스크립트 다운로드
curl -o /tmp/01_init_db.sh \
  https://raw.githubusercontent.com/skilleat-labs/cloud-native-minwon-lab/main/app/scripts/01_init_db.sh

# 실행 권한 부여 및 실행
chmod +x /tmp/01_init_db.sh
sudo bash /tmp/01_init_db.sh
```

스크립트가 자동으로 수행하는 작업:

| 단계 | 내용 |
|------|------|
| [1/4] | MySQL 8.0 설치 |
| [2/4] | MySQL 시작 및 자동 실행 설정 |
| [3/4] | DB · 계정 · 테이블 생성, 샘플 데이터 입력 |
| [4/4] | 외부 접속용 바인딩 설정 (0.0.0.0) |

완료 메시지 예시:
```
✅ 완료! App VM에서 아래 환경변수를 설정하세요:
  export DB_HOST=192.168.1.10
  export DB_USER=complaint_user
  export DB_PASSWORD=Minjeon2024!
  export DB_NAME=complaints_db
```

**DB VM의 사설 IP를 복사해 두세요.** STEP 02에서 사용합니다.

```bash
# DB VM 사설 IP 확인
hostname -I | awk '{print $1}'
```

---

## STEP 02 — 앱 배포 (두 가지 방법)

### 방법 A: 사용자 스크립트로 자동 배포 (권장) ⭐

App VM을 **새로 생성**할 때 사용자 스크립트 란에 아래 내용을 붙여넣습니다.

```
Compute > Instance > 인스턴스 생성
→ [추가 설정] > 사용자 스크립트
```

```bash
#!/bin/bash
set -e

# ── ① 이 값을 반드시 수정하세요 ────────────────────────────
DB_HOST="192.168.1.10"        # ← DB VM 사설 IP
DB_PORT="3306"
DB_USER="complaint_user"
DB_PASSWORD="Minjeon2024!"
DB_NAME="complaints_db"
APP_PORT="8080"
# ──────────────────────────────────────────────────────────

GITHUB_REPO="https://github.com/skilleat-labs/cloud-native-minwon-lab.git"
APP_DIR="/opt/complaint-app"

apt-get update -y
apt-get install -y python3 python3-pip git

git clone "$GITHUB_REPO" /tmp/minwon-repo
mkdir -p "$APP_DIR"
cp -r /tmp/minwon-repo/app/. "$APP_DIR/"

pip3 install -r "$APP_DIR/requirements.txt" --break-system-packages 2>/dev/null || \
  pip3 install -r "$APP_DIR/requirements.txt"

cat > "$APP_DIR/.env" <<EOF
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
PORT=${APP_PORT}
EOF

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
```

!!! info "사용자 스크립트 동작 확인"
    부팅 후 약 2~3분 뒤 아래 명령으로 확인하세요.
    ```bash
    sudo systemctl status complaint-app
    sudo journalctl -u complaint-app -f   # 실시간 로그
    ```

---

### 방법 B: SSH 직접 접속 후 수동 배포

이미 생성된 App VM이 있거나 사용자 스크립트 없이 배포할 때 사용합니다.

```bash
# App VM에 SSH 접속 후

# 스크립트 다운로드
curl -o /tmp/02_install_app.sh \
  https://raw.githubusercontent.com/skilleat-labs/cloud-native-minwon-lab/main/app/scripts/02_install_app.sh

# 환경변수 설정 후 실행
export DB_HOST=192.168.1.10   # ← DB VM 사설 IP
export DB_USER=complaint_user
export DB_PASSWORD=Minjeon2024!
export DB_NAME=complaints_db

chmod +x /tmp/02_install_app.sh
sudo -E bash /tmp/02_install_app.sh
```

---

## STEP 03 — App VM을 Load Balancer 멤버로 등록

### 콘솔 경로

```
Network > Load Balancer > [minwon-lb]
> 멤버 그룹 탭 > 멤버 추가
```

### 설정값

| 항목 | 값 |
|------|---|
| 인스턴스 | `minwon-app-01` |
| 목적지 포트 | `8080` |
| 가중치 | 1 |

---

## STEP 04 — 헬스체크 통과 확인

멤버를 등록하면 LB가 `/health` 엔드포인트로 상태 확인을 시작합니다.

```
Network > Load Balancer > [minwon-lb] > 멤버 상태
→ 상태: ACTIVE ← 정상
→ 상태: ERROR  ← 아래 확인 순서 참고
```

헬스체크 실패 시 확인 순서:

| 순서 | 확인 항목 |
|------|---------|
| 1 | `sudo systemctl status complaint-app` — 앱이 실행 중인가 |
| 2 | `curl http://localhost:8080/health` — 앱이 8080 포트로 응답하는가 |
| 3 | App 보안 그룹이 `192.168.0.0/24`에서 오는 8080 요청을 허용하는가 |
| 4 | LB 헬스체크 포트가 `8080`인가 |

---

## STEP 05 — 브라우저에서 민원 서비스 접속

LB 플로팅 IP로 접속합니다.

```
http://<LB-플로팅-IP>
```

확인 항목:

- [ ] 민원 서비스 메인 화면이 표시된다
- [ ] DB 연결 상태가 "연결됨"으로 표시된다
- [ ] 샘플 민원 3건이 목록에 보인다
- [ ] 새 민원을 접수하면 목록에 추가된다

---

## App-DB 연결 오류 시 점검 순서

| 순서 | 확인할 것 | 원인 |
|------|---------|------|
| 1 | DB VM이 실행 중인가 | 인스턴스 중지 상태 |
| 2 | MySQL 프로세스가 떠 있는가 | `sudo systemctl status mysql` |
| 3 | DB 보안 그룹이 App에서의 요청을 허용하는가 | 원격이 CIDR로 잘못 지정됨 |
| 4 | `.env`의 DB_HOST가 사설 IP인가 | 공인 IP를 적었거나 오타 |
| 5 | App VM과 DB VM이 같은 VPC인가 | 서브넷·VPC 오선택 |

!!! tip "연결 실패의 90%는 보안 그룹 또는 주소·포트 오타입니다"

---

## 4차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|----------|---------|
| ① | DB VM에서 MySQL이 실행 중이다 | `sudo systemctl status mysql` |
| ② | App VM에서 앱이 실행 중이다 | `sudo systemctl status complaint-app` |
| ③ | App VM이 LB 멤버로 등록되었다 | LB > 멤버 그룹 탭 |
| ④ | 헬스체크 상태가 ACTIVE다 | LB > 멤버 상태 |
| ⑤ | LB 플로팅 IP로 민원 서비스가 접속된다 | 브라우저 확인 |
| ⑥ | 민원을 접수하면 목록에서 조회된다 | 서비스 직접 사용 |

---

**다음 차시**: 첨부파일 저장을 Object Storage로 분리합니다.
