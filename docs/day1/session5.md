# Day 1 · 5차시 — 민원 데이터와 첨부파일을 안전하게 저장하라

**소요 시간**: 50분 (15:00~15:50)
**목표**: Object Storage 컨테이너를 만들고, 첨부파일이 버킷에 저장되는 흐름을 확인한다

---

## 이번 차시에 하는 것

| STEP | 작업 |
|------|------|
| 01 | Object Storage 서비스 활성화 |
| 02 | 컨테이너(버킷) 생성 |
| 03 | 앱에 Object Storage 연결 설정 |
| 04 | 첨부파일 업로드 후 저장 결과 확인 |

---

## 개념 — 왜 첨부파일을 Object Storage에 저장하는가

### App VM 로컬에 저장하면 생기는 문제

```
App VM 1 (파일 저장)     App VM 2
      ↑                       ↑
  사용자 A                사용자 B
  "내 파일 어디 갔지?"
```

- App VM이 2대 이상이면 파일이 **한 서버에만** 저장됨
- LB가 다른 서버로 보내면 파일을 찾을 수 없음
- App VM을 삭제하면 파일도 사라짐

### Object Storage를 쓰면

```
App VM 1 ──┐
           ├──→ Object Storage (공용 버킷)
App VM 2 ──┘
```

- 몇 대의 서버든 같은 버킷에서 파일 접근 가능
- 서버를 삭제해도 파일은 유지
- 용량 제한 없음

---

## 개념 — 3가지 스토리지 선택 기준

| 항목 | Block Storage | NAS | Object Storage |
|------|-------------|-----|---------------|
| 연결 방식 | 디스크로 직접 연결 | 네트워크 마운트 | HTTP REST API |
| 동시 접근 | 1대만 가능 | 여러 대 동시 가능 | 제한 없음 |
| 위치 제약 | 같은 AZ만 | 프로젝트 네트워크 안 | 리전 어디서나 |
| 실습 용도 | **DB 데이터** | (개념 비교용) | **첨부파일** |

!!! tip "선택 기준"
    - 한 서버 전용 → **Block Storage**
    - 여러 서버 공유 → **NAS**
    - 웹에서 HTTP로 접근 → **Object Storage**

---

## 개념 — 저장 위치별 역할

| 저장 위치 | 저장하는 것 | 이유 |
|---------|-----------|------|
| DB (Block Storage) | 민원 번호, 제목, 내용, 상태, **파일 경로** | 검색·정렬이 필요한 구조화 데이터 |
| Object Storage | 첨부 이미지, PDF **파일 본문** | 크기가 크고, 여러 서버 동시 접근 필요 |
| App VM 로컬 | 저장하지 않음 | 서버 증가·교체 시 파일 소실 위험 |

**업로드 흐름:**
```
사용자 (첨부파일 선택)
      ↓
App VM (파일 수신)
      ↓
Object Storage ← 파일 본문 저장
DB VM          ← 파일 경로(URL)만 기록
```

---

## STEP 01 — Object Storage 서비스 활성화

### 콘솔 경로

```
상단 메뉴 > 서비스 선택 > Storage > Object Storage > 서비스 활성화
```

### 활성화 방법

1. 콘솔 상단 **서비스 선택** 클릭
2. 왼쪽 분류에서 **Storage** 선택
3. **Object Storage** 항목에서 **서비스 활성화** 클릭
4. 왼쪽 메뉴에 **Storage > Object Storage** 가 나타나면 완료

!!! info "프로젝트당 한 번만 활성화하면 됩니다"
    이미 활성화된 경우 왼쪽 메뉴에서 바로 Object Storage가 보입니다.

---

## STEP 02 — 컨테이너(버킷) 생성

### 콘솔 경로

```
Storage > Object Storage > 컨테이너 생성
```

### 설정값

| 항목 | 값 |
|------|---|
| 이름 | `minwon-attachments` |
| 접근 정책 | **PRIVATE** |
| 스토리지 클래스 | Standard |

### 접근 정책 비교

| 정책 | 설명 | 언제 사용 |
|------|------|---------|
| PRIVATE | 프로젝트 사용자만 접근 (인증 토큰 필요) | **민원 첨부파일 (기본값)** |
| PUBLIC | URL만 알면 인증 없이 접근 가능 | 공개 안내 자료, 정적 파일 |

!!! warning "민원 첨부파일은 반드시 PRIVATE"
    개인정보가 포함될 수 있는 파일을 PUBLIC으로 설정하면 누구나 URL로 접근 가능합니다.

---

## STEP 03 — Object Storage 접근 정보 확인

앱에서 Object Storage에 연결하려면 아래 정보가 필요합니다.

```
Storage > Object Storage > API 엔드포인트 확인
```

| 항목 | 위치 |
|------|------|
| Object Storage URL | API 엔드포인트 탭 |
| Tenant ID | API 엔드포인트 탭 |
| API User ID | 계정 설정 > API 보안 설정 |
| API Password | API 보안 설정에서 발급 |

---

## STEP 04 — 앱에 Object Storage 연결

App VM에 SSH로 접속한 뒤 환경변수 파일을 수정합니다.

```bash
sudo nano /opt/complaint-app/.env
```

아래 내용을 추가합니다:

```bash
# Object Storage 설정 (5차시)
OBJECT_STORAGE_URL=https://kr1-api-object-storage.nhncloudservice.com/v1/AUTH_{TenantID}
OBJECT_STORAGE_CONTAINER=minwon-attachments
OS_USERNAME={API User ID}
OS_PASSWORD={API Password}
```

앱 재시작:

```bash
sudo systemctl restart complaint-app
sudo systemctl status complaint-app
```

---

## STEP 05 — 첨부파일 업로드 및 확인

### 5-1. 민원 접수 시 첨부파일 업로드

```
브라우저 → http://<LB-플로팅-IP>
→ 민원 접수 → 첨부파일 선택 → 접수
```

### 5-2. Object Storage에서 파일 확인

```
Storage > Object Storage > [minwon-attachments]
→ 업로드한 파일이 목록에 보이면 성공
```

### 5-3. DB에는 파일 경로(URL)만 저장되는지 확인

```
민원 상세 화면 → 첨부파일 링크 클릭 → 파일이 열리면 성공
```

---

## Object Storage 주요 기능 (운영 관점)

| 기능 | 설명 |
|------|------|
| 버전 관리 | 오브젝트 업데이트 이력 관리, 이전 버전 복원 |
| 객체 잠금 (WORM) | 지정 기간 동안 덮어쓰기·삭제 방지 (보존 의무 자료) |
| 수명 주기 제어 | 보관 기간 지정 후 자동 삭제 |
| 컨테이너 복제 | 다른 리전으로 자동 복제 (재해 대비) |
| 서버 측 암호화 | 저장 시 자동 암호화 |
| S3 호환 API | AWS SDK 및 서드파티 도구 사용 가능 |

---

## 5차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|----------|---------|
| ① | Object Storage 서비스가 활성화되었다 | Storage > Object Storage 메뉴 진입 가능 |
| ② | `minwon-attachments` 컨테이너가 PRIVATE으로 생성되었다 | 컨테이너 상세 확인 |
| ③ | 민원 신청 시 첨부파일이 버킷에 저장된다 | Object Storage 오브젝트 목록 |
| ④ | DB에는 파일 본문이 아닌 경로(URL)가 저장된다 | 민원 상세에서 첨부파일 링크 동작 확인 |

---

## 1일차 최종 확인 — 외부에서 전체 흐름 테스트

1. 브라우저에서 `http://<LB-플로팅-IP>` 접속
2. 새 민원 접수 (제목, 내용 입력)
3. 첨부파일 업로드 (이미지 또는 PDF)
4. 민원 목록에서 접수된 내용 확인
5. 첨부파일 링크 클릭 후 파일 열기

모두 확인되면 **1일차 미션 완료**입니다.

!!! warning "2일차를 위해 반드시 남겨두세요"
    | 자원 | 이유 |
    |------|------|
    | DB VM | 2일차에도 기존 민원 데이터 그대로 사용 |
    | Block Storage | DB VM에 연결된 상태 유지 |
    | Object Storage 컨테이너 | 기존 첨부파일 유지 |
    | VPC, 서브넷 | Kubernetes 클러스터도 같은 네트워크 사용 |
