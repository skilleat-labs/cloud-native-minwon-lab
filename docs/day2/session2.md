# Day 2 · 2차시 — 같은 민원 서비스를 어디서나 동일하게 실행하라

**소요 시간**: 50분 (11:00~11:50)
**목표**: 준비된 이미지를 컨테이너로 실행하고, 포트와 환경 변수 주입 방식을 이해한다

---

## 이번 차시에 하는 것

| STEP | 내용 |
|------|------|
| 01 | App VM에 Docker 설치 |
| 02 | NCR 로그인 |
| 03 | 이미지 Pull & 컨테이너 실행 |
| 04 | 동작 확인 |
| 05 | 컨테이너 삭제 후 재실행 — 상태 관찰 |

---

## 개념 — 컨테이너를 실행할 때 정해야 하는 세 가지

| 결정 사항 | 내용 | 예시 |
|---------|------|------|
| 무엇을 실행할 것인가 | 이미지 이름과 태그 | `complaint-app:latest` |
| 어떤 포트로 들어올 것인가 | 호스트 포트 → 컨테이너 포트 | `80 → 8080` |
| 어떤 설정으로 동작할 것인가 | 환경 변수로 주입 | DB 주소, 계정, 버킷 정보 |

---

## 개념 — 포트 연결 구조

```
외부 요청 (브라우저)
        ↓
VM(호스트): 80번 포트로 들어온 요청을 컨테이너 8080으로 전달
        ↓
컨테이너: 앱이 듣고 있는 8080 포트
```

컨테이너는 자기만의 네트워크 공간을 가집니다. 컨테이너 안의 포트는 밖에서 그대로 보이지 않으므로 `-p 호스트포트:컨테이너포트` 로 연결해줘야 합니다.

---

## 개념 — 설정을 이미지 밖으로 빼는 이유

### 이미지 안에 설정을 넣으면 (문제)

- DB 주소가 바뀌면 이미지를 다시 만들어야 함
- 이미지 안에 비밀번호가 그대로 남음
- 개발/운영 환경마다 이미지를 따로 관리해야 함

### 환경 변수로 주입하면 (장점)

- 이미지는 하나, 환경마다 다른 값만 주입
- 민감한 값은 별도로 분리 가능
- 같은 이미지로 개발·검증·운영을 모두 커버

!!! tip "핵심"
    이미지는 어디서나 같고, 설정은 환경마다 다르다.

---

## STEP 01 — App VM에 Docker 설치

App VM에 SSH로 접속합니다.

```bash
ssh -i MyKey.pem ubuntu@<App-VM-플로팅-IP>
```

Docker를 설치합니다.

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker
```

설치 확인:

```bash
docker --version
# Docker version 24.x.x ← 정상
```

---

## STEP 02 — NCR 로그인

NCR에 로그인해야 이미지를 Pull할 수 있습니다.

```
Containers > NCR > [minwon-registry] > 기본 정보
→ 로그인 명령어 확인 및 복사
```

콘솔에서 복사한 명령어를 실행합니다.

```bash
docker login {레지스트리 주소}
# Username: {NHN Cloud 이메일}
# Password: {API 비밀번호}
```

`Login Succeeded` 가 나오면 성공입니다.

---

## STEP 03 — 이미지 Pull & 컨테이너 실행

### 이미지 받기

```bash
docker pull {레지스트리 주소}/complaint-app:latest
```

### 컨테이너 실행

```bash
docker run -d \
  --name complaint-app \
  -p 8080:8080 \
  -e DB_HOST=<DB-VM-사설-IP> \
  -e DB_PORT=3306 \
  -e DB_USER=complaint_user \
  -e DB_PASSWORD=Minjeon2024! \
  -e DB_NAME=complaints_db \
  -e OBJECT_STORAGE_URL=https://kr1-api-object-storage.nhncloudservice.com/v1/AUTH_{TenantID} \
  -e OBJECT_STORAGE_CONTAINER=minwon-attachments \
  -e OS_USERNAME={NHN Cloud 이메일} \
  -e OS_PASSWORD={API 비밀번호} \
  {레지스트리 주소}/complaint-app:latest
```

!!! danger "DB_HOST를 반드시 실제 DB VM 사설 IP로 변경하세요"

---

## STEP 04 — 동작 확인

```bash
# 컨테이너 실행 상태 확인
docker ps
# CONTAINER ID   IMAGE           STATUS          PORTS
# abc123         complaint-app   Up 30 seconds   0.0.0.0:8080->8080/tcp

# 앱 응답 확인
curl http://localhost:8080/health
# {"status": "ok"} ← 정상

# 로그 확인
docker logs complaint-app
```

브라우저에서 `http://<App-VM-플로팅-IP>:8080` 으로 접속해서 1일차 민원 데이터가 보이는지 확인합니다.

---

## STEP 05 — 컨테이너 삭제 후 재실행 관찰

### 컨테이너 안에서 파일 만들기

```bash
docker exec complaint-app touch /tmp/my-test-file.txt
docker exec complaint-app ls /tmp/
# my-test-file.txt ← 존재함
```

### 컨테이너 삭제 후 재실행

```bash
docker rm -f complaint-app

# 동일한 명령으로 다시 실행 (STEP 03 명령어 그대로)
docker run -d --name complaint-app -p 8080:8080 \
  -e DB_HOST=<DB-VM-사설-IP> \
  ... (동일한 환경 변수)
  {레지스트리 주소}/complaint-app:latest
```

### 관찰

```bash
# 아까 만든 파일이 사라졌는가?
docker exec complaint-app ls /tmp/
# (파일 없음) ← 컨테이너가 새로 만들어졌기 때문

# DB의 민원 데이터는 남아 있는가?
curl http://localhost:8080
# 데이터가 그대로 보임 ← DB는 컨테이너 밖에 있기 때문
```

| 관찰 항목 | 결과 | 이유 |
|---------|------|------|
| 컨테이너 안 파일 | 사라짐 | 컨테이너는 새로 만들어진 것 |
| DB의 민원 데이터 | 그대로 | DB는 컨테이너 밖(VM)에 있음 |
| Object Storage 첨부파일 | 그대로 | Object Storage는 컨테이너 밖 |

!!! tip "핵심"
    컨테이너는 언제든 사라질 수 있다고 가정하고 설계한다.
    저장해야 하는 것은 모두 컨테이너 밖(DB, Object Storage)에 두어야 한다.

---

## 2차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|---------|---------|
| ① | Docker가 설치되었다 | `docker --version` |
| ② | NCR 로그인이 성공했다 | `Login Succeeded` |
| ③ | 컨테이너가 실행 중이다 | `docker ps` |
| ④ | 브라우저에서 민원 서비스가 접속된다 | 브라우저 확인 |
| ⑤ | 컨테이너를 지워도 DB 데이터는 남는다 | 재실행 후 데이터 확인 |

---

**다음 차시**: 컨테이너가 여러 개가 되면 누가 관리할까요? Kubernetes로 넘어갑니다.
