# Day 2 · 6차시 — 최종 실습 미션 & 자원 정리

**시간**: 16:00 ~ 17:00 (1시간)  
**목표**: 2일간 배운 내용을 미션으로 정리하고, 실습 자원을 안전하게 삭제한다

---

## 최종 실습 미션

> 2일 동안 만든 민원 서비스를 돌아보며, 스스로 점검하고 설명할 수 있는지 확인합니다.

### 미션 1 — 내 서비스 동작 최종 확인

브라우저에서 민원 서비스에 접속해 아래 항목을 모두 확인하세요.

| 확인 항목 | 1일차 방식 | 2일차 방식 |
|---------|-----------|-----------|
| 민원 등록 화면 접속 | LB 플로팅 IP | Kubernetes Service EXTERNAL-IP |
| 새 민원 등록 후 목록 확인 | ✓ | ✓ |
| 1일차에 올린 첨부파일 열기 | ✓ | ✓ (Object Storage 그대로) |
| DB 데이터가 유지되고 있는지 | ✓ | ✓ (DB VM 그대로) |

```bash
# 현재 서비스 상태 최종 확인
kubectl get pods
kubectl get deployments
kubectl get svc
```

### 미션 2 — 내 아키텍처 설명하기 (옆 사람에게)

아래 두 문장을 완성해 옆 사람에게 설명해보세요.

```
1일차에 만든 구조에서,
민원 신청자의 요청은 [ ] → [ ] → [ ] → [ ] 순서로 흘러간다.

2일차에서 App VM을 Kubernetes로 바꾼 이유는
[ ] 때문이다. Kubernetes는 [ ] 을/를 자동으로 해준다.
```

### 미션 3 — 장애 시나리오 점검

아래 상황이 발생하면 어떻게 대응하는지 생각해보세요.

| 장애 상황 | 1일차 (VM) 대응 | 2일차 (K8s) 대응 |
|---------|--------------|----------------|
| App 서버가 갑자기 중단 | 콘솔 접속 → 수동 재시작 | 자동 복구 (조정 루프) |
| 민원 접수가 폭증 | VM 추가 → LB 수동 등록 | `replicas` 값만 변경 |
| 새 버전 배포 필요 | 서버 접속 → 코드 교체 → 재시작 | 이미지 태그 변경 → 순차 교체 |

---

## 자원 정리

!!! danger "과금 주의"
    NHN Cloud는 자원이 존재하는 것만으로도 과금됩니다.  
    실습이 끝나면 반드시 아래 순서대로 정리하세요.

!!! warning "삭제 순서가 중요합니다"
    의존 관계가 있는 자원은 순서를 지켜 삭제해야 합니다.  
    순서를 어기면 삭제가 실패하거나 자원이 남을 수 있습니다.

### 삭제 순서 1 — Kubernetes 자원

```bash
# 1. 배포된 앱 삭제
kubectl delete deployment complaint-app

# 2. 서비스 삭제
kubectl delete svc complaint-svc

# 3. ConfigMap / Secret 삭제 (있을 경우)
kubectl delete configmap complaint-config
kubectl delete secret complaint-secret
```

### 삭제 순서 2 — NKS 클러스터

```
콘솔 > Container > NHN Kubernetes Service(NKS)
  → 내 클러스터 선택 → 삭제
```

!!! info "NKS 삭제 시간"
    클러스터 삭제는 5~10분 소요됩니다. 삭제가 완료된 후 다음 단계를 진행하세요.

### 삭제 순서 3 — NCR 레지스트리

```
콘솔 > Containers > NHN Container Registry(NCR)
  → 이미지 먼저 삭제 → 레지스트리 삭제
```

### 삭제 순서 4 — VM 및 1일차 자원

| 자원 | 콘솔 경로 | 주의사항 |
|------|---------|---------|
| App VM | Compute > Instance > 삭제 | NKS 삭제 후 진행 |
| DB VM | Compute > Instance > 삭제 | 데이터 백업 필요 시 스냅샷 먼저 |
| Block Storage | Storage > Block Storage > 삭제 | VM 분리 후 삭제 |
| Object Storage | Storage > Object Storage > 컨테이너 삭제 | 파일 먼저 전체 삭제 후 컨테이너 삭제 |
| Load Balancer | Network > Load Balancer > 삭제 | |
| 플로팅 IP | Network > Floating IP > 삭제 | LB에서 해제 후 삭제 |
| 보안 그룹 | Network > Security Group > 삭제 | VM에서 해제 후 삭제 |
| VPC / 서브넷 | Network > VPC > 삭제 | 모든 자원 정리 후 마지막에 |

### 삭제 순서 5 — 프로젝트 삭제 (선택)

```
콘솔 홈 > 내 프로젝트 선택 > 프로젝트 삭제
```

!!! tip "프로젝트 삭제 = 내부 자원 일괄 삭제"
    프로젝트를 삭제하면 내부의 모든 자원이 함께 삭제됩니다.
    단, Object Storage 파일처럼 별도 삭제가 필요한 자원이 남아있으면 프로젝트 삭제가 거부될 수 있습니다.

---

## 마무리 — 2일간의 여정을 돌아보며

### 우리가 만든 것

```
Day 1                              Day 2
  │                                  │
  ▼                                  ▼
인터넷 → 플로팅IP → LB          인터넷 → K8s Service
         → App VM                         → Pod 1
         → DB VM + Block Storage          → Pod 2   → DB VM + Block Storage
         → Object Storage                → Pod 3   → Object Storage

"손으로 하나하나 만들었다"         "선언해 두면 시스템이 유지한다"
```

### 핵심 정리

| 배운 것 | 한 줄 요약 |
|--------|----------|
| 클라우드 기본 자원 | VPC·보안그룹·VM·스토리지는 온프레미스의 네트워크·서버·디스크와 같은 역할 |
| 2-Tier 아키텍처 | App과 DB를 분리하면 보안·확장성·가용성이 모두 좋아진다 |
| 컨테이너 | 앱과 실행환경을 묶어 어디서든 동일하게 실행 |
| Kubernetes | "원하는 상태"를 선언하면 시스템이 그 상태를 유지 |
| 자동 복구 | 사람이 감시하지 않아도 장애를 감지하고 복구 |
| 수평 확장 | 트래픽 증가 시 숫자 하나로 서버를 늘릴 수 있음 |

---

---

!!! success "수고하셨습니다"
    2일 동안 민원 서비스를 VM에서 Kubernetes까지 직접 만들어보셨습니다.  
    오늘 배운 구조와 개념이 실제 운영 환경에서 도움이 되길 바랍니다.
