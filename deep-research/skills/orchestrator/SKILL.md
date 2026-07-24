---
name: orchestrator
description: "딥 리서치 에이전트 팀(웹·학술·커뮤니티 조사 → 교차 검증 → 종합)을 리서치 리드가 조율하여 신뢰도를 매긴 리서치 보고서를 만든다. 어떤 주제든 깊이 조사, 리서치, 딥리서치, 여러 각도에서 알아봐줘, 자료 조사, 종합 보고서, 팩트체크, 사실 확인, 무엇에 대해 조사·정리해줘 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — 이전 조사 수정, 부분 재조사, 커뮤니티 반응만 다시, 학술 근거만 보강, 검증 다시, 보고서만 다시 써줘, 업데이트, 개선, 다시 조사 요청 시에도 반드시 이 스킬을 사용할 것. 단순 사실 한 줄 질문은 직접 응답 가능."
---

# Deep Research Orchestrator

리서치 팀을 조율하여 **범위 설정 → 웹·학술·커뮤니티 병렬 조사 → 교차 검증 → 종합 보고서**까지 한 번에 수행한다.

## 실행 모드: 에이전트 팀

전 Phase에서 에이전트 팀 모드를 사용한다. 팀원 간 직접 통신이 품질의 핵심 동력이기 때문이다 — 웹이 발견한 공식 발표가 학술 검증 대상이 되고, 커뮤니티가 포착한 간극이 즉시 다른 각도의 재조사를 부르며, 세 각도가 같은 주장을 두고 수렴/발산해야 삼각측량이 성립한다. 이 교환을 리드가 일일이 중계하면 병목이 되고 신호가 손실된다.

## 경로 규약

이 하네스는 플러그인으로 배포된다. **모든 산출물 경로는 하네스를 실행 중인 프로젝트의 루트 기준 상대 경로**이며, 플러그인이 어디에 설치되었는지와 무관하다. 작업 루트는 `research/`다.

| 용도 | 경로 |
|------|------|
| 중간 산출물 | `research/_workspace/` |
| 최종 산출물 | `research/outputs/{YYYYMMDD}-{slug}/research-report.md` |

에이전트 정의와 스킬은 플러그인이 제공하므로 **경로로 참조하지 않는다.** 에이전트는 `subagent_type`으로, 스킬은 Skill 툴의 스킬명으로 호출한다.

## 팀 구성

리더는 이 스킬을 실행하는 메인 세션이며, 리서치 리드 역할을 수행한다. 시작 시 `deep-research:research-lead` 정의를 리드 원칙으로 적용한다 — 메인 세션이 리더이므로 이 에이전트를 별도로 띄우지 않는다.

| 팀원 (`subagent_type`) | 사용 스킬 | 출력 |
|------|----------|------|
| `deep-research:web-researcher` | `deep-research:web-research` | `01_web_findings.md` |
| `deep-research:academic-researcher` | `deep-research:academic-research` | `02_academic_findings.md` |
| `deep-research:community-researcher` | `deep-research:community-research` | `03_community_findings.md` |
| `deep-research:cross-validator` | `deep-research:cross-validation` | `04_validation.md` |
| `deep-research:synthesis-writer` | `deep-research:synthesis-report` | `outputs/.../research-report.md` |

**팀원 생성 방식:** 위 표의 `subagent_type`을 그대로 사용한다. 플러그인이 배포한 에이전트 정의가 자동 등록되므로, 정의 파일을 Read시키는 우회는 필요 없다 — 역할·원칙·통신 프로토콜이 시스템 프롬프트로 이미 주입된 상태로 기동한다. `model`은 전원 `opus`.

**프롬프트 필수 요소 (전 팀원 공통):** 에이전트 정의에는 역할만 있고 이번 실행의 경로·하위 질문은 없다. 팀원은 프로젝트 루트에서 실행되므로 다음이 빠지면 파일을 엉뚱한 위치에 쓰거나 엉뚱한 것을 조사한다.
1. **하위 질문 목록(Q번호)과 각자 주도할 질문**
2. **입력 파일의 `research/_workspace/...` 전체 경로**
3. **출력 파일의 `research/_workspace/...` 전체 경로**

## 워크플로우

### Phase 0: 컨텍스트 확인

`research/_workspace/` 존재 여부로 실행 모드를 정한다.

| 상태 | 모드 | 행동 |
|------|------|------|
| 미존재 | **초기 실행** | Phase 1로 진행 |
| 존재 + 사용자가 부분 수정 요청 | **부분 재실행** | Phase 1 건너뛰고 아래 "부분 재실행" 절차 |
| 존재 + 새 주제/새 입력 | **새 실행** | `research/_workspace/`를 `research/_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |

애매하면 사용자에게 묻는다. 기존 조사를 덮어쓰는 것은 되돌리기 어렵기 때문이다.

**부분 재실행 절차:**
1. 어떤 산출물이 대상인지 특정한다 (예: "커뮤니티 반응이 얕다" → `03_community_findings.md`, community-researcher / "보고서 요약이 길다" → synthesis-writer)
2. 해당 팀원만 포함해 팀을 구성한다. 조사 내용이 바뀌면 cross-validator를 함께 소집해 영향받는 하위 질문만 재검증한다
3. 팀원 프롬프트에 **이전 산출물 경로 + 사용자 피드백 원문**을 그대로 포함한다. 요약하지 않는다 — 요약 과정에서 사용자가 지적한 뉘앙스가 사라진다
4. 조사/검증이 바뀌면 synthesis-writer로 영향받는 섹션만 보고서를 갱신한다
5. Phase 5로 진행해 최종 보고서를 갱신한다

### Phase 1: 범위 설정 (리드 단독 + 사용자 확인)

**실행 방식:** 리서치 리드(메인 세션) 단독. 조사원을 아직 띄우지 않는다.

1. 사용자 입력에서 다음을 파악한다. 없으면 묻는다:
   - **조사 주제** (필수)
   - **범위 제한 / 관점 / 목적** (없으면 조사 후 제안) — 예: 시점 범위, 지역, "찬반 양쪽" 요청 등
   - **깊이/분량 기대치** (없으면 표준: 하위 질문 3~6개)
2. `research/_workspace/` 생성
3. 리드가 주제를 **하위 질문 3~6개(Q1~Qn)**로 분해한다. 각 질문에 "어떤 증거가 있으면 답이 되는가"와 "어느 각도가 주도하는가"를 적어 `research/_workspace/00_scope.md`에 기록 (사용자 요청 원문 포함).
4. **사용자에게 하위 질문 목록을 제시하고 승인받는다.** 이 하네스에서 사용자 확인은 여기 한 번뿐이다. 조사가 끝난 뒤 질문을 바꾸면 전량 재작업이기 때문이다. 사용자가 질문을 더하거나 빼면 반영한다.

### Phase 2: 병렬 다각도 조사

**실행 방식:** 에이전트 팀 (web + academic + community 동시)

1. 팀 생성 (조사원 3인):
   ```
   TeamCreate(
     team_name: "deep-research-team",
     members: [
       { name: "web-researcher",
         agent_type: "deep-research:web-researcher", model: "opus",
         prompt: "하위 질문: {Q1~Qn 원문 + 각자 주도할 Q}.
                  출력: research/_workspace/01_web_findings.md" },
       { name: "academic-researcher",
         agent_type: "deep-research:academic-researcher", model: "opus",
         prompt: "하위 질문: {...}. 출력: research/_workspace/02_academic_findings.md" },
       { name: "community-researcher",
         agent_type: "deep-research:community-researcher", model: "opus",
         prompt: "하위 질문: {...}. 출력: research/_workspace/03_community_findings.md" }
     ]
   )
   ```
2. 전체 브리핑 (`SendMessage to: "all"`): 하위 질문 목록, 각자 주도 질문, `00_scope.md` 경로, 주장 레코드 형식 준수 요청
3. TaskCreate: 각 조사원에게 "담당 각도로 전 하위 질문 조사" 작업 등록
4. **통신 규칙 — 이 Phase의 핵심 (리드를 경유하지 않는다):**
   - web-researcher가 논문·연구를 언급한 자료를 만나면 academic-researcher에게 SendMessage로 원문 검증을 요청한다
   - community-researcher가 공식/학술 서사와 어긋나는 신호를 포착하면 web·academic에게 직접 공유해 교차 확인을 청한다
   - 세 조사원은 **같은 Q번호로 주장을 태깅**해야 한다. 이것이 다음 Phase 삼각측량의 유일한 정렬 축이다
5. 리드는 세 산출물이 완료될 때까지 개입하지 않는다. 조기 개입은 병렬성을 죽인다. 단, 조사원이 "주제 전제를 뒤집는 발견"을 보고하면 즉시 하위 질문 재설계를 검토한다

### Phase 3: 교차 검증 및 보강 루프

**실행 방식:** 에이전트 팀 (cross-validator 합류, 조사원 대기)

1. cross-validator 소집, 입력으로 `00_scope.md` + `01/02/03_findings.md` 전체 지정
2. TaskCreate: "Q번호별 삼각측량 → `04_validation.md`"
3. 검증 완료 → `04_validation.md`의 **조사 공백/상충 목록** 확인
4. **공백 없음 / 경미** → Phase 4
5. **공백/미해결 상충 있음** → 보강 루프:
   - 리드가 공백을 담당 각도별로 묶는다 (예: "Q3 학술 근거 전무 → academic", "Q5 상충 → web 1차 자료")
   - 해당 조사원에게 SendMessage로 **보강 범위만** 전달한다. 전면 재조사가 아니라 지목된 Q·각도만 심화한다
   - 조사원이 해당 findings 파일의 그 섹션을 갱신
   - cross-validator가 **보강된 부분만** 재검증 (영향받는 Q번호만)
   - **최대 2회.** 3회차 진입 시 남은 공백을 `04_validation.md`에 "미해결"로 확정하고 Phase 4로 넘어간다. 완벽한 근거를 무한히 좇는 비용이 한계효용보다 크기 때문이다

### Phase 4: 종합 보고서 작성

**실행 방식:** 에이전트 팀 (synthesis-writer 합류)

1. 리드가 종합 방향 브리프를 `research/_workspace/05_synthesis_brief.md`에 작성 (무엇을 확립/논쟁/미확인 층위로 놓을지, 보고서의 초점)
2. synthesis-writer 소집, 입력으로 `00_scope.md` + `04_validation.md`(주 입력) + `05_synthesis_brief.md` 지정, 출력은 최종 경로 지정
3. TaskCreate: "신뢰도 층위 보고서 작성 → `research/outputs/{YYYYMMDD}-{slug}/research-report.md`"
4. **통신 규칙:** synthesis-writer가 검증 분류가 모호한 주장을 만나면 cross-validator에게 직접 질의한다. 보고서로 답할 수 없는 하위 질문이 있으면 리드에게 보고해 "한계"로 명시할지 결정받는다
5. 완료 조건: 보고서에 TL;DR·확립된 사실·논쟁 지점·한계 섹션이 모두 채워져 있을 것. 상충이 있는데 "논쟁 지점"이 비어 있으면 리드가 반려한다

### Phase 5: 통합 및 정리

1. 리드가 최종 보고서를 직접 확인한다:
   - 확증되지 않은 주장이 단정적 어조로 쓰이지 않았는가
   - 상충이 숨겨지지 않고 살아 있는가
   - 폴백 모드였던 각도가 "한계"에 명시됐는가
   - 모든 핵심 진술에 근거가 붙어 있는가
2. 팀원에게 종료 알림 → `TeamDelete`
3. `research/_workspace/`는 **삭제하지 않는다** (사후 검증·부분 재실행의 입력)
4. 사용자에게 요약 보고: 확립된 핵심 사실, 주요 논쟁, 가장 큰 공백/한계, 보고서 경로
5. 피드백 요청: "결과에서 개선할 부분이나 팀 구성에서 바꾸고 싶은 점이 있나요?"

## 데이터 흐름

```
사용자 입력
    ↓
[리드] 하위 질문 분해 → 00_scope.md → 사용자 승인
    ↓ 브리핑(all)
 ┌──────────────┬───────────────┬────────────────┐
 ↓              ↓               ↓                (SendMessage로 상호 교차 확인)
web-researcher  academic-researcher  community-researcher
01_web_...      02_academic_...      03_community_...
 └──────────────┴───────────────┴────────────────┘
    ↓ (Q번호로 정렬)
cross-validator → 04_validation.md (확증/상충/단일출처/미확인 + 공백)
    ↓ 공백 보강(최대 2회) ↺  담당 조사원 재소집
[리드] 종합 방향 → 05_synthesis_brief.md
    ↓
synthesis-writer ←SendMessage→ cross-validator (분류 재확인)
    ↓
outputs/{date}-{slug}/research-report.md
    ↓
[리드: 최종 확인 + 사용자 보고]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 조사원 1명 웹 검색 불가 | 해당 각도 폴백 모드 선언 → findings 상단 명시 → cross-validator가 그 각도 신뢰강도를 낮춰 반영. 수치를 지어내지 않는다 |
| 한 각도의 근거 전무 (예: 학술 연구 없음) | "근거 없음"을 발견으로 기록. cross-validator가 나머지 각도 주장을 단일출처 이하로 분류 |
| 세 각도가 전부 상충 | 삭제하지 않고 전 출처 병기, `04_validation.md`에 '논쟁'으로. synthesis-writer가 양측 제시 |
| 조사원이 Q번호 태깅 누락 | 리드가 반려하고 재태깅 요청 — 태깅이 없으면 삼각측량이 불가능하다 |
| 팀원 1명 실패 | SendMessage로 상태 확인 → 1회 재시작 → 재실패 시 해당 각도를 보고서에 "미조사"로 명시하고 진행 |
| cross-validator 실패 | 리드가 `deep-research:cross-validation` 스킬의 삼각측량 절차를 직접 수행 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 보강 루프 3회차 | 루프 종료. 남은 공백을 보고서 "한계"에 기록 |
| 산출물 간 상충 데이터 | 삭제하지 않고 출처 병기 |
| 주제가 조사 불가(사적/순수 예측/가치판단) | 리드가 조사 가능/불가 부분을 분리, 불가 부분은 보고서에서 "조사 범위 밖"으로 명시 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "원격근무가 생산성에 실제로 어떤 영향을 주는지 여러 각도에서 조사해줘"
2. Phase 1 — 리드가 하위 질문 5개 분해(Q1 측정된 생산성 변화, Q2 직군별 차이, Q3 기업 공식 입장, Q4 근로자 체감, Q5 장기 효과 근거 유무), 사용자 승인
3. Phase 2 — web(기업 발표·통계)·academic(생산성 연구·메타분석)·community(재택 근로자 스레드) 병렬 조사, 같은 Q번호로 태깅, community가 "공식은 생산성↑라는데 현장은 번아웃 호소" 간극을 web·academic에 공유
4. Phase 3 — cross-validator 삼각측량: Q1 일부 확증(연구+통계 수렴), Q4 커뮤니티 단일출처, Q5 학술 근거 공백 발견 → academic 보강 1회
5. Phase 4 — synthesis-writer가 확립/논쟁/미확인 층위 보고서 작성, "생산성 측정 방식에 따라 결과가 갈림"을 논쟁 섹션으로 살림
6. Phase 5 — `outputs/20260724-remote-work-productivity/research-report.md` 생성, 한계에 "Q5 장기 효과는 검증된 근거 부족" 명시
7. 예상: 확증·상충·공백이 신뢰등급과 함께 구분되어 전달됨

### 에러 흐름 A — 한 각도 검색 불가
1. Phase 2에서 community-researcher의 커뮤니티 접근이 3회 무의미한 결과 반환
2. 커뮤니티 각도 폴백 선언, `03_community_findings.md` 상단에 "조사 모드: 제한적" 명시
3. cross-validator가 커뮤니티 근거 없는 상태로 web·academic만 삼각측량 → 현장 체감 관련 주장은 "단일출처/미확인"으로 분류
4. synthesis-writer가 보고서 한계에 "커뮤니티 각도 제한적, 현장 체감은 검증 부족" 명시
5. 없는 여론을 지어내지 않음

### 에러 흐름 B — 보강 루프 한도 초과
1. Phase 3 1회차: 공백 3건 (Q2 학술 근거 없음, Q5 상충 미해결, Q3 단일출처)
2. 리드가 academic·web에 보강 범위 전달
3. 2회차: Q3 확증으로 승격, Q2 여전히 학술 근거 없음, Q5 상충 잔존 + 보강 자료가 새 상충 유발
4. 3회차 진입 금지 → Q2·Q5를 `04_validation.md`에 "미해결"로 확정
5. Phase 4~5 진행, 보고서 "한계"와 "논쟁 지점"에 잔존 항목 명시, 사용자 보고 시 언급
