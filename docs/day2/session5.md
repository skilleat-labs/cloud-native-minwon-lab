# Day 2 · 5차시 — 민원 폭주와 장애에 대응하라

**소요 시간**: 50분 (15:00~15:50)
**목표**: Pod 자동 복구를 직접 관찰하고, 복제본을 늘려 수평 확장을 실습한다

---

## 이번 차시에 하는 것

| STEP | 내용 |
|------|------|
| 01 | 현재 상태 확인 |
| 02 | Pod 삭제 → 자동 복구 관찰 |
| 03 | 복제본 3개로 수평 확장 |
| 04 | 서비스 정상 동작 최종 확인 |

---

## 개념 — 어제였다면

App VM에서 서비스가 죽으면:

1. Load Balancer 헬스체크 실패
2. 해당 서버 트래픽 제외
3. 남은 서버가 없으면 서비스 중단
4. **누군가 알아채고 서버에 접속해 다시 실행해야 함**
5. 복구 시간 = "사람이 얼마나 빨리 알아채는가"

---

## 개념 — 오늘은 (Pod 자동 복구)

Pod가 죽으면 Kubernetes의 조정 루프가 작동합니다.

```
① 원하는 상태 (replicas: 3)
        ↓
② 현재 상태 관찰 (실제 2개만 실행 중)
        ↓
③ 차이 감지 → 새 Pod 자동 생성
        ↓
④ 준비 완료 → Service 대상에 자동 포함
↑_________________________________↑ (끊임없이 반복)
```

| 단계 | 1일차 (사람이 한다) | 2일차 (시스템이 한다) |
|------|-----------------|------------------|
| 장애 감지 | 모니터링, 연락에 걸리는 시간 | 조정 루프가 즉시 감지 |
| 복구 작업 | 접속, 원인 파악, 재실행 | 새 Pod 자동 생성 |
| 서비스 상태 | 남은 서버 없으면 중단 | 나머지 Pod가 계속 처리 |

---

## STEP 01 — 현재 상태 확인

```bash
# Pod 목록 확인
kubectl get pods
# NAME                             READY   STATUS    RESTARTS
# complaint-app-7d4b9c8f6-xxxxx   1/1     Running   0

# 현재 복제본 수 확인
kubectl get deployments
# NAME            READY   UP-TO-DATE   AVAILABLE
# complaint-app   1/1     1            1

# Service 상태 확인
kubectl get services
```

브라우저에서 서비스가 정상 동작하는지 확인합니다.

```
http://<EXTERNAL-IP>
```

---

## STEP 02 — Pod 삭제 → 자동 복구 관찰

### Pod 이름 확인 후 삭제

```bash
# Pod 이름 확인
kubectl get pods

# Pod 삭제 (장애 상황 재현)
kubectl delete pod <Pod-이름>
# pod "complaint-app-7d4b9c8f6-xxxxx" deleted
```

### 자동 복구 관찰

```bash
# 즉시 확인 — 새 Pod가 생성되는 과정 관찰
kubectl get pods
# NAME                             READY   STATUS              RESTARTS
# complaint-app-7d4b9c8f6-yyyyy   0/1     ContainerCreating   0   ← 새로 만들어지는 중

# 잠시 후 다시 확인
kubectl get pods
# NAME                             READY   STATUS    RESTARTS
# complaint-app-7d4b9c8f6-yyyyy   1/1     Running   0          ← 복구 완료
```

!!! tip "관찰 포인트"
    - 삭제한 Pod와 새로 생긴 Pod의 **이름이 다릅니다** — "고쳐 쓴 것"이 아니라 "새로 만든 것"
    - 복구되는 동안에도 서비스가 끊기지 않습니다 (Pod가 1개라 잠깐 끊길 수 있음 — 다음 STEP에서 해결)

---

## STEP 03 — 복제본 3개로 수평 확장

### 방법 1: 명령어로 즉시 변경

```bash
kubectl scale deployment complaint-app --replicas=3
```

### 방법 2: YAML 수정 후 적용

```bash
# deployment.yaml에서 replicas 값 변경
# replicas: 1 → replicas: 3
kubectl apply -f app/deployment.yaml
```

### 확장 결과 확인

```bash
kubectl get pods
# NAME                             READY   STATUS    RESTARTS
# complaint-app-7d4b9c8f6-aaaa   1/1     Running   0
# complaint-app-7d4b9c8f6-bbbb   1/1     Running   0
# complaint-app-7d4b9c8f6-cccc   1/1     Running   0

kubectl get deployments
# NAME            READY   UP-TO-DATE   AVAILABLE
# complaint-app   3/3     3            3
```

### 확장 후 다시 Pod 삭제해보기

```bash
kubectl delete pod <Pod-이름-하나>

# 즉시 확인
kubectl get pods
# 3개 중 하나가 Terminating이고, 새 Pod가 생성 중
# 나머지 2개는 계속 서비스 처리 중 → 서비스 끊기지 않음
```

!!! tip "1일차와의 결정적 차이"
    1일차: App VM을 늘리면 Load Balancer에 **멤버를 수동 등록**해야 했습니다.
    오늘: replicas를 늘리면 새 Pod가 **라벨만 맞으면 자동으로** Service 대상에 포함됩니다.

---

## STEP 04 — 서비스 정상 동작 최종 확인

```
http://<EXTERNAL-IP>
```

확인 항목:

- [ ] 민원 서비스 메인 화면이 표시된다
- [ ] 1일차에 등록한 민원 데이터가 그대로 보인다
- [ ] 1일차에 올린 첨부파일이 열린다
- [ ] Pod를 3개로 늘렸어도 데이터는 하나로 보인다
- [ ] 새 민원을 등록하면 목록에 추가된다

---

## 5차시 체크포인트

| # | 확인 항목 | 확인 방법 |
|---|---------|---------|
| ① | Pod 삭제 후 새 Pod가 자동 생성되었다 | `kubectl get pods` |
| ② | 삭제한 Pod와 새 Pod의 이름이 다르다 | Pod 이름 비교 |
| ③ | 복제본이 3개로 늘었다 | `kubectl get deployments` |
| ④ | Pod 3개가 모두 `Running` 상태다 | `kubectl get pods` |
| ⑤ | 어느 Pod가 처리해도 같은 데이터가 보인다 | 브라우저 확인 |
| ⑥ | 1일차 첨부파일이 그대로 남아 있다 | Object Storage 확인 |

---

## 2일차 최종 비교 — VM vs Kubernetes

| 운영 작업 | 1일차 (사람이 한다) | 2일차 (시스템이 한다) |
|---------|-----------------|------------------|
| 서비스가 죽었는지 확인 | 사람이 감시 | 조정 루프가 감지 |
| 죽은 서비스 재실행 | 사람이 접속해서 실행 | 자동으로 새 Pod 생성 |
| 서버를 늘린다 | 인스턴스 생성 후 설치 | replicas 값 변경 |
| 늘어난 서버를 트래픽 대상에 넣는다 | LB에 멤버 수동 등록 | 라벨로 자동 포함 |
| 새 버전을 배포한다 | 서버마다 파일 교체 | 새 이미지로 순차 교체 |

!!! info "자동화는 운영자를 없애지 않습니다"
    "서버를 살리는 일"에서 "어떤 상태가 되어야 하는지 정의하고, 버전과 자원과 보안을 관리하는 일"로 이동할 뿐입니다.

---

## 2일차 미션 완료 — 두 문장으로 정리

> **1일차:** 클라우드에서 서비스를 연다는 것은, 길과 문을 만들고 그 위에 서버와 저장소를 배치하는 일이다.

> **2일차:** 클라우드 네이티브란, 원하는 상태를 선언해 두고 시스템이 그 상태를 유지하게 만드는 일이다.

---

!!! warning "실습 후 자원 정리"
    사용하지 않는 자원도 과금됩니다. 실습이 끝나면 강사 안내에 따라 정리해 주세요.

    | 자원 | 정리 방법 |
    |------|---------|
    | NKS 클러스터 | 콘솔 > NKS > 클러스터 삭제 |
    | App VM | 콘솔 > Compute > Instance > 삭제 |
    | DB VM | 강사 안내에 따라 (데이터 보존 여부 확인) |
    | NCR 레지스트리 | 콘솔 > NCR > 레지스트리 삭제 |
