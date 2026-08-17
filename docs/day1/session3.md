# Day 1 · 3차시 — 민원 서비스를 실행할 서버와 DB를 준비하라

**소요 시간**: 50분 (13:00~13:50)
**목표**: App VM과 DB VM을 생성하고, DB용 Block Storage를 연결·마운트한다

---

## 이번 차시에 만드는 것

| STEP | 자원 | 역할 |
|------|------|------|
| 01 | App VM | 민원 서비스 실행 서버 |
| 02 | DB VM | 민원 데이터 저장 서버 |
| 03 | Block Storage | DB 데이터 전용 디스크 |
| 04 | Block Storage 연결 및 마운트 | 데이터 디스크 준비 |

---

## 개념 — App VM vs DB VM 역할 분담

| 구분 | App VM | DB VM |
|------|--------|-------|
| 하는 일 | 민원 화면 출력, 접수 처리, 파일 업로드 | 민원 데이터 저장, 쿼리 처리 |
| 외부 노출 | LB 경유 (플로팅 IP 없음) | 없음 (사설 IP만) |
| 확장 | 여러 대로 늘릴 수 있음 | 교체해도 데이터 유지 |

!!! tip "핵심"
    App Tier는 갈아 끼울 수 있는 계층, DB Tier는 지켜야 하는 계층입니다.

---

## STEP 01 — App VM 생성

### 콘솔 경로

```
Compute > Instance > 인스턴스 생성
```

### 설정값

| 항목 | 값 |
|------|---|
| 이름 | `minwon-app-01` |
| 이미지 | Ubuntu Server 22.04 LTS |
| 인스턴스 타입 | `t2.c1m1` (1 vCPU, 1GB RAM) |
| 가용성 영역 | 한국(판교) 선택 |
| 루트 디스크 | HDD 20GB |
| VPC | `minwon-vpc` |
| 서브넷 | `minwon-subnet-app` |
| 보안 그룹 | `minwon-sg-app` |
| 키페어 | 새로 생성 또는 기존 키페어 선택 |
| 플로팅 IP | 연결 안 함 (LB 경유) |

!!! warning "키페어 주의"
    개인 키(.pem) 파일은 생성 시점에 **딱 한 번만** 다운로드됩니다.
    잃어버리면 SSH 접속이 불가능합니다. 반드시 보관하세요.

### 인스턴스 타입 참고

| 타입 | 특성 | 용도 |
|------|------|------|
| t2 | 저비용, 낮은 워크로드 | **실습용** (이 과정에서 사용) |
| m2 | CPU·메모리 균형 | 일반 웹 서버 |
| c2 | 고성능 연산 | 배치 처리 |
| r2 | 메모리 집약 | 캐시, 대용량 처리 |

---

## STEP 02 — DB VM 생성

### 설정값

| 항목 | 값 |
|------|---|
| 이름 | `minwon-db-01` |
| 이미지 | Ubuntu Server 22.04 LTS |
| 인스턴스 타입 | `t2.c1m1` (1 vCPU, 1GB RAM) |
| 가용성 영역 | App VM과 **동일한 AZ** ← Block Storage 연결 조건 |
| 루트 디스크 | HDD 20GB |
| VPC | `minwon-vpc` |
| 서브넷 | `minwon-subnet-db` |
| 보안 그룹 | `minwon-sg-db` |
| 키페어 | App VM과 동일한 키페어 사용 권장 |
| 플로팅 IP | 연결 안 함 |

!!! warning "가용성 영역(AZ) 확인"
    Block Storage는 **같은 AZ의 인스턴스에만** 연결할 수 있습니다.
    DB VM과 Block Storage의 AZ를 반드시 일치시키세요.

---

## STEP 03 — Block Storage 생성

### 콘솔 경로

```
Storage > Block Storage > 블록 스토리지 생성
```

### 설정값

| 항목 | 값 |
|------|---|
| 이름 | `minwon-db-disk` |
| 가용성 영역 | DB VM과 **동일한 AZ** |
| 타입 | HDD |
| 크기 | 20GB |

### 왜 DB 데이터를 별도 Block Storage에 두는가

| 이유 | 설명 |
|------|------|
| 데이터 보호 | DB VM을 삭제·교체해도 Block Storage는 남음 |
| 수명 주기 분리 | OS 디스크와 데이터 디스크를 따로 관리 |
| 용량 확장 | 데이터 디스크만 별도로 늘릴 수 있음 |

---

## STEP 04 — Block Storage 연결 및 마운트

### 4-1. 콘솔에서 연결

```
Storage > Block Storage > [minwon-db-disk] > 연결 관리
→ 인스턴스: minwon-db-01 선택 → 연결
```

### 4-2. DB VM에서 마운트 (SSH 접속 후)

먼저 DB VM에 SSH로 접속합니다.

```bash
# App VM에 플로팅 IP가 없으므로, 임시로 DB VM에 플로팅 IP를 붙이거나
# Bastion Host 경유로 접속합니다.
# 실습에서는 강사 안내에 따라 접속합니다.
ssh -i MyKey.pem ubuntu@<DB-VM-플로팅-IP>
```

### 4-3. 디스크 인식 확인

```bash
lsblk
# 새로운 디스크(vdb)가 보이는지 확인
# NAME   SIZE
# vda    20G   ← 루트 디스크
# vdb    20G   ← 방금 연결한 Block Storage
```

### 4-4. 파티션 생성

```bash
echo -e "n\np\n1\n\n\nw" | sudo fdisk /dev/vdb
```

### 4-5. 파일시스템 생성

```bash
sudo mkfs -t xfs /dev/vdb1
```

### 4-6. 마운트 및 자동 마운트 등록

```bash
# 마운트 지점 생성
sudo mkdir -p /mnt/data

# 마운트
sudo mount /dev/vdb1 /mnt/data

# 재부팅 후 자동 마운트 등록
echo "/dev/vdb1 /mnt/data xfs defaults 0 0" | sudo tee -a /etc/fstab

# 확인
df -h | grep mnt
```

---

## STEP 05 — App VM에서 DB VM 통신 확인

App VM에 SSH로 접속한 뒤 DB VM 사설 IP로 통신이 되는지 확인합니다.

```bash
# DB VM 사설 IP 확인 (콘솔 Compute > Instance > DB VM 상세)
# 예: 192.168.1.10

# App VM에서 DB 포트 연결 테스트
nc -zv 192.168.1.10 3306
# Connection to 192.168.1.10 3306 port [tcp/mysql] succeeded! ← 성공
```

통신이 안 되면 확인 순서:

1. DB VM이 실행 중인가?
2. `minwon-sg-db`의 원격이 `minwon-sg-app`으로 지정되어 있는가?
3. 두 VM이 같은 VPC 안에 있는가?

---

## 3차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|----------|---------|
| ① | App VM이 실행 중이고 `minwon-sg-app`이 적용되었는가 | Compute > Instance 상세 |
| ② | DB VM이 실행 중이고 `minwon-sg-db`이 적용되었는가 | Compute > Instance 상세 |
| ③ | Block Storage가 DB VM과 같은 AZ에 있는가 | Storage > Block Storage |
| ④ | Block Storage가 DB VM에 연결되고 마운트되었는가 | `df -h` 결과 확인 |
| ⑤ | App VM → DB VM 사설 IP 통신이 되는가 | `nc -zv <DB-IP> 3306` |

---

**다음 차시**: DB를 초기화하고 민원 서비스를 사용자 스크립트로 자동 배포합니다.
