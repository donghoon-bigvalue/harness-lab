---
name: orchestrator
description: "종합 코드 리뷰 에이전트 팀(아키텍처·보안·성능·스타일 4축 병렬 감사 → 검증·트리아지 → 리포트 통합)을 리뷰 리드가 조율하여 심각도로 우선순위를 매긴 하나의 리뷰 리포트를 만든다. 코드 리뷰, 코드 감사, 종합 리뷰, 이 코드/PR/브랜치/변경분 리뷰해줘, 아키텍처·보안·성능·스타일 점검, 취약점/병목/구조 검토 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — 리뷰 다시, 부분 재감사, 보안만 다시, 성능 발견 보강, 검증 다시, 리포트만 다시 써줘, 업데이트, 개선 요청 시에도 반드시 이 스킬을 사용할 것. 특정 함수 한 줄에 대한 단순 질문은 직접 응답 가능."
---

# Code Review Orchestrator

리뷰 팀을 조율하여 **범위 설정 → 아키텍처·보안·성능·스타일 4축 병렬 감사 → 검증·트리아지 → 통합 리포트**까지 한 번에 수행한다.

## 실행 모드: 에이전트 팀

전 Phase에서 에이전트 팀 모드를 사용한다. 팀원 간 직접 통신이 통합 품질의 핵심 동력이기 때문이다 — 보안이 찾은 무제한 입력이 성능의 DoS 후보가 되고, 아키텍처가 지목한 결합이 다른 축 발견의 근본 원인이 되며, 네 축이 같은 코드를 각자 렌즈로 본 뒤 검증관이 교차로 묶어야 "네 개의 린터 출력"이 아닌 통합 리뷰가 성립한다. 이 교환을 리드가 일일이 중계하면 병목이 되고 교차 신호가 손실된다.

## 경로 규약

이 하네스는 플러그인으로 배포된다. **모든 산출물 경로는 하네스를 실행 중인 프로젝트의 루트 기준 상대 경로**이며, 플러그인이 어디에 설치되었는지와 무관하다. 작업 루트는 `code-review/`다.

| 용도 | 경로 |
|------|------|
| 중간 산출물 | `code-review/_workspace/` |
| 최종 산출물 | `code-review/outputs/{YYYYMMDD}-{slug}/code-review-report.md` |

에이전트 정의와 스킬은 플러그인이 제공하므로 **경로로 참조하지 않는다.** 에이전트는 `subagent_type`으로, 스킬은 Skill 툴의 스킬명으로 호출한다.

**리뷰는 코드를 고치지 않는다.** 이 하네스의 산출물은 리포트다. 사용자가 명시적으로 수정을 요청하지 않는 한 대상 코드를 변경하지 않는다.

## 팀 구성

리더는 이 스킬을 실행하는 메인 세션이며, 리뷰 리드 역할을 수행한다. 시작 시 `code-review-harness:review-lead` 정의를 리드 원칙으로 적용한다 — 메인 세션이 리더이므로 이 에이전트를 별도로 띄우지 않는다.

| 팀원 (`subagent_type`) | 사용 스킬 | 출력 |
|------|----------|------|
| `code-review-harness:architecture-auditor` | `code-review-harness:architecture-audit` | `01_architecture_findings.md` |
| `code-review-harness:security-auditor` | `code-review-harness:security-audit` | `02_security_findings.md` |
| `code-review-harness:performance-auditor` | `code-review-harness:performance-audit` | `03_performance_findings.md` |
| `code-review-harness:style-auditor` | `code-review-harness:style-audit` | `04_style_findings.md` |
| `code-review-harness:finding-verifier` | `code-review-harness:finding-verification` | `05_verification.md` |
| `code-review-harness:report-integrator` | `code-review-harness:report-integration` | `outputs/.../code-review-report.md` |

**팀원 생성 방식:** 위 표의 `subagent_type`을 그대로 사용한다. 플러그인이 배포한 에이전트 정의가 자동 등록되므로, 정의 파일을 Read시키는 우회는 필요 없다 — 역할·원칙·통신 프로토콜이 시스템 프롬프트로 이미 주입된 상태로 기동한다. `model`은 전원 `opus`.

**프롬프트 필수 요소 (전 팀원 공통):** 에이전트 정의에는 역할만 있고 이번 실행의 대상·심각도 기준은 없다. 팀원은 프로젝트 루트에서 실행되므로 다음이 빠지면 엉뚱한 파일을 감사하거나 산출물을 엉뚱한 위치에 쓴다.
1. **리뷰 대상 파일 목록**(또는 diff/브랜치 지정)과 각자 축의 초점
2. **공통 심각도 기준** (`00_scope.md`에 정의)
3. **입력 파일의 `code-review/_workspace/...` 전체 경로**
4. **출력 파일의 `code-review/_workspace/...` 전체 경로**

## 심각도 기준 (팀 공통)

리드가 `00_scope.md`에 배포하고 네 감사원이 공유한다. 검증관이 이 잣대로 정규화한다.

| 심각도 | 정의 |
|--------|------|
| **Critical** | 즉시·조건 없이 악용/장애 가능 — 원격 코드 실행, 인증 우회, 데이터 유실, 운영 다운, 하드코딩된 운영 비밀 |
| **High** | 실제 피해 경로가 있으나 조건부 — 권한 상승, 사용자 체감 성능 저하, 심각한 구조 결합, 확장 시 무너지는 병목 |
| **Medium** | 특정 상황에서 문제 — 경계 조건 버그, 확장성 제약, 취약한 추상화, 완화 가능한 취약점 |
| **Low** | 위생 문제 — 국소 비효율, 가독성, 관례 위반 |
| **Info** | 개선 제안 — 리팩터 기회, 관측성, 예방적 강화 |

심각도는 **악용/장애 경로 존재 × 조건의 현실성 × 영향 범위**로 판정한다. 네 축 모두 같은 잣대를 쓴다.

## 워크플로우

### Phase 0: 컨텍스트 확인

`code-review/_workspace/` 존재 여부로 실행 모드를 정한다.

| 상태 | 모드 | 행동 |
|------|------|------|
| 미존재 | **초기 실행** | Phase 1로 진행 |
| 존재 + 사용자가 부분 수정 요청 | **부분 재실행** | Phase 1 건너뛰고 아래 "부분 재실행" 절차 |
| 존재 + 새 대상/새 입력 | **새 실행** | `code-review/_workspace/`를 `code-review/_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |

애매하면 사용자에게 묻는다. 기존 리뷰를 덮어쓰는 것은 되돌리기 어렵기 때문이다.

**부분 재실행 절차:**
1. 어떤 산출물이 대상인지 특정한다 (예: "보안이 얕다" → `02_security_findings.md`, security-auditor / "리포트 요약이 길다" → report-integrator)
2. 해당 팀원만 포함해 팀을 구성한다. 감사 내용이 바뀌면 finding-verifier를 함께 소집해 영향받는 발견만 재검증한다
3. 팀원 프롬프트에 **이전 산출물 경로 + 사용자 피드백 원문**을 그대로 포함한다. 요약하지 않는다 — 사용자가 지적한 뉘앙스가 사라진다
4. 감사/검증이 바뀌면 report-integrator로 영향받는 섹션만 리포트를 갱신한다
5. Phase 5로 진행해 최종 리포트를 갱신한다

### Phase 1: 범위 설정 (리드 단독 + 사용자 확인)

**실행 방식:** 리뷰 리드(메인 세션) 단독. 감사원을 아직 띄우지 않는다.

1. 사용자 입력에서 다음을 파악한다. 없으면 묻는다:
   - **리뷰 대상** (필수) — 커밋 안 된 변경(`git diff`)? main 대비 브랜치 전체? 특정 PR? 특정 모듈·디렉토리? 리포지토리 전체? 대상이 모호하면 반드시 확인한다. 잘못된 대상으로 4축을 돌리면 전량 재작업이다.
   - **중점 축 / 제외 범위** (없으면 4축 전부) — 예: "보안 위주로", "스타일은 생략"
   - **깊이 기대치 / 프로젝트 관례 문서** (없으면 표준)
2. `code-review/_workspace/` 생성
3. 리드가 대상 파일 목록을 확정하고(대형이면 위험도 높은 영역 우선), 심각도 기준과 축별 초점을 `code-review/_workspace/00_scope.md`에 기록 (사용자 요청 원문 + 대상 파일 목록 포함).
4. **대상이 크거나 모호하면 사용자에게 대상 파일 목록·범위를 제시하고 승인받는다.** 명백한 소규모 diff면 생략 가능. 이 하네스에서 범위 확인은 사후 재작업을 막는 유일한 관문이다.

### Phase 2: 병렬 4축 감사

**실행 방식:** 에이전트 팀 (architecture + security + performance + style 동시)

1. 팀 생성 (감사원 4인):
   ```
   TeamCreate(
     team_name: "code-review-team",
     members: [
       { name: "architecture-auditor",
         agent_type: "code-review-harness:architecture-auditor", model: "opus",
         prompt: "리뷰 대상: {대상 파일 목록/ diff}. 심각도 기준: 00_scope.md.
                  축 초점: 구조·결합·경계. 출력: code-review/_workspace/01_architecture_findings.md" },
       { name: "security-auditor",
         agent_type: "code-review-harness:security-auditor", model: "opus",
         prompt: "리뷰 대상: {...}. 출력: code-review/_workspace/02_security_findings.md" },
       { name: "performance-auditor",
         agent_type: "code-review-harness:performance-auditor", model: "opus",
         prompt: "리뷰 대상: {...}. 출력: code-review/_workspace/03_performance_findings.md" },
       { name: "style-auditor",
         agent_type: "code-review-harness:style-auditor", model: "opus",
         prompt: "리뷰 대상: {...}. 출력: code-review/_workspace/04_style_findings.md" }
     ]
   )
   ```
2. 전체 브리핑 (`SendMessage to: "all"`): 대상 파일 목록, 심각도 기준, 각자 축 초점, `00_scope.md` 경로, 발견 레코드 형식(축별 ID) 준수 요청
3. TaskCreate: 각 감사원에게 "담당 축으로 대상 전체 감사" 작업 등록
4. **통신 규칙 — 이 Phase의 핵심 (리드를 경유하지 않는다):**
   - security-auditor가 무제한 입력·자원 소비를 만나면 performance-auditor에게 DoS 후보로 공유한다
   - architecture-auditor가 경계 붕괴·god object를 지목하면 security·performance에게 근본 원인 후보로 공유한다
   - style-auditor가 삼켜진 예외를 만나면 관련 축 감사원에게 버그 은폐 가능성으로 넘긴다
   - 네 감사원은 **축별 ID(ARCH-/SEC-/PERF-/STYLE-)로 발견을 태깅**하고 **위치(파일:줄)를 명시**해야 한다. 이것이 다음 Phase 대조·중복 병합의 정렬 축이다
5. 리드는 네 산출물이 완료될 때까지 개입하지 않는다. 조기 개입은 병렬성을 죽인다. 단, 감사원이 "범위를 뒤집는 발견"(대상 밖 공통 모듈의 Critical)을 보고하면 즉시 범위 확대 여부를 판단한다

### Phase 3: 검증·트리아지 및 보강 루프

**실행 방식:** 에이전트 팀 (finding-verifier 합류, 감사원 대기)

1. finding-verifier 소집, 입력으로 `00_scope.md` + `01~04_findings.md` 전체 지정
2. TaskCreate: "발견 대조 → 확인/오탐/중복/교차/미결 분류 + 심각도 정규화 → `05_verification.md`"
3. 검증 완료 → `05_verification.md`의 **검증 공백/미결 목록** 확인
4. **공백 없음 / 경미** → Phase 4
5. **미결/미해결 상충 있음** → 보강 루프:
   - 리드가 미결을 담당 축별로 묶는다 (예: "SEC-3 완화 미확인 → security", "PERF-2 실측 필요 → performance")
   - 해당 감사원에게 SendMessage로 **보강 범위만** 전달한다. 전면 재감사가 아니라 지목된 발견만 심화한다
   - 감사원이 해당 findings 파일의 그 섹션을 갱신
   - finding-verifier가 **보강된 부분만** 재검증
   - **최대 2회.** 3회차 진입 시 남은 미결을 `05_verification.md`에 "미해결"로 확정하고 Phase 4로 넘어간다. 완벽한 판정을 무한히 좇는 비용이 한계효용보다 크기 때문이다

### Phase 4: 리포트 통합

**실행 방식:** 에이전트 팀 (report-integrator 합류)

1. 리드가 통합 방향 브리프를 `code-review/_workspace/06_integration_brief.md`에 작성 (무엇을 최상단에 놓을지, 리포트 초점·독자)
2. report-integrator 소집, 입력으로 `05_verification.md`(주 입력) + `00_scope.md` + `06_integration_brief.md` 지정, 출력은 최종 경로 지정
3. TaskCreate: "심각도 순 통합 리포트 작성 → `code-review/outputs/{YYYYMMDD}-{slug}/code-review-report.md`"
4. **통신 규칙:** report-integrator가 분류·심각도가 모호한 발견을 만나면 finding-verifier에게 직접 질의한다. 리포트로 답할 수 없는 발견은 리드에게 보고해 "한계"로 명시할지 결정받는다
5. 완료 조건: 리포트에 실행 요약·심각도별 발견·교차 발견·권장 수정 순서·한계 섹션이 모두 채워져 있을 것. 오탐으로 걸러진 것은 부록에 남아 있을 것

### Phase 5: 통합 및 정리

1. 리드가 최종 리포트를 직접 확인한다:
   - '미결'·'추정' 발견이 단정적 어조로 쓰이지 않았는가
   - 오탐이 본문에 남아 있지 않고 부록으로 갔는가
   - 교차 발견이 단일 축에 묻히지 않고 부각됐는가
   - 미감사 축·범위 축소·실측 불가가 "한계"에 명시됐는가
   - 심각도 순으로 배열되어 실행 요약만 읽어도 우선순위가 보이는가
2. 팀원에게 종료 알림 → `TeamDelete`
3. `code-review/_workspace/`는 **삭제하지 않는다** (사후 검증·부분 재실행의 입력)
4. 사용자에게 요약 보고: 심각도별 발견 총계, 가장 시급한 발견, 교차 발견, 가장 큰 미결/한계, 리포트 경로
5. 피드백 요청: "결과에서 개선할 부분이나 팀 구성에서 바꾸고 싶은 점이 있나요?"

## 데이터 흐름

```
사용자 입력
    ↓
[리드] 대상·심각도 기준 확정 → 00_scope.md → (대형이면 사용자 승인)
    ↓ 브리핑(all)
 ┌────────────┬────────────┬────────────┬────────────┐
 ↓            ↓            ↓            ↓          (SendMessage로 교차 공유)
architecture  security     performance  style
01_arch_...   02_sec_...   03_perf_...  04_style_...
 └────────────┴────────────┴────────────┴────────────┘
    ↓ (축별 ID·위치로 정렬)
finding-verifier → 05_verification.md (확인/오탐/중복/교차/미결 + 심각도 정규화)
    ↓ 미결 보강(최대 2회) ↺  담당 감사원 재소집
[리드] 통합 방향 → 06_integration_brief.md
    ↓
report-integrator ←SendMessage→ finding-verifier (분류 재확인)
    ↓
outputs/{date}-{slug}/code-review-report.md
    ↓
[리드: 최종 확인 + 사용자 보고]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 리뷰 대상 모호 | 감사원 소집 전 사용자에게 대상(diff/브랜치/모듈/전체) 확인. 잘못된 대상은 전량 재작업 |
| 대상이 너무 큼 | 위험도 높은 영역(진입점·인증·데이터 접근·외부 입력) 우선, 나머지는 후속 리뷰로 명시 |
| 감사원 1명 실패 | SendMessage로 상태 확인 → 1회 재시작 → 재실패 시 해당 축을 리포트에 "미감사"로 명시하고 진행 |
| 감사원이 축 ID/위치 태깅 누락 | 리드가 반려하고 재태깅 요청 — 태깅이 없으면 대조·중복 병합이 불가능하다 |
| 보안 발견의 완화 확인 불가 | 오탐/확인으로 몰지 않고 '미결'로. 검증관이 보강 대상으로 처리 |
| 성능 발견이 실측 없는 추정 | 확신도 '추정' 유지, 리포트 "한계"에 "실측 필요" 명시 |
| finding-verifier 실패 | 리드가 `code-review-harness:finding-verification` 스킬의 분류 절차를 직접 수행 |
| 확인된 발견 0건 | "심각도 있는 발견 없음"을 정직한 결론으로. 커버리지·한계 명시로 "안 나옴"과 "안 봄" 구분 |
| 발견 간 상충(같은 코드 정반대 판단) | 삭제하지 않고 양측 근거 병기, 리포트에 판정 근거와 함께 |
| 보강 루프 3회차 | 루프 종료, 남은 미결을 리포트 "한계"에 기록 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "이 PR 변경분 종합적으로 리뷰해줘"
2. Phase 1 — 리드가 `git diff`로 대상 파일 목록 확정, 심각도 기준·축별 초점을 `00_scope.md`에 기록
3. Phase 2 — architecture(결합·경계)·security(악용경로)·performance(병목)·style(관례) 병렬 감사, 축별 ID·위치로 태깅. security가 "무제한 페이지 크기 파라미터"를 performance에 DoS 후보로 공유
4. Phase 3 — finding-verifier 분류: SEC-2와 PERF-4가 같은 코드(무제한 입력) → 교차 발견으로 병합(Critical), STYLE-1은 완화된 관례라 오탐 처리, PERF-2는 실측 없어 미결 → performance 보강 1회
5. Phase 4 — report-integrator가 심각도 순 리포트 작성, 교차 발견을 별도 부각, 오탐을 부록에, 실측 미확인을 한계에
6. Phase 5 — `outputs/20260724-pr-payment-refactor/code-review-report.md` 생성, 요약 보고(Critical 1·High 2·Medium 3, 교차 발견 1)
7. 예상: 확인된 발견이 심각도 순으로, 오탐·미결과 구분되어 전달됨

### 에러 흐름 A — 한 축 감사 실패
1. Phase 2에서 style-auditor가 도중 실패
2. 리드가 SendMessage로 상태 확인 → 1회 재시작 → 재실패
3. finding-verifier가 스타일 축 없이 나머지 3축만 검증, 스타일을 "미감사"로 표기
4. report-integrator가 리포트 한계에 "스타일 축 미감사" 명시
5. 없는 스타일 발견을 지어내지 않음

### 에러 흐름 B — 보강 루프 한도 초과
1. Phase 3 1회차: 미결 3건 (SEC-3 완화 미확인, PERF-2 실측 필요, ARCH-5 맥락 부족)
2. 리드가 security·performance·architecture에 보강 범위 전달
3. 2회차: ARCH-5 확인으로 승격, SEC-3 여전히 완화 미확인, PERF-2 실측 여전히 불가
4. 3회차 진입 금지 → SEC-3·PERF-2를 `05_verification.md`에 "미해결"로 확정
5. Phase 4~5 진행, 리포트 "한계"에 잔존 미결 명시, 사용자 보고 시 언급
