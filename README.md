# harness-lab

도메인별 **하네스**(에이전트 팀 + 스킬)를 구축·축적하는 저장소. 이 저장소 자체가 **Claude Code 플러그인 마켓플레이스**이며, 각 하네스는 최상위 디렉토리 하나를 차지하는 독립 플러그인이다. 필요한 하네스만 켜서 다른 프로젝트에서 복사 없이 사용한다.

## 하네스란

하네스 하나 = **전문 에이전트 팀 + 그들이 사용하는 스킬**의 묶음이다. 감독자(오케스트레이터) 스킬이 도메인 작업을 팬아웃/파이프라인으로 팀원 에이전트에게 위임하고, 산출물을 교차 검증해 하나의 완성된 결과물로 통합한다.

```
<harness>/
  .claude-plugin/plugin.json    # 플러그인 메타데이터
  agents/<agent>.md             # subagent_type: <harness>:<agent>
  skills/<skill>/SKILL.md       # Skill 이름: <harness>:<skill>
```

## 하네스 목록

| 하네스 (플러그인) | 목적 | 구성 | 작업 루트 |
|---|---|---|---|
| **youtube-content-harness** | 트렌드 조사 → 대본 → 제목/태그 SEO → 썸네일 컨셉 → 교차 검수로 발행 가능한 유튜브 콘텐츠 패키지 산출 | 감독자 1 + 팀원 5, 스킬 6 | `youtube-content/` |
| **webtoon-studio** | 스토리·캐릭터·패널·대사를 병렬 제작하고 상호 교차 리뷰로 스타일 일관성 확보, 회차 원고+콘티 산출 | 에이전트 5, 스킬 6 | `webtoon/` |
| **deep-research** | 어떤 주제든 웹·학술·커뮤니티 세 각도에서 병렬 조사·삼각측량하여 신뢰도 층위를 매긴 종합 보고서 산출 | 리드 1 + 조사원 5, 스킬 6 | `research/` |
| **website-studio** | 와이어프레임·디자인 → API 계약 → 프론트(React/Next.js)·백엔드 병렬 구현 → 경계면 QA → 배포 준비 파이프라인 | 빌드 리드 1 + 엔지니어 5, 스킬 6 | `website/` |
| **code-review-harness** | 아키텍처·보안·성능·스타일 네 축을 병렬 감사하고 교차 검증해 심각도로 우선순위를 매긴 하나의 리뷰 리포트로 통합 | 리드 1 + 감사원 4 + 검증관 1 + 통합관 1, 스킬 7 | `code-review/` |
| **marketing-campaign-harness** | 타겟 조사로 포지셔닝을 세우고 카피·비주얼·A/B 계획을 정렬시켜 반복 품질 리뷰로 캠페인 패키지 산출 | 리드 1 + 전문가 5, 스킬 6 | `marketing/` |
| **data-pipeline-harness** | 스키마 → ETL → 검증 규칙 → 모니터링을 계층적으로 위임하고 통합 리뷰어가 정합성을 교차 검증한 파이프라인 설계 패키지 산출 | 아키텍트 1 + 에이전트 5, 스킬 6 | `data-pipeline/` |
| **api-doc-harness** | 코드베이스에서 API 엔드포인트를 추출·분석하고 설명·예제를 작성한 뒤 소스와 교차 대조하여 근거(파일:라인)가 붙은 API 레퍼런스 산출 | 리드 1 + 팀원 4, 스킬 5 | `api-docs/` |

각 하네스의 설계 근거와 변경 이력은 [`CLAUDE.md`](./CLAUDE.md)에 상세히 기록되어 있다.

## 다른 프로젝트에서 사용하기

사용할 프로젝트의 `.claude/settings.json`에 마켓플레이스를 등록하고 필요한 하네스만 켠다.

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

| 목적 | 명령 |
|---|---|
| 설치 확인 | `claude plugin list` |
| 구성 요소 확인 | `claude plugin details <name>` |
| 로컬 수정본 시험 (해당 세션만) | `claude --plugin-dir <하네스 디렉토리>` |

하네스를 켜면 해당 도메인 작업 요청 시 감독자 스킬이 자동으로 트리거되며, 산출물은 **실행 프로젝트 루트 기준**의 작업 루트(위 표 참조)에 생성된다.

## 새 하네스 추가하기

`harness:harness` 스킬(하네스 엔지니어링 메타 스킬)로 구성하는 것을 권장한다. 수기로 추가할 때도 아래 규약을 지켜야 한다.

새 하네스를 추가하면 루트 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json)의 `plugins` 배열에도 등록한다. **등록하지 않으면 다른 프로젝트에서 설치할 수 없다.**

### 작성 규칙 — 하나라도 어기면 다른 프로젝트에서 깨진다

1. **에이전트·스킬을 경로로 참조하지 않는다.** 에이전트는 `subagent_type`, 스킬은 Skill 툴 이름으로 호출한다. 플러그인 설치 위치는 환경마다 다르다.
2. **이름에 도메인 접두사를 붙이지 않는다.** 네임스페이스가 이미 `<harness>:`를 붙이므로, `youtube-trend-research`는 `youtube-content-harness:youtube-trend-research`가 되어 중복된다.
3. **산출물 경로는 실행 프로젝트 루트 기준 상대 경로**로 쓴다. 플러그인 소스 디렉토리에 쓰면 안 된다 — 그곳은 사용자의 프로젝트가 아니다.

스킬 안에서 자기 플러그인의 스크립트·레퍼런스를 참조할 때만 `${CLAUDE_PLUGIN_ROOT}/skills/...`를 쓴다. **이것은 셸 환경변수가 아니다** — 스킬을 호출한 모델이 알게 되는 절대 경로로 직접 치환해서 실행해야 한다. 그대로 Bash에 넘기면 `/skills/...`로 해석되어 실패한다.

## 저장소 구조

```
harness-lab/
  .claude-plugin/marketplace.json   # 마켓플레이스 정의 (모든 하네스 등록)
  CLAUDE.md                         # 하네스별 설계 근거·변경 이력
  <harness>/                        # 하네스 하나 = 플러그인 하나
    .claude-plugin/plugin.json
    agents/*.md
    skills/*/SKILL.md
```
