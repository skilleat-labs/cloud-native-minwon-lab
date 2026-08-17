# Day 2 · 3차시 — 컨테이너가 많아지면 누가 관리하지?

**소요 시간**: 50분 (13:00~13:50)
**목표**: Kubernetes의 구조를 이해하고, NKS 클러스터를 생성해 kubectl로 연결한다

---

## 이번 차시에 하는 것

| STEP | 내용 |
|------|------|
| 01 | NKS 클러스터 생성 |
| 02 | kubectl 설치 |
| 03 | kubeconfig 적용 |
| 04 | 클러스터 구성 요소 확인 |

---

## 개념 — 왜 Kubernetes가 필요한가

컨테이너가 여러 개가 되면 사람이 직접 관리해야 할 일이 폭발적으로 늘어납니다.

| 상황 | 사람이 해야 하는 일 |
|------|-----------------|
| 컨테이너가 죽었다 | 누군가 알아채고, 접속해서, 다시 실행해야 한다 |
| 접속자가 늘었다 | 노드에 여유가 있는지 확인하고 컨테이너를 더 띄워야 한다 |
| 노드가 죽었다 | 그 노드에 있던 컨테이너를 다른 노드에 다시 띄워야 한다 |
| 새 버전을 배포한다 | 하나씩 교체하면서 서비스가 끊기지 않게 조절해야 한다 |
| 트래픽을 나눠야 한다 | 새로 뜬 컨테이너 주소를 로드 밸런서에 등록해야 한다 |

!!! tip "Kubernetes는 이 모든 것을 자동으로 합니다"

---

## 개념 — 클러스터 구조

```
컨트롤 플레인 (Control Plane)
클러스터 관리 — 스케줄링, 스케일링, 배포 등 모든 활동 관리
        ↓
[노드 1] [노드 2] [노드 3]
실제 애플리케이션이 실행되는 서버 (= 어제의 App VM)
```

| 구성 요소 | 역할 | 1일차 대응 개념 |
|---------|------|--------------|
| 컨트롤 플레인 | 전체를 관리 — 무엇을 어디에 띄울지 결정 | 운영자의 판단 |
| 노드 | 컨테이너가 실제로 실행되는 서버 | App VM |
| Pod | 노드 위에서 실행되는 최소 배포 단위 | App VM 위의 프로세스 |

---

## 개념 — Pod / Deployment / Service

### Pod

- 컨테이너를 담는 **가장 작은 배포 단위**
- 언제든 사라질 수 있는 존재로 취급 — 고쳐 쓰지 않고 새로 만듦
- Pod마다 IP가 있지만, 재생성되면 주소가 바뀜

### Deployment

```
Deployment: "민원 서비스 이미지를 3개 유지하라"
        ↓
ReplicaSet: 부족하면 만들고, 넘치면 지운다
        ↓        ↓        ↓
      Pod 1    Pod 2    Pod 3
```

"몇 개가 있어야 한다"만 적으면 Kubernetes가 실제로 세고 맞춥니다.

### Service

```
민원 신청자
        ↓
Service (고정된 접근 지점 — Pod 주소가 바뀌어도 항상 같은 주소)
        ↓        ↓        ↓
      Pod 1    Pod 2    Pod 3
```

| 역할 | 1일차에서는 | 2일차에서는 |
|------|-----------|-----------|
| 단일 진입점 | Load Balancer | Kubernetes Service |
| 트래픽 분산 | LB 로드 밸런싱 | Service가 정상 Pod로 분배 |
| 대상 목록 갱신 | 멤버 수동 등록 | 라벨이 맞는 Pod를 자동 포함 |

---

## 개념 — NKS (관리형 Kubernetes)

| 관리 주체 | 담당 영역 |
|---------|---------|
| NHN Cloud | 컨트롤 플레인 (고가용성 보장, 설치·구성·운영) |
| 사용자 | 노드 (사양, 수), 서비스 (외부 노출), Pod (앱, 복제본 수) |

---

## STEP 01 — NKS 서비스 활성화 & 클러스터 생성

### 서비스 활성화

```
상단 메뉴 > 서비스 선택 > Containers > NKS > 서비스 활성화
```

### 클러스터 생성

```
Containers > NKS > 클러스터 생성
```

### 설정값

**클러스터 기본 설정**

| 항목 | 값 |
|------|---|
| 클러스터 이름 | `minwon-cluster` |
| Kubernetes 버전 | 최신 지원 버전 선택 |
| VPC | `minwon-vpc` |
| 서브넷 | `minwon-subnet-app` |
| API 엔드포인트 | Public |

**기본 노드 그룹 설정**

| 항목 | 값 |
|------|---|
| 이미지 | Ubuntu Server 22.04 LTS |
| 가용성 영역 | 한국(판교) |
| 인스턴스 타입 | `m2.c2m4` (2 vCPU, 4GB RAM) |
| 노드 수 | 2 |
| 키페어 | 1일차와 동일한 키페어 |
| 블록 스토리지 | HDD 20GB |

!!! info "클러스터 생성에는 약 10분이 소요됩니다"
    생성 버튼을 누른 뒤 상태가 `CREATE_COMPLETE`가 될 때까지 기다립니다.

!!! tip "노드는 결국 인스턴스"
    노드 그룹 설정은 1일차에서 배운 이미지, 인스턴스 타입, 키페어, 블록 스토리지 개념 그대로입니다.

---

## STEP 02 — kubectl 설치

클러스터를 조작하려면 `kubectl` 명령어 도구가 필요합니다.

**로컬 PC(Mac)**에서 설치합니다.

```bash
# Homebrew로 설치
brew install kubectl

# 설치 확인
kubectl version --client
```

**Windows**라면 공식 문서 참고: https://kubernetes.io/docs/tasks/tools/install-kubectl-windows/

---

## STEP 03 — kubeconfig 적용

kubeconfig는 클러스터에 접근하기 위한 인증 정보가 담긴 파일입니다.

### 콘솔에서 다운로드

```
Containers > NKS > [minwon-cluster]
→ 기본 정보 탭 > 설정 파일 다운로드 버튼 클릭
```

### 로컬에 적용

```bash
# 다운로드한 파일을 ~/.kube 디렉토리에 복사
mkdir -p ~/.kube
cp ~/Downloads/minwon-cluster-kubeconfig.yaml ~/.kube/config

# 또는 환경변수로 지정
export KUBECONFIG=~/Downloads/minwon-cluster-kubeconfig.yaml
```

### 연결 확인

```bash
kubectl cluster-info
# Kubernetes control plane is running at https://...
```

---

## STEP 04 — 클러스터 구성 요소 확인

```bash
# 노드 목록
kubectl get nodes
# NAME         STATUS   ROLES    AGE
# node-xxxxx   Ready    <none>   5m
# node-yyyyy   Ready    <none>   5m

# 기본 Pod 목록 (시스템 Pod)
kubectl get pods -A

# Deployment 목록
kubectl get deployments

# Service 목록
kubectl get services
```

`kubectl get nodes` 에서 모든 노드가 `Ready` 상태이면 준비 완료입니다.

---

## 3차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|---------|---------|
| ① | NKS 클러스터가 `CREATE_COMPLETE` 상태다 | 콘솔 > NKS 목록 |
| ② | kubectl이 설치되었다 | `kubectl version --client` |
| ③ | kubeconfig가 적용되었다 | `kubectl cluster-info` |
| ④ | 노드가 `Ready` 상태다 | `kubectl get nodes` |

---

## 핵심 개념 정리

| 용어 | 한 문장 정의 |
|------|-----------|
| Cluster | Kubernetes가 관리하는 전체 묶음 |
| Control Plane | 무엇을 어디에 띄울지 결정하고 상태를 유지 |
| Node | 실제로 컨테이너가 실행되는 서버 |
| Pod | 컨테이너를 담는 가장 작은 배포 단위 |
| Deployment | 몇 개를 어떤 이미지로 유지할지 선언 |
| Service | 변하지 않는 접근 지점, 정상 Pod로 분산 |

---

**다음 차시**: 1일차 DB와 Object Storage를 연결해 Pod로 민원 서비스를 배포합니다.
