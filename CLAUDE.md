# harness-lab

도메인별 하네스(에이전트 팀 + 스킬)를 구축·축적하는 저장소. **이 저장소 자체가 Claude Code 플러그인 마켓플레이스**이며, 각 하네스는 최상위 디렉토리 하나를 차지하는 독립 플러그인이다.

## 구조 규약

하네스 하나 = 플러그인 하나 = 최상위 디렉토리 하나.

```
<harness>/
  .claude-plugin/plugin.json    # 플러그인 메타데이터
  agents/<agent>.md             # subagent_type: <harness>:<agent>
  skills/<skill>/SKILL.md       # Skill 이름: <harness>:<skill>
```

새 하네스를 추가하면 루트 `.claude-plugin/marketplace.json`의 `plugins` 배열에도 등록한다. 등록하지 않으면 다른 프로젝트에서 설치할 수 없다.

**작성 규칙 3가지** — 하나라도 어기면 다른 프로젝트에서 깨진다:

1. **에이전트·스킬을 경로로 참조하지 않는다.** 에이전트는 `subagent_type`, 스킬은 Skill 툴 이름으로 호출한다. 플러그인 설치 위치는 환경마다 다르다.
2. **이름에 도메인 접두사를 붙이지 않는다.** 네임스페이스가 이미 `<harness>:`를 붙이므로 `youtube-trend-research`는 `youtube-content-harness:youtube-trend-research`가 되어 중복된다.
3. **산출물 경로는 실행 프로젝트 루트 기준 상대 경로**로 쓴다. 플러그인 소스 디렉토리에 쓰면 안 된다 — 그곳은 사용자의 프로젝트가 아니다.

스킬 안에서 자기 플러그인의 스크립트·레퍼런스를 참조할 때만 `${CLAUDE_PLUGIN_ROOT}/skills/...`를 쓴다. **이것은 셸 환경변수가 아니다** — 스킬을 호출한 모델이 알게 되는 절대 경로로 직접 치환해서 실행해야 한다. 그대로 Bash에 넘기면 `/skills/...`로 해석되어 실패한다.

## 다른 프로젝트에서 사용하기

사용할 프로젝트의 `.claude/settings.json`에 추가한다:

```json
{
  "extraKnownMarketplaces": {
    "harness-lab": {
      "source": { "source": "github", "repo": "donghoon-bigvalue/harness-lab" }
    }
  },
  "enabledPlugins": {
    "youtube-content-harness@harness-lab": true,
    "webtoon-studio@harness-lab": true
  }
}
```

필요한 하네스만 켠다. 설치 확인은 `claude plugin list`, 구성 요소 확인은 `claude plugin details <name>`. 로컬에서 수정 중인 하네스를 시험하려면 `claude --plugin-dir <하네스 디렉토리>`로 해당 세션에만 로드한다.

## 하네스: 웹툰 에피소드 제작

**목표:** 스토리·캐릭터·패널·대사를 병렬 제작하고 상호 교차 리뷰로 스타일 일관성을 확보해, 회차 원고 패키지와 콘티를 산출한다.

**플러그인:** `webtoon-studio` (에이전트 5, 스킬 6) | **작업 루트:** 실행 프로젝트의 `webtoon/`

**트리거:** 웹툰 회차 제작·기획·연출·캐릭터·대사 관련 작업 요청 시 `webtoon-studio:episode-orchestrator` 스킬을 사용하라. 후속 요청("대사만 다시", "컷 다시 나눠줘", "리뷰 한 번 더")도 동일하다. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-23 | 초기 구성 — 에이전트 5, 스킬 6 | webtoon-studio 전체 | issue #1 |
| 2026-07-24 | 플러그인으로 패키징 | webtoon-studio 전체 | 다른 프로젝트에서 복사 없이 사용 |
| 2026-07-24 | 팀원 소집을 실제 `subagent_type`으로 전환 | skills/episode-orchestrator | 플러그인 배포 에이전트가 커스텀 타입으로 등록됨을 검증 — 정의 파일 Read 우회 불필요 |
| 2026-07-24 | 스크립트 경로를 `${CLAUDE_PLUGIN_ROOT}` 기준으로 변경 | panel-layout, style-consistency 및 호출부 | 저장소 상대 경로는 설치 환경에서 존재하지 않음 |

## 하네스: 유튜브 콘텐츠 제작

**목표:** 트렌드 조사 → 대본 → 제목/태그 SEO → 썸네일 컨셉 → 교차 검수를 감독자 에이전트가 조율하여, 발행 가능한 콘텐츠 패키지 하나를 만들어낸다.

**플러그인:** `youtube-content-harness` (감독자 1 + 팀원 5, 스킬 6) | **작업 루트:** 실행 프로젝트의 `youtube-content/`

**트리거:** 유튜브 영상 기획·콘텐츠 제작 관련 요청(소재 발굴, 대본, 제목/태그, 썸네일, 검수 — 부분 요청 포함) 시 `youtube-content-harness:orchestrator` 스킬을 사용하라. 단순 질문("유튜브 알고리즘이 뭐야")은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-23 | 초기 구성 — 감독자 + 팀원 5명(trend-researcher, script-writer, seo-optimizer, thumbnail-planner, content-reviewer), 스킬 6개 | 전체 | issue #2 |
| 2026-07-23 | content-reviewer 추가 (이슈 명시 4명 외) | agents/content-reviewer.md, skills/content-review | 산출물 간 정합성 검증 축이 없으면 제목·대본·썸네일이 서로 다른 영상을 가리킴 |
| 2026-07-23 | 대본 스킬을 롱폼/숏폼 레퍼런스로 분리 | skills/script-writing/references/ | 두 포맷의 구조·평가지표가 근본적으로 달라 단일 문서로는 오버피팅 |
| 2026-07-23 | 에이전트 정의에 경로 기준 명시 | agents/*.md | 팀원이 `_workspace/`만으로는 엉뚱한 위치에 파일을 쓴다 |
| 2026-07-23 | 워커 스킬 description에 경계 조건 추가 | skills/{trend-research,script-writing,seo-optimization,thumbnail-concept,content-review} | 트리거 검증에서 오케스트레이터와의 충돌 및 도메인 누수(블로그 SEO, 이미지 생성) 발견 |
| 2026-07-24 | 플러그인으로 패키징 | 전체 | 다른 프로젝트에서 복사 없이 사용 |
| 2026-07-24 | 팀원 소집을 실제 `subagent_type`으로 전환 | skills/orchestrator | 플러그인 배포 에이전트가 커스텀 타입으로 등록됨을 검증 — 정의 파일 Read 우회 불필요 |

## 하네스: 딥 리서치

**목표:** 어떤 주제든 웹·학술·커뮤니티 세 각도에서 병렬 조사하고 교차 검증(삼각측량)하여, 신뢰도 층위를 매긴 종합 리서치 보고서 하나를 산출한다.

**플러그인:** `deep-research` (리서치 리드 1 + 조사원 5, 스킬 6) | **작업 루트:** 실행 프로젝트의 `research/`

**트리거:** 어떤 주제든 깊이 조사·리서치·자료 조사·여러 각도 조사·팩트체크·종합 보고서 요청(부분 요청 포함) 시 `deep-research:orchestrator` 스킬을 사용하라. 후속 요청("커뮤니티 반응만 다시", "학술 근거 보강", "보고서만 다시")도 동일하다. 단순 사실 한 줄 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-24 | 초기 구성 — 리드 + 조사원 5명(web-researcher, academic-researcher, community-researcher, cross-validator, synthesis-writer), 스킬 6개 | deep-research 전체 | issue #6 |
| 2026-07-24 | 조사원 3명에 공통 주장 레코드 형식(출처유형·신뢰강도·Q번호 태깅) 부여 | agents/{web,academic,community}-researcher, skills/{web,academic,community}-research | Q번호 정렬과 출처 태깅이 없으면 cross-validator가 세 각도를 삼각측량할 수 없음 |
| 2026-07-24 | 교차 검증 축(cross-validator)을 이슈 명시 각도 외로 추가 | agents/cross-validator.md, skills/cross-validation | "교차 검증 후 종합"이 이슈 핵심 요구 — 삼각측량 분류(확증/상충/단일출처/미확인)가 신뢰도 층위의 근거 |

## 하네스: API 문서 생성

**목표:** 코드베이스에서 API 엔드포인트를 추출·분석하고, 설명·사용 예제를 작성한 뒤, 실제 소스와 교차 대조하는 완성도 리뷰를 파이프라인으로 처리하여, 근거(파일:라인)가 붙은 API 레퍼런스 문서 하나를 산출한다.

**플러그인:** `api-doc-harness` (문서 리드 1 + 팀원 4, 스킬 5) | **작업 루트:** 실행 프로젝트의 `api-docs/`

**트리거:** 코드베이스의 API 문서화·API 레퍼런스 생성·엔드포인트 문서 자동 생성·OpenAPI 명세 추출 요청(부분 요청 포함) 시 `api-doc-harness:orchestrator` 스킬을 사용하라. 후속 요청("특정 엔드포인트 설명만 다시", "예제에 언어 추가", "응답 형태 틀린 것 고쳐", "새 엔드포인트 반영", "리뷰 다시")도 동일하다. 단순한 API 사용법 한 줄 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-24 | 초기 구성 — 리드 + 팀원 4명(endpoint-analyzer, description-writer, example-generator, completeness-reviewer), 스킬 5개 | api-doc-harness 전체 | issue #10 |
| 2026-07-24 | 엔드포인트 ID(E번호) + 파일:라인 근거를 파이프라인 공통 색인으로 부여 | agents/*, skills/* | E번호 정렬이 없으면 설명·예제가 어느 엔드포인트를 가리키는지, 리뷰어가 무엇을 대조하는지 알 수 없음 |
| 2026-07-24 | 완성도 리뷰를 "존재 확인"이 아닌 소스 직접 3자 교차 대조로 규정 | agents/completeness-reviewer.md, skills/completeness-review | API 문서의 치명적 실패는 그럴듯하지만 코드와 다른 서술 — 레코드만 믿으면 추출 오류·누락을 통과시킴 |
| 2026-07-24 | 프레임워크별 라우트 탐색 전략을 조건부 로딩 reference로 분리 | skills/endpoint-analysis/references/frameworks.md | Express·FastAPI·Spring·Rails·Go 등 스택별 등록 방식이 근본적으로 달라 단일 문서로는 오버피팅 |
