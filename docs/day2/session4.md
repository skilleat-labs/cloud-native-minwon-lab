# Day 2 · 4차시 — 기존 DB를 유지한 채 서비스를 배포하라

**소요 시간**: 50분 (14:00~14:50)
**목표**: Secret으로 연결 정보를 주입하고, YAML을 적용해 Pod에서 1일차 DB와 Object Storage에 연결한다

---

## 이번 차시에 하는 것

| STEP | 내용 |
|------|------|
| 01 | deployment.yaml 내용 파악 |
| 02 | Secret 값 수정 (DB IP, Object Storage 정보) |
| 03 | 배포 적용 (`kubectl apply`) |
| 04 | Pod 정상 실행 확인 |
| 05 | 브라우저에서 기존 데이터 연결 확인 |

---

## 개념 — Secret으로 연결 정보를 분리하는 이유

| 방식 | 문제 |
|------|------|
| YAML에 직접 작성 | YAML 파일을 보는 모든 사람이 비밀번호를 알게 됨 |
| 이미지 안에 포함 | 이미지를 Pull하면 비밀번호가 노출됨 |
| **Secret으로 분리** | 배포 정의(Deployment)와 비밀 값을 따로 관리 가능 |

DB 비밀번호가 바뀌어도 이미지를 다시 만들 필요 없이 **Secret 값만 교체**하면 됩니다.

---

## 개념 — YAML 읽는 법

### Deployment YAML 구조

```yaml
apiVersion: apps/v1
kind: Deployment          # 어떤 종류의 오브젝트인지
metadata:
  name: complaint-app     # 이 배포의 이름
spec:
  replicas: 1             # 유지할 Pod 개수
  selector:
    matchLabels:
      app: complaint-app  # 어떤 Pod를 관리할지 (라벨로 선택)
  template:
    metadata:
      labels:
        app: complaint-app # Pod에 붙이는 이름표
    spec:
      containers:
      - name: complaint-app
        image: {레지스트리}/complaint-app:latest  # 실행할 이미지
        ports:
        - containerPort: 8080
        envFrom:
        - secretRef:
            name: complaint-db-secret  # Secret에서 환경 변수 주입
```

### Service YAML 구조

```yaml
apiVersion: v1
kind: Service
metadata:
  name: complaint-service
spec:
  type: LoadBalancer       # 외부 노출 방식 (NHN Cloud LB 자동 생성)
  selector:
    app: complaint-app     # 이 라벨을 가진 Pod로 트래픽 전달
  ports:
  - port: 80               # 외부에서 접속할 포트
    targetPort: 8080       # Pod 안 컨테이너 포트
```

```
외부 → port: 80 → Service → targetPort: 8080 → Pod
```

---

## STEP 01 — deployment.yaml 확인

레포지토리에 준비된 YAML 파일을 확인합니다.

```bash
# 로컬 PC에서 레포지토리 clone (처음인 경우)
git clone https://github.com/skilleat-labs/cloud-native-minwon-lab.git
cd cloud-native-minwon-lab

# YAML 파일 위치 확인
ls app/
# Dockerfile  app.py  deployment.yaml  requirements.txt  ...
```

---

## STEP 02 — deployment.yaml 수정

`app/deployment.yaml` 파일에서 아래 항목을 실제 값으로 수정합니다.

```bash
# 편집기로 열기
nano app/deployment.yaml
```

### 수정해야 하는 값

**① Secret의 DB_HOST**

```yaml
stringData:
  DB_HOST: "192.168.0.20"    # ← DB VM 사설 IP로 변경
  DB_USER: "complaint_user"
  DB_PASSWORD: "Minjeon2024!"
  DB_NAME: "complaints_db"
```

**② Deployment의 이미지 주소**

```yaml
containers:
  - name: complaint-app
    image: <레지스트리 주소>/complaint-app:latest   # ← 실제 레지스트리 주소로 변경
```

!!! danger "두 곳을 반드시 수정하세요"
    - `DB_HOST`: 1일차 DB VM의 사설 IP
    - `image`: 1차시에서 확인한 NCR 레지스트리 주소

### Object Storage 설정 추가 (선택)

1일차에서 설정한 Object Storage도 연결하려면 Secret에 추가합니다.

```yaml
stringData:
  DB_HOST: "192.168.x.x"
  DB_USER: "complaint_user"
  DB_PASSWORD: "Minjeon2024!"
  DB_NAME: "complaints_db"
  OBJECT_STORAGE_URL: "https://kr1-api-object-storage.nhncloudservice.com/v1/AUTH_{TenantID}"
  OBJECT_STORAGE_CONTAINER: "minwon-attachments"
  OS_USERNAME: "{NHN Cloud 이메일}"
  OS_PASSWORD: "{API 비밀번호}"
```

---

## STEP 03 — 배포 적용

```bash
kubectl apply -f app/deployment.yaml
```

아래와 같이 출력되면 정상입니다.

```
secret/complaint-db-secret created
deployment.apps/complaint-app created
service/complaint-service created
```

### 배포가 실제로 일어나는 순서

1. `kubectl apply` → 컨트롤 플레인이 원하는 상태로 기록
2. 스케줄러가 배치할 노드 결정
3. 노드에서 NCR로부터 이미지 Pull
4. 컨테이너 실행 → Pod 준비 완료
5. Service가 해당 Pod를 대상에 포함

---

## STEP 04 — Pod 정상 실행 확인

```bash
# Pod 상태 확인 (Running이 될 때까지 반복)
kubectl get pods
# NAME                             READY   STATUS    RESTARTS   AGE
# complaint-app-7d4b9c8f6-xxxxx   1/1     Running   0          1m

# Deployment 확인
kubectl get deployments
# NAME            READY   UP-TO-DATE   AVAILABLE
# complaint-app   1/1     1            1

# Service 확인 (EXTERNAL-IP가 생길 때까지 1~2분 대기)
kubectl get services
# NAME                TYPE           CLUSTER-IP    EXTERNAL-IP      PORT(S)
# complaint-service   LoadBalancer   10.x.x.x     {공인IP}         80:xxxxx/TCP
```

!!! info "EXTERNAL-IP가 <pending>인 경우"
    NHN Cloud Load Balancer가 생성 중입니다. 1~2분 후 다시 확인하세요.

### Pod가 뜨지 않을 때 확인 순서

```bash
# Pod 상세 이벤트 확인
kubectl describe pod <Pod-이름>

# Pod 로그 확인
kubectl logs <Pod-이름>
```

| 증상 | 원인 |
|------|------|
| `ImagePullBackOff` | 이미지 주소 오타 또는 NCR 인증 실패 |
| `CrashLoopBackOff` | 앱 실행 오류 — `kubectl logs`로 원인 확인 |
| `Pending` | 노드에 자원 여유 없음 |

---

## STEP 05 — 기존 데이터 연결 확인

Service의 `EXTERNAL-IP`로 브라우저에서 접속합니다.

```
http://<EXTERNAL-IP>
```

확인 항목:

- [ ] 민원 서비스 메인 화면이 표시된다
- [ ] 1일차에 등록한 민원 데이터가 목록에 보인다
- [ ] 1일차에 올린 첨부파일이 열린다
- [ ] 새 민원을 등록하면 목록에 추가된다

!!! tip "데이터가 보이면 설계가 옳았다는 증명"
    Pod를 새로 만들었음에도 1일차 데이터가 그대로 보이는 것은,
    데이터 계층(DB)과 애플리케이션 계층(Pod)을 분리한 설계 덕분입니다.

---

## 4차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|---------|---------|
| ① | Secret이 생성되었다 | `kubectl get secrets` |
| ② | Deployment가 생성되었다 | `kubectl get deployments` |
| ③ | Pod가 `Running` 상태다 | `kubectl get pods` |
| ④ | Service의 EXTERNAL-IP가 생겼다 | `kubectl get services` |
| ⑤ | 브라우저에서 민원 서비스가 접속된다 | 브라우저 확인 |
| ⑥ | 1일차 민원 데이터가 보인다 | 민원 목록 확인 |

---

**다음 차시**: 일부러 Pod를 삭제해서 자동 복구를 관찰하고, 복제본을 3개로 늘려 수평 확장을 실습합니다.
