---
name: orchestrator
description: "마케팅 캠페인 에이전트 팀(타겟 시장 조사 → 카피·비주얼 병렬 창작 → A/B 테스트 계획, 품질 리뷰어의 반복 검수 동반)을 캠페인 리드가 조율해 실행 가능한 캠페인 패키지를 만든다. 마케팅 캠페인 기획·제작, 광고 캠페인, 타겟 조사, 광고 카피, 비주얼 컨셉, A/B 테스트 계획, 프로모션·런칭 캠페인, 캠페인 패키지 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — 캠페인 수정, 카피만 다시, 비주얼만 다시, 타겟 바꿔서 다시, 테스트 계획만 다시, 리뷰 한 번 더, 업데이트, 개선, 재실행 요청 시에도 반드시 이 스킬을 사용할 것. 단순 마케팅 질문(용어·개념)은 직접 응답 가능."
---

# Marketing Campaign Orchestrator

캠페인 팀을 조율하여 **포지셔닝 설정 → 타겟 시장 조사 → 카피·비주얼 병렬 창작 → A/B 테스트 계획 → 반복 정합성 검수**까지 한 번에 수행하고, 실행 가능한 캠페인 패키지를 산출한다.

## 실행 모드: 에이전트 팀 (품질 리뷰어 상주)

전 Phase에서 에이전트 팀 모드를 사용한다. 팀원 간 직접 통신이 품질의 핵심 동력이기 때문이다 — 조사가 발견한 타겟 언어가 카피로 바로 흐르고, 카피와 비주얼이 같은 기둥을 강화하도록 서로 맞추며, quality-reviewer가 각 산출물이 나오는 즉시 정합성을 검수해 상류에서 균열을 잡는다. 이 교환을 리드가 일일이 중계하면 병목이 되고 신호가 손실된다.

**품질 리뷰어는 최종 게이트가 아니라 상주 검수자다.** 조사가 끝나면 조사를, 카피가 나오면 카피를, 비주얼이 나오면 카피와의 정합을 바로 본다(점진 검수). 잘못된 조사 위에 쌓은 카피·비주얼을 전량 되돌리는 것보다, 상류에서 잡는 편이 싸기 때문이다.

## 경로 규약

이 하네스는 플러그인으로 배포된다. **모든 산출물 경로는 하네스를 실행 중인 프로젝트의 루트 기준 상대 경로**이며, 플러그인이 어디에 설치되었는지와 무관하다. 작업 루트는 `marketing/`다.

| 용도 | 경로 |
|------|------|
| 중간 산출물 | `marketing/_workspace/` |
| 최종 산출물 | `marketing/outputs/{YYYYMMDD}-{slug}/campaign-package.md` |

에이전트 정의와 스킬은 플러그인이 제공하므로 **경로로 참조하지 않는다.** 에이전트는 `subagent_type`으로, 스킬은 Skill 툴의 스킬명으로 호출한다.

## 팀 구성

리더는 이 스킬을 실행하는 메인 세션이며, 캠페인 리드 역할을 수행한다. 시작 시 `marketing-campaign-harness:campaign-lead` 정의를 리드 원칙으로 적용한다 — 메인 세션이 리더이므로 이 에이전트를 별도로 띄우지 않는다.

| 팀원 (`subagent_type`) | 사용 스킬 | 출력 |
|------|----------|------|
| `marketing-campaign-harness:market-researcher` | `marketing-campaign-harness:market-research` | `01_market_research.md` |
| `marketing-campaign-harness:copywriter` | `marketing-campaign-harness:ad-copywriting` | `02_ad_copy.md` |
| `marketing-campaign-harness:visual-concept-designer` | `marketing-campaign-harness:visual-concept-design` | `03_visual_concept.md` |
| `marketing-campaign-harness:ab-test-planner` | `marketing-campaign-harness:ab-test-planning` | `04_ab_test_plan.md` |
| `marketing-campaign-harness:quality-reviewer` | `marketing-campaign-harness:campaign-review` | `05_review.md` |

**팀원 생성 방식:** 위 표의 `subagent_type`을 그대로 사용한다. 플러그인이 배포한 에이전트 정의가 자동 등록되므로, 정의 파일을 Read시키는 우회는 필요 없다 — 역할·원칙·통신 프로토콜이 시스템 프롬프트로 이미 주입된 상태로 기동한다. `model`은 전원 `opus`.

**프롬프트 필수 요소 (전 팀원 공통):** 에이전트 정의에는 역할만 있고 이번 실행의 경로·스파인은 없다. 팀원은 프로젝트 루트에서 실행되므로 다음이 빠지면 파일을 엉뚱한 위치에 쓰거나 엉뚱한 것을 만든다.
1. **포지셔닝 스파인(세그먼트 S#·메시지 기둥 P#)과 담당 범위**
2. **입력 파일의 `marketing/_workspace/...` 전체 경로**
3. **출력 파일의 `marketing/_workspace/...` 전체 경로**

## 워크플로우

### Phase 0: 컨텍스트 확인

`marketing/_workspace/` 존재 여부로 실행 모드를 정한다.

| 상태 | 모드 | 행동 |
|------|------|------|
| 미존재 | **초기 실행** | Phase 1로 진행 |
| 존재 + 사용자가 부분 수정 요청 | **부분 재실행** | Phase 1 건너뛰고 아래 "부분 재실행" 절차 |
| 존재 + 새 캠페인/새 입력 | **새 실행** | `marketing/_workspace/`를 `marketing/_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 Phase 1 |

애매하면 사용자에게 묻는다. 기존 캠페인을 덮어쓰는 것은 되돌리기 어렵기 때문이다.

**부분 재실행 절차:**
1. 어떤 산출물이 대상인지 특정한다 (예: "카피만 다시" → `02_ad_copy.md`, copywriter / "타겟을 B2B로" → 스파인 수정 후 하류 전체 / "테스트 계획만" → ab-test-planner)
2. 해당 팀원만 포함해 팀을 구성한다. 창작 내용이 바뀌면 quality-reviewer를 함께 소집해 영향받는 부분만 재검수한다
3. 팀원 프롬프트에 **이전 산출물 경로 + 사용자 피드백 원문**을 그대로 포함한다. 요약하지 않는다 — 요약 과정에서 사용자가 지적한 뉘앙스가 사라진다
4. 창작·검수가 바뀌면 Phase 6으로 진행해 패키지의 영향받는 섹션만 갱신한다

### Phase 1: 포지셔닝 설정 (리드 단독 + 사용자 확인)

**실행 방식:** 캠페인 리드(메인 세션) 단독. 팀원을 아직 띄우지 않는다.

1. 사용자 입력에서 다음을 파악한다. 없으면 묻는다:
   - **제품/오퍼와 캠페인 목표** (필수 — 무엇을, 왜 알리는가, 무엇이 성공인가)
   - **타겟 / 채널 / 예산·기간 / 브랜드 톤** (없으면 조사 후 제안하거나 표준 가정)
2. `marketing/_workspace/` 생성
3. 리드가 브리프를 **포지셔닝 스파인**으로 분해해 `marketing/_workspace/00_brief.md`에 기록:
   - **세그먼트 S1~Sn** (JTBD 기반 가설)
   - **메시지 기둥 P1~Pm** (3개 이하 권장, 각 기둥은 조사로 검증될 가설)
   - 오퍼, 채널, 성공 지표, 가드레일(금지 표현·브랜드 톤·규제 주의), 사용자 요청 원문
4. **사용자에게 포지셔닝 스파인(세그먼트·기둥·성공 지표)을 제시하고 승인받는다.** 이 하네스에서 사용자 확인은 여기 한 번뿐이다. 창작이 끝난 뒤 축을 바꾸면 전량 재작업이기 때문이다. 사용자가 세그먼트·기둥을 더하거나 빼면 반영한다.

### Phase 2: 타겟 시장 조사 (조사 → 스파인 검증)

**실행 방식:** 에이전트 팀 (market-researcher + quality-reviewer 상주)

1. 팀 생성. market-researcher와 quality-reviewer를 소집한다:
   ```
   TeamCreate(
     team_name: "marketing-campaign-team",
     members: [
       { name: "market-researcher",
         agent_type: "marketing-campaign-harness:market-researcher", model: "opus",
         prompt: "포지셔닝 스파인: {S1~Sn, P1~Pm 원문}. 이 세그먼트·기둥 가설을 근거로 검증/교정하라.
                  입력: marketing/_workspace/00_brief.md
                  출력: marketing/_workspace/01_market_research.md" },
       { name: "quality-reviewer",
         agent_type: "marketing-campaign-harness:quality-reviewer", model: "opus",
         prompt: "스파인: {…}. 각 산출물을 완성 즉시 점진 검수하라.
                  출력(누적): marketing/_workspace/05_review.md" }
     ]
   )
   ```
2. TaskCreate: market-researcher에게 "S#·P# 가설 근거 검증 + 페르소나·경쟁 맵 작성"
3. 조사 완료 → quality-reviewer가 **기둥 검증의 탄탄함**을 먼저 점검한다 (근거 없는 기둥이 하류로 흘러가면 카피·비주얼이 전량 헛돈다)
4. **스파인 교정 판단:** 조사가 기둥 가설을 뒤집으면(예: "P1 가격 소구는 약함, 신뢰가 진짜 차별점"), 리드가 `00_brief.md`의 스파인을 갱신한다. 큰 변경이면 사용자에게 재확인한다. 이 교정은 창작 전에 끝내야 한다.

### Phase 3: 카피·비주얼 병렬 창작

**실행 방식:** 에이전트 팀 (copywriter + visual-concept-designer 동시, quality-reviewer 상주)

1. copywriter와 visual-concept-designer를 팀에 추가하고, 검증된 스파인·조사 경로를 프롬프트로 전달
2. 전체 브리핑 (`SendMessage`): 검증된 기둥(P#)·세그먼트(S#), 각자 담당 기둥, `00_brief.md`·`01_market_research.md` 경로, [P#][S#] 태깅 준수 요청
3. TaskCreate: copywriter "채널별 카피 세트 + 변형", visual-concept-designer "아트 디렉션 + 키 비주얼 컨셉" (조사 완료에 의존)
4. **통신 규칙 — 이 Phase의 핵심 (리드를 경유하지 않는다):**
   - copywriter와 visual-concept-designer는 SendMessage로 **같은 기둥을 강화하도록** 핵심 문구·무드·카피 자리·길이를 직접 맞춘다
   - 두 창작자는 모든 산출물을 **같은 P번호로 태깅**한다 — 이것이 다음 정합성 검수의 정렬 축이다
   - quality-reviewer는 카피·비주얼이 나오는 즉시 정합을 점검하고, 불일치·근거부족·가드레일 위반을 담당 작가에게 직접 수정 요청한다 (전량 완성을 기다리지 않는다)
5. 리드는 두 산출물이 완료될 때까지 큰 개입을 하지 않는다. 단, 리뷰어가 "카피 대 비주얼 상충, 어느 기둥이 맞는지 판정 필요"를 보고하면 스파인 기준으로 판정한다

### Phase 4: A/B 테스트 계획

**실행 방식:** 에이전트 팀 (ab-test-planner 합류, quality-reviewer 상주)

1. ab-test-planner를 팀에 추가하고, 카피·비주얼 변형 경로 + 성공 지표·우선순위 변수를 전달
2. TaskCreate: "가설 기반 실험 설계 → `04_ab_test_plan.md` (변수 격리·가드레일 지표 필수)"
3. **통신 규칙:** ab-test-planner가 통제된 대조(한 변수만 다른 변형 쌍)가 부족하면 copywriter·visual-concept-designer에게 직접 추가 변형을 요청한다. quality-reviewer가 테스트결함(변수 미격리·가설 없음·가드레일 지표 누락·중요 변수 미검증)을 점검해 재설계를 요청한다

### Phase 5: 종합 정합성 검수 + 반복 개선 루프

**실행 방식:** 에이전트 팀 (quality-reviewer 주도, 창작자 대기)

1. quality-reviewer가 네 산출물 전체를 스파인 기준으로 교차 대조 → `05_review.md`에 정합성 매트릭스·지적 목록·가드레일 위반·판정 기록
2. **정합/경미** → Phase 6
3. **불일치/근거부족/누락/테스트결함 있음** → 반복 개선 루프:
   - 리드가 지적을 담당별로 묶는다 (예: "카피 세트 B가 P3로 새어 카피 정렬 필요", "T2 변수 미격리 → 테스트 재설계")
   - 해당 작가에게 SendMessage로 **수정 범위만** 전달한다. 전면 재작업이 아니라 지목된 항목만 고친다
   - 작가가 해당 산출물 섹션을 갱신
   - quality-reviewer가 **수정된 부분만** 재검수 (영향받는 P번호만), 수정으로 새로 생긴 불일치가 없는지 확인
   - **최대 2회.** 3회차 진입 시 남은 미해결 항목을 `05_review.md`에 "알려진 한계"로 확정하고 Phase 6으로 넘어간다. 완벽한 정합을 무한히 좇는 비용이 한계효용보다 크기 때문이다

### Phase 6: 캠페인 패키지 조립

**실행 방식:** 리드(메인 세션) 주도

1. 리드가 `marketing/_workspace/05_campaign_direction.md`에 조립 방향을 정리(최종 정렬 판단·강조점·남은 한계)
2. 리드가 네 산출물을 하나의 **캠페인 패키지**로 조립해 `marketing/outputs/{YYYYMMDD}-{slug}/campaign-package.md`에 출력. 패키지 필수 섹션:
   - **캠페인 요약**: 타겟·핵심 메시지(기둥)·오퍼 한눈에
   - **포지셔닝**: 세그먼트·메시지 기둥 (검증 근거 포함)
   - **광고 카피**: 채널별 카피 세트·변형 (P#·S# 태깅)
   - **비주얼 컨셉**: 아트 디렉션·키 비주얼·레이아웃 명세
   - **A/B 테스트 계획**: 실험 로드맵·가설·지표
   - **정합성 검수 결과 / 알려진 한계**: 통과 항목과 미해결 항목
3. 완료 조건: 모든 검증된 기둥이 카피·비주얼로 다뤄지고, A/B가 핵심 변수를 검증하며, 가드레일 위반이 없을 것. 누락·위반이 남아 있으면 "알려진 한계"에 명시
4. 팀원에게 종료 알림 → `TeamDelete`
5. `marketing/_workspace/`는 **삭제하지 않는다** (사후 검증·부분 재실행의 입력)
6. 사용자에게 요약 보고: 포지셔닝, 핵심 카피·비주얼 방향, 우선 테스트, 남은 한계, 패키지 경로
7. 피드백 요청: "결과에서 개선할 부분이나 팀 구성에서 바꾸고 싶은 점이 있나요?"

## 데이터 흐름

```
사용자 입력
    ↓
[리드] 포지셔닝 스파인 분해 → 00_brief.md (S#·P#) → 사용자 승인
    ↓
market-researcher → 01_market_research.md (기둥 검증·페르소나·경쟁 맵)
    ↓ quality-reviewer 점진 검수 → 기둥 근거 확인 → (필요 시 리드가 스파인 교정)
 ┌──────────────────────┬──────────────────────┐
 ↓                      ↓          (SendMessage로 같은 기둥 강화·무드 정렬)
copywriter              visual-concept-designer
02_ad_copy.md           03_visual_concept.md
 └──────────────────────┴──────────────────────┘
    ↓ (P번호로 정렬) · quality-reviewer 점진 검수
ab-test-planner → 04_ab_test_plan.md (변수 격리·가드레일 지표)
    ↓
quality-reviewer 종합 검수 → 05_review.md (정합/불일치/근거부족/누락/테스트결함)
    ↓ 반복 개선(최대 2회) ↺  담당 작가 재소집
[리드] 조립 방향 → 05_campaign_direction.md
    ↓
outputs/{date}-{slug}/campaign-package.md
    ↓
[리드: 최종 확인 + 사용자 보고]
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 시장 조사 데이터 부족 | 확보한 것만 기록, "조사 모드: 제한적" 명시. 수치를 지어내지 않는다. reviewer가 근거 없는 카피를 "근거부족"으로 걸러냄 |
| 조사가 기둥 가설을 전면 부정 | 창작 전에 리드가 스파인 교정, 큰 변경이면 사용자 재확인. 잘못된 축 위 창작은 전량 폐기 |
| 카피 대 비주얼 상충 | 삭제하지 않고 리드가 스파인 충실도로 판정, 진 쪽을 정렬. 취향이 아니라 스파인이 기준 |
| 근거 없는 최상급·금지 표현 | reviewer가 매력도와 무관하게 반려. 완화 또는 근거 보강. 규제 리스크는 타협 없음 |
| A/B 변형 부족(테스트 불가) | ab-test-planner가 창작자에게 통제된 변형 요청. 없으면 "변형 필요"로 명시 |
| 검증된 기둥 미커버(누락) | reviewer가 발견으로 기록 → 리드가 담당 배정 또는 "알려진 한계"로 명시 |
| 팀원 1명 실패 | SendMessage로 상태 확인 → 1회 재시작 → 재실패 시 해당 산출물을 패키지에 "미완성"으로 명시하고 진행 |
| quality-reviewer 실패 | 리드가 `marketing-campaign-harness:campaign-review` 스킬의 정합성 검수 절차를 직접 수행 |
| 팀원 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 반복 루프 3회차 | 루프 종료. 남은 미해결 항목을 패키지 "알려진 한계"에 기록 |
| 실제 이미지 생성 요청 | 이 하네스는 비주얼 컨셉·명세까지 산출. 실제 제작은 명세를 받을 디자이너·이미지 툴로 안내 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "신규 명상 앱 런칭 캠페인 만들어줘. 바쁜 직장인 타겟, 인스타·유튜브 광고."
2. Phase 1 — 리드가 스파인 분해(S1 번아웃 직장인·S2 수면 문제 직장인 / P1 "5분이면 충분", P2 "과학적 검증", P3 "습관 형성"), 성공 지표(설치당 비용·7일 잔존), 가드레일(의학적 효능 단정 금지), 사용자 승인
3. Phase 2 — market-researcher가 경쟁 앱 메시지 수집, P2(과학적 검증)는 경쟁사도 다 하는 말이라 "약함"으로 판정, "직장 중 몰래 쓸 수 있는 은밀함"을 대안 기둥으로 제안 → 리드가 P2를 교체
4. Phase 3 — copywriter(혜택 vs 공포 변형)·visual-concept-designer(차분한 무채색 vs 활기 대비) 병렬 창작, 두 사람이 SendMessage로 "P1은 여백 많은 미니멀 비주얼 + '5분' 헤드라인"으로 정렬, 모두 P번호 태깅
5. Phase 4 — ab-test-planner가 T1(헤드라인 소구: 혜택 vs 공포)·T2(키 비주얼)를 변수 격리해 설계, 가드레일 지표로 7일 잔존 지정
6. Phase 5 — reviewer 검수: 카피 하나가 "불면증 치료"라는 의학적 단정(가드레일 위반) 적발 → copywriter가 "숙면 습관"으로 완화, 재검수 통과
7. Phase 6 — `outputs/20260724-meditation-app-launch/campaign-package.md` 생성
8. 예상: 검증된 포지셔닝에 카피·비주얼·테스트가 정렬되고 가드레일을 지킨 패키지

### 에러 흐름 A — 카피·비주얼 상충
1. Phase 3에서 copywriter는 P1(가성비)을 밀고, visual-concept-designer는 P3(프리미엄)을 강화 — 한 캠페인이 두 방향으로 갈림
2. quality-reviewer가 점진 검수에서 "불일치" 적발, 리드에 보고
3. 리드가 스파인 확인 — 주 기둥은 P1 → visual을 P1(가성비: 정직·명료한 비주얼)로 정렬 요청
4. visual-concept-designer가 키 비주얼만 수정, reviewer 재검수 통과
5. 취향이 아니라 스파인이 판정 기준이었음

### 에러 흐름 B — 반복 루프 한도 초과
1. Phase 5 1회차: 지적 3건 (카피 근거부족, T2 변수 미격리, P2 비주얼 누락)
2. 리드가 담당별로 수정 범위 전달
3. 2회차: 근거부족·T2는 해소, P2 비주얼은 제작 제약으로 여전히 누락
4. 3회차 진입 금지 → P2 비주얼 누락을 `05_review.md`·패키지 "알려진 한계"로 확정
5. Phase 6 진행, 패키지에 명시, 사용자 보고 시 언급
