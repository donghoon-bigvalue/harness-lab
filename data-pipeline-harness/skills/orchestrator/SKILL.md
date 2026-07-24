---
name: orchestrator
description: "데이터 파이프라인 설계 팀(스키마 → ETL → 검증 → 모니터링 → 통합 리뷰)을 파이프라인 아키텍트가 계층적으로 위임·조율하여 실행 가능한 파이프라인 설계 패키지를 만든다. 데이터 파이프라인 설계·구축, 데이터 모델링/스키마 설계, ETL/ELT 로직, 데이터 검증·품질 규칙, 파이프라인 모니터링·관측성 설정 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — 이전 설계 수정, 부분 재설계, 스키마만 다시, ETL만 다시, 검증 규칙만 보강, 모니터링만 추가, 정합성 다시 검토, 업데이트, 개선, 다시 설계 요청 시에도 반드시 이 스킬을 사용할 것. 단순 개념 질문(예: 'ETL이 뭐야')은 직접 응답 가능."
---

# Data Pipeline Design Orchestrator

파이프라인 설계 팀을 조율하여 **요구사항 분해 → 스키마 설계 → ETL·검증 병렬 설계 → 모니터링 → 통합 정합성 검토 → 설계 패키지 통합**까지 한 번에 수행한다.

## 실행 모드: 에이전트 팀 (계층적 위임)

전 Phase에서 에이전트 팀 모드를 사용한다. 이 도메인의 핵심은 **계층적 위임**이다 — 아키텍트가 스키마를 계약으로 못 박고, 그 위에 ETL·검증을 병렬로, 모니터링을 그 뒤에 위임한다. 그리고 팀원 간 직접 통신이 품질의 동력이다: ETL이 "원천에 이 필드가 없다"고 하면 스키마 계약이 재검토되고, 검증이 "이 제약은 스키마에 있어야 한다"고 하면 카탈로그가 갱신되며, 모니터링이 "계측 훅이 없다"고 하면 ETL이 보강된다. 이 교환을 아키텍트가 일일이 중계하면 병목이 되고 계약의 미묘한 어긋남이 소실된다.

## 경로 규약

이 하네스는 플러그인으로 배포된다. **모든 산출물 경로는 하네스를 실행 중인 프로젝트의 루트 기준 상대 경로**이며, 플러그인이 어디에 설치되었는지와 무관하다. 작업 루트는 `data-pipeline/`다.

| 용도 | 경로 |
|------|------|
| 중간 산출물 | `data-pipeline/_workspace/` |
| 최종 산출물 | `data-pipeline/outputs/{YYYYMMDD}-{slug}/pipeline-design.md` |

에이전트 정의와 스킬은 플러그인이 제공하므로 **경로로 참조하지 않는다.** 에이전트는 `subagent_type`으로, 스킬은 Skill 툴의 스킬명으로 호출한다.

## 핵심 색인: 엔티티/필드 카탈로그

이 하네스의 모든 산출물은 스키마-디자이너가 발행하는 **엔티티/필드 카탈로그**를 색인으로 공유한다. 각 엔티티는 `E1, E2 …`, 각 필드는 `E1.amount`로 주소가 매겨진다. ETL은 타겟 필드를, 검증은 규칙 대상 필드를, 모니터링은 감시 대상 엔티티/규칙을 이 ID로 태깅한다. 통합 리뷰어는 이 ID를 유일한 기준축으로 네 산출물을 대조한다. **카탈로그 색인이 없으면 정합성 검증이 불가능하다** — 딥리서치의 Q번호와 같은 역할이다.

## 팀 구성

리더는 이 스킬을 실행하는 메인 세션이며, 파이프라인 아키텍트 역할을 수행한다. 시작 시 `data-pipeline-harness:pipeline-architect` 정의를 리드 원칙으로 적용한다 — 메인 세션이 리더이므로 이 에이전트를 별도로 띄우지 않는다.

| 팀원 (`subagent_type`) | 사용 스킬 | 출력 |
|------|----------|------|
| `data-pipeline-harness:schema-designer` | `data-pipeline-harness:schema-design` | `01_schema.md` |
| `data-pipeline-harness:etl-engineer` | `data-pipeline-harness:etl-logic` | `02_etl.md` |
| `data-pipeline-harness:validation-engineer` | `data-pipeline-harness:data-validation` | `03_validation.md` |
| `data-pipeline-harness:monitoring-engineer` | `data-pipeline-harness:monitoring-setup` | `04_monitoring.md` |
| `data-pipeline-harness:integration-reviewer` | `data-pipeline-harness:integration-review` | `05_review.md` |

**팀원 생성 방식:** 위 표의 `subagent_type`을 그대로 사용한다. 플러그인이 배포한 에이전트 정의가 자동 등록되므로, 정의 파일을 Read시키는 우회는 필요 없다 — 역할·원칙·통신 프로토콜이 시스템 프롬프트로 이미 주입된 상태로 기동한다. `model`은 전원 `opus`.

**프롬프트 필수 요소 (전 팀원 공통):** 에이전트 정의에는 역할만 있고 이번 실행의 경로·담당 엔티티는 없다. 팀원은 프로젝트 루트에서 실행되므로 다음이 빠지면 파일을 엉뚱한 위치에 쓰거나 엉뚱한 것을 설계한다.
1. **담당 엔티티 목록(E번호)과 이번 범위**
2. **입력 파일의 `data-pipeline/_workspace/...` 전체 경로**
3. **출력 파일의 `data-pipeline/_workspace/...` 전체 경로**

## 위임 계층 (Phase 순서의 근거)

스키마가 계약이므로 **먼저** 확정한다. ETL·검증은 둘 다 카탈로그를 소비하므로 병렬 가능하다. 모니터링은 ETL 스테이지·검증 규칙을 소비하므로 그 뒤다. 통합 리뷰는 넷을 대조하므로 맨 뒤다.

```
아키텍트 (스펙·계약)
    └─ 1차 위임 → schema-designer (카탈로그 = 계약)
            └─ 2차 위임(병렬) → etl-engineer + validation-engineer
                    └─ 3차 위임 → monitoring-engineer
                            └─ 검토 → integration-reviewer → (보강 루프) → 아키텍트 통합
```

## 워크플로우

### Phase 0: 컨텍스트 확인

`data-pipeline/_workspace/` 존재 여부로 실행 모드를 정한다.

| 상태 | 모드 | 행동 |
|------|------|------|
| 미존재 | **초기 실행** | Phase 1로 진행 |
| 존재 + 사용자가 부분 수정 요청 | **부분 재실행** | Phase 1 건너뛰고 아래 "부분 재실행" 절차 |
| 존재 + 새 파이프라인/새 요구 | **새 실행** | `data-pipeline/_workspace/`를 `data-pipeline/_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |

애매하면 사용자에게 묻는다. 기존 설계를 덮어쓰는 것은 되돌리기 어렵기 때문이다.

**부분 재실행 절차:**
1. 어떤 산출물이 대상인지 특정한다 (예: "검증 규칙이 얕다" → `03_validation.md`, validation-engineer / "E3 모니터링 추가" → monitoring-engineer)
2. 해당 팀원만 포함해 팀을 구성한다. **카탈로그(스키마)가 바뀌면 하류 전부가 영향받으므로**, 스키마 변경 시엔 ETL·검증·모니터링을 함께 소집한다. 그 외 국소 변경이면 담당 팀원 + integration-reviewer만 소집해 영향받는 경계면만 재검증한다
3. 팀원 프롬프트에 **이전 산출물 경로 + 사용자 피드백 원문 + 관련 카탈로그 필드 ID**를 그대로 포함한다. 요약하지 않는다 — 요약 과정에서 사용자가 지적한 뉘앙스가 사라진다
4. 변경이 정합성에 영향을 주면 integration-reviewer가 해당 경계면만 재대조
5. Phase 5로 진행해 최종 설계 패키지를 갱신한다

### Phase 1: 요구사항 분해 (아키텍트 단독 + 사용자 확인)

**실행 방식:** 파이프라인 아키텍트(메인 세션) 단독. 전문가를 아직 띄우지 않는다.

1. 사용자 입력에서 다음을 파악한다. 없으면 묻는다:
   - **원천 데이터** (필수) — 무엇을, 어떤 형태로(테이블/파일/스트림/API), 가능하면 샘플·스키마
   - **타겟 사용처** (필수) — 분석/운영/ML/리포팅 중 무엇, 조회 패턴 (정규화 정도를 가른다)
   - **처리 주기·SLA** — 배치/스트리밍, 신선도 요구, 정확도 요구 (없으면 표준 제안: 일 배치)
   - **기술 스택** — 웨어하우스/오케스트레이터/변환 도구 (없으면 스택-중립 설계 후 제안)
   - **데이터 규모** — 물리 설계·적재 방식을 가른다 (없으면 확인)
2. `data-pipeline/_workspace/` 생성
3. 아키텍트가 요구를 **파이프라인 스펙**으로 정리한다: 이번에 설계할 **엔티티 목록**(각각 원천·그레인 힌트·처리 주기 배정), 비기능 요구, 범위 경계, 미해결 결정을 `data-pipeline/_workspace/00_spec.md`에 기록 (사용자 요청 원문 포함).
4. **사용자에게 스펙(특히 설계할 엔티티 목록과 처리 주기)을 제시하고 승인받는다.** 이 하네스에서 사용자 확인은 여기 한 번뿐이다. 스키마 계약이 확정된 뒤 범위를 바꾸면 하류 전량 재작업이기 때문이다.

### Phase 2: 스키마 설계 (계약 확정)

**실행 방식:** 에이전트 팀 (schema-designer 단독 위임)

계약을 먼저 못 박는다. 이 단계가 끝나야 ETL·검증·모니터링이 참조할 색인이 생긴다.

1. 팀 생성, schema-designer 소집. 입력으로 `00_spec.md` 지정, 출력은 `01_schema.md`
2. TaskCreate: "설계할 엔티티를 E번호·필드 ID로 카탈로그화(그레인·타입·제약·물리) → `01_schema.md`"
3. 완료 조건: 모든 엔티티에 그레인이 확정되고, 모든 필드에 타입·널 허용·제약이 명시되고, E번호·필드 ID 색인이 부여됐을 것. 그레인이 비어 있거나 색인이 없으면 아키텍트가 반려한다 — 색인 없이는 하류 정합성 검증이 불가능하다
4. 아키텍트가 카탈로그를 검토하고 확정한다. 이후 카탈로그 변경은 반드시 팀 브로드캐스트를 거친다

### Phase 3: ETL·검증 병렬 설계

**실행 방식:** 에이전트 팀 (etl-engineer + validation-engineer 동시)

둘 다 카탈로그를 소비하므로 병렬로 위임한다.

1. 두 팀원 소집 (etl-engineer, validation-engineer), 입력으로 `00_spec.md` + `01_schema.md`(카탈로그) 지정
2. 전체 브리핑(`SendMessage to: "all"`): 카탈로그 경로, 담당 엔티티, "모든 산출물을 필드 ID로 태깅" 요청
3. TaskCreate: etl-engineer "카탈로그 타겟 필드를 채우는 로직 → `02_etl.md`", validation-engineer "카탈로그 제약을 검증 규칙으로 → `03_validation.md`"
4. **통신 규칙 — 이 Phase의 핵심 (아키텍트를 경유하지 않는다):**
   - etl-engineer가 원천으로 못 채우는 카탈로그 필드를 만나면 schema-designer에게 SendMessage로 계약 재검토를 요청한다 (필드 제거/널 허용/기본값)
   - validation-engineer가 카탈로그에 없어야 할/있어야 할 제약을 발견하면 schema-designer에게 직접 반영을 제안한다
   - etl-engineer가 데이터 손실·형변환(NULL→0 등) 지점을 만들면 validation-engineer에게 공유해 그 지점에 검증을 걸게 한다
   - 둘은 **같은 필드 ID로 산출물을 태깅**해야 한다. 이것이 통합 리뷰 정합성 검증의 유일한 정렬 축이다
5. **카탈로그 변경 발생 시:** schema-designer가 카탈로그를 고치면 팀 전체에 브로드캐스트하고, ETL·검증이 영향받는 필드를 따라 갱신한다. 아키텍트는 계약 변경이 스펙 범위를 벗어나는지만 감독한다

### Phase 4: 모니터링 설계

**실행 방식:** 에이전트 팀 (monitoring-engineer 합류, ETL·검증 대기)

1. monitoring-engineer 소집, 입력으로 `02_etl.md`(스테이지) + `03_validation.md`(규칙·심각도) + `00_spec.md`(SLA) + `01_schema.md`(핵심 엔티티) 지정
2. TaskCreate: "신선도·양·품질·지연·드리프트 지표 + SLO + 알림 라우팅 → `04_monitoring.md`"
3. **통신 규칙:** monitoring-engineer가 감시에 필요한 계측(스테이지 타임스탬프·행 수)이 ETL에 없으면 etl-engineer에게 직접 계측 추가를 요청한다. 검증 규칙 심각도(block/warn)와 알림 등급(page/notify)을 validation-engineer와 합의한다
4. 완료 조건: 핵심 엔티티(팩트·마트)마다 신선도·양 지표가 있고, 모든 block 규칙에 알림이 매핑됐을 것

### Phase 5: 통합 정합성 검토 및 보강 루프

**실행 방식:** 에이전트 팀 (integration-reviewer 합류, 전문가 대기)

1. integration-reviewer 소집, 입력으로 네 산출물 전체(`01`~`04`) + `00_spec.md` 지정, 기준축은 `01_schema.md` 카탈로그
2. TaskCreate: "경계면별 정합성 대조(스키마↔ETL↔검증↔모니터링) → `05_review.md`"
3. 검토 완료 → `05_review.md`의 **불일치/누락/위험 목록** 확인
4. **정합 / 경미** → Phase 6
5. **불일치/누락/위험 있음** → 보강 루프:
   - 아키텍트가 문제를 담당 전문가별로 묶는다 (예: "E2.status 미충족 → etl", "UNIQUE 제약 검증 없음 → validation", "E1 신선도 감시 없음 → monitoring")
   - 해당 전문가에게 SendMessage로 **보강 범위만** 전달한다. 전면 재설계가 아니라 지목된 필드 ID·규칙만 수정한다
   - 카탈로그 자체가 문제면 schema-designer가 고치고 하류 갱신을 브로드캐스트한다
   - integration-reviewer가 **보강된 경계면만** 재대조
   - **최대 2회.** 3회차 진입 시 남은 불일치를 `05_review.md`에 "미해결"로 확정하고 Phase 6으로 넘어간다. 완벽한 정합을 무한히 좇는 비용이 한계효용보다 크기 때문이다

### Phase 6: 설계 패키지 통합

**실행 방식:** 파이프라인 아키텍트(메인 세션) 단독

1. 아키텍트가 검증된 네 스펙을 하나의 **파이프라인 설계 패키지**로 통합한다 → `data-pipeline/outputs/{YYYYMMDD}-{slug}/pipeline-design.md`. 포함:
   - **개요·목표·범위** (스펙 요약)
   - **end-to-end 데이터 흐름** (원천 → 스테이징 → 변환 → 타겟, 스테이지·엔티티 표기)
   - **스키마** (카탈로그 + DDL, `01`에서)
   - **ETL 로직** (엔티티별 적재·변환, `02`에서)
   - **검증 규칙** (계층별 규칙·심각도, `03`에서)
   - **모니터링** (지표·SLO·알림, `04`에서)
   - **정합성·한계** (`05`의 확인 항목 + 미해결 항목 명시)
2. 아키텍트가 최종 패키지를 직접 확인한다:
   - 카탈로그의 모든 필드가 ETL로 채워지고 제약이 검증되는가
   - block 규칙이 전부 감시되는가
   - 미해결 불일치가 숨겨지지 않고 "한계"에 살아 있는가
   - 스펙 SLA가 모니터링 SLO로 커버되는가
3. 팀원에게 종료 알림 → `TeamDelete`
4. `data-pipeline/_workspace/`는 **삭제하지 않는다** (사후 검증·부분 재실행의 입력)
5. 사용자에게 요약 보고: 설계한 엔티티, 핵심 적재 방식, 검증 관문, 모니터링 SLO, 미해결 한계, 패키지 경로
6. 피드백 요청: "결과에서 개선할 부분이나 팀 구성에서 바꾸고 싶은 점이 있나요?"

## 데이터 흐름

```
사용자 입력
    ↓
[아키텍트] 요구 분해 → 00_spec.md (엔티티 목록·SLA·스택) → 사용자 승인
    ↓ 1차 위임
schema-designer → 01_schema.md (엔티티/필드 카탈로그 = 계약, E번호·필드 ID)
    ↓ 2차 위임(병렬, 카탈로그 소비)          ┌ SendMessage로 계약 재검토 ┐
 ┌──────────────────────┬──────────────────────┐               │
 ↓                      ↓                       ↑───────────────┘
etl-engineer          validation-engineer
02_etl.md             03_validation.md
(타겟 필드 채움)       (제약 → 규칙, 심각도)
 └──────────┬───────────┘
    ↓ 3차 위임 (스테이지·규칙 소비)
monitoring-engineer → 04_monitoring.md (지표·SLO·알림, 심각도 매핑)
    ↓ 검토 (카탈로그 기준축으로 대조)
integration-reviewer → 05_review.md (정합/불일치/누락/위험)
    ↓ 보강(최대 2회) ↺  담당 전문가 재소집
[아키텍트] 통합
    ↓
outputs/{date}-{slug}/pipeline-design.md
    ↓
[아키텍트: 최종 확인 + 사용자 보고]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 원천 스키마/샘플 부재 | schema-designer가 가정한 타입에 "원천 미확인" 표기 → validation-engineer가 형식 검증 강화. 지어내지 않는다 |
| ETL이 카탈로그 필드를 못 채움 | 계약 문제로 취급 → schema-designer에게 되돌려 필드 제거/널 허용/기본값 결정. 임의값으로 채우지 않는다 |
| 카탈로그 변경 발생 | schema-designer가 팀 브로드캐스트 → 영향받는 ETL·검증·모니터링만 갱신. 아키텍트는 스펙 범위 이탈만 감독 |
| 카탈로그 색인(E번호) 누락 | 아키텍트가 반려하고 재색인 요청 — 색인이 없으면 정합성 대조가 불가능하다 |
| block 규칙에 감시 없음 | 통합 리뷰가 "위험"으로 분류 → monitoring-engineer 보강 |
| SLA가 스택으로 달성 불가 | 아키텍트가 트레이드오프를 사용자에게 제시하고 스펙 조정 |
| 팀원 1명 실패 | SendMessage로 상태 확인 → 1회 재시작 → 재실패 시 해당 영역을 패키지에 "미설계"로 명시하고 진행 |
| integration-reviewer 실패 | 아키텍트가 `data-pipeline-harness:integration-review` 스킬의 체크리스트를 직접 수행 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 보강 루프 3회차 | 루프 종료. 남은 불일치를 패키지 "한계"에 기록 |
| 두 전문가 산출물이 근본 모순 | 삭제하지 않고 양측 병기, 아키텍트 결정에 남김 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "주문 로그(Postgres orders, order_items)를 분석 웨어하우스로 옮기는 파이프라인 설계해줘. 일 배치, 매출 대시보드용."
2. Phase 1 — 아키텍트가 스펙 정리: 설계 엔티티 E1 fct_order_item(그레인: 주문 품목 1건), E2 dim_customer, E3 mart_daily_sales, 일 배치, 신선도 SLA 07:00, 규모 일 500만 행. 사용자 승인
3. Phase 2 — schema-designer가 카탈로그 발행(E1~E3, 필드 ID·타입·제약·파티션), DDL 작성
4. Phase 3 — etl-engineer가 E1 증분 병합·E2 SCD·E3 집계 로직 작성(타겟 필드를 E-ID로 태깅), validation-engineer가 형식·무결성·비즈니스(금액≥0, 주문일≤배송일)·신선도 규칙 작성. ETL이 "원천에 discount 필드 없음" 제보 → schema-designer가 E1.discount를 널 허용으로 조정, 브로드캐스트
5. Phase 4 — monitoring-engineer가 E1·E3 신선도(≤07:00)·행수(±30%)·검증 실패율 지표, block 규칙→page 매핑 작성. ETL에 스테이지 타임스탬프 계측 요청
6. Phase 5 — integration-reviewer 대조: E2.segment 미충족(ETL 누락) 발견 → etl 보강 1회. block 규칙 전부 감시 확인
7. Phase 6 — `outputs/20260724-order-sales-pipeline/pipeline-design.md` 생성, end-to-end 흐름 + 네 스펙 통합, 한계에 "discount 원천 미확인" 명시
8. 예상: 스키마·ETL·검증·모니터링이 동일 필드 ID로 정합, 실행 가능한 설계 패키지 전달

### 에러 흐름 A — 원천 필드 부재
1. Phase 3에서 etl-engineer가 카탈로그 NOT NULL 필드 E1.channel을 원천으로 채울 수 없음을 발견
2. schema-designer에게 SendMessage → 계약 재검토: 원천에 정말 없으면 E1.channel을 널 허용 + 기본값 'unknown'으로, 또는 필드 제거
3. 변경을 팀 브로드캐스트 → validation-engineer가 해당 필드 NOT NULL 규칙 제거, monitoring 영향 없음
4. 임의 채널값을 지어내지 않음. 통합 리뷰가 정합 확인

### 에러 흐름 B — 보강 루프 한도 초과
1. Phase 5 1회차: 누락 3건 (E2.segment 미충족, UNIQUE 제약 검증 없음, E3 신선도 감시 없음)
2. 아키텍트가 etl·validation·monitoring에 보강 범위 전달
3. 2회차: E2.segment·신선도 해소, 그러나 UNIQUE 검증이 원천 중복으로 구조적 불가 판명(원천 자체에 중복 존재)
4. 3회차 진입 금지 → UNIQUE 정합 불가를 `05_review.md`에 "미해결"로 확정
5. Phase 6 진행, 패키지 "한계"에 "원천 중복으로 E2 UNIQUE 보장 불가, 적재 전 dedup 또는 원천 정제 필요" 명시, 사용자 보고 시 언급
