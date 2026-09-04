# 온라인 민원 서비스로 배우는 클라우드 & 클라우드 네이티브

NHN Cloud를 활용해 온라인 민원 서비스를 직접 구축하며, 클라우드 인프라의 핵심 개념을 익히는 실습 과정입니다.

## 과정 정보

| 구분 | 내용 |
|------|------|
| 대상 | 공공기관 클라우드 운영자 |
| 일정 | 2일 과정 / 일 7시간 (10:00~17:00) |
| 방식 | 이론 + 콘솔 실습 + 시나리오 미션 |
| 실습 환경 | NHN Cloud 콘솔 (개인 실습 계정) |

## 실습 가이드 목차

```mermaid
flowchart LR
    S1["🔑 1차시\n콘솔 로그인"]
    S2["📐 2차시\n인프라 계획"]
    S3["🌐 3차시\n네트워크 & LB"]
    S4["🖥️ 4차시\nVM & Block Storage"]
    S5["🚀 5차시\n서비스 자동 배포"]
    S6["📦 6차시\nObject Storage"]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6

    style S1 fill:#e8f4fd,stroke:#2196F3
    style S2 fill:#e8f4fd,stroke:#2196F3
    style S3 fill:#e8f4fd,stroke:#2196F3
    style S4 fill:#e8f4fd,stroke:#2196F3
    style S5 fill:#e8f4fd,stroke:#2196F3
    style S6 fill:#e8f4fd,stroke:#2196F3
```

| 일차 | 차시 | 주제 |
|------|------|------|
| Day 1 | 1차시 | [콘솔에 로그인하자](day1/session1.md) |
| Day 1 | 2차시 | [어디에 올릴지 그려보자](day1/session2.md) |
| Day 1 | 3차시 | [네트워크 & 보안 그룹 & LB 구성](day1/session3.md) |
| Day 1 | 4차시 | [VM 생성 & Block Storage 연결](day1/session4.md) |
| Day 1 | 5차시 | [서비스 자동 배포 & LB 등록](day1/session5.md) |
| Day 1 | 6차시 | [Object Storage & 저장소 분리](day1/session6.md) |

## 1일차 최종 아키텍처

```mermaid
flowchart TB
    USER["👤 민원 신청자\n(인터넷)"]

    subgraph PUBLIC["🌍 공인 영역"]
        FIP["🌐 플로팅 IP\n공인 IP"]
    end

    subgraph VPC["🏢 VPC — 192.168.0.0/16"]
        subgraph SUBNET_APP["📡 App 서브넷 (192.168.10.x)"]
            LB["⚖️ Load Balancer\n단일 진입점 · 헬스체크"]
            APP["🖥️ App VM\n민원 서비스 앱 · :8080"]
        end
        subgraph SUBNET_DB["🔒 DB 서브넷 (192.168.20.x)"]
            DB["🗄️ DB VM\nMySQL · :3306"]
        end
        subgraph STORAGE["💾 스토리지"]
            BS["📀 Block Storage\nDB 데이터"]
            OS["📦 Object Storage\n첨부파일"]
        end
    end

    USER -->|"HTTP"| FIP
    FIP --> LB
    LB -->|":8080"| APP
    APP -->|":3306"| DB
    APP -->|"REST API"| OS
    DB --- BS

    style PUBLIC fill:#fff9e6,stroke:#f0ad4e
    style VPC fill:#f0f7ff,stroke:#2196F3
    style SUBNET_APP fill:#e8f4fd,stroke:#90caf9
    style SUBNET_DB fill:#fce4ec,stroke:#ef9a9a
    style STORAGE fill:#e8f5e9,stroke:#a5d6a7
    style LB fill:#d4edda,stroke:#28a745
    style OS fill:#e8f5e9,stroke:#4caf50
    style BS fill:#e8f5e9,stroke:#4caf50
```

## 실습 원칙

```mermaid
flowchart LR
    subgraph DO["🙋 직접 만드는 것"]
        D1["VPC · 서브넷"]
        D2["보안 그룹"]
        D3["Load Balancer"]
        D4["VM (App · DB)"]
        D5["Block Storage"]
        D6["Object Storage"]
    end
    subgraph GIVEN["📦 제공되는 것"]
        G1["민원 서비스 앱"]
        G2["DB 설치 스크립트"]
        G3["배포 자동화 스크립트"]
    end

    style DO fill:#e8f4fd,stroke:#2196F3
    style GIVEN fill:#e8f5e9,stroke:#4caf50
```

!!! warning "주의"
    1일차에 만든 DB VM, Block Storage, Object Storage는 2일차에도 사용합니다. 임의로 삭제하지 마세요.
