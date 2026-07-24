# harness-lab

도메인별 하네스(에이전트 팀 + 스킬)를 구축·축적하는 저장소. 각 하네스는 최상위 디렉토리 하나를 차지하며, 아래 트리거 규칙에 따라 해당 오케스트레이터 스킬로 진입한다.

## 하네스: 웹툰 에피소드 제작

**목표:** 스토리·캐릭터·패널·대사를 병렬 제작하고 상호 교차 리뷰로 스타일 일관성을 확보해, 회차 원고 패키지와 콘티를 산출한다.

**위치:** `webtoon-studio/`

**트리거:** 웹툰 회차 제작·기획·연출·캐릭터·대사 관련 작업 요청 시 `webtoon-episode-orchestrator` 스킬을 사용하라. 후속 요청("대사만 다시", "컷 다시 나눠줘", "리뷰 한 번 더")도 동일하다. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-23 | 초기 구성 — 에이전트 5, 스킬 6 | webtoon-studio 전체 | issue #1 |

## 하네스: 유튜브 콘텐츠 제작

**목표:** 트렌드 조사 → 대본 → 제목/태그 SEO → 썸네일 컨셉 → 교차 검수를 감독자 에이전트가 조율하여, 발행 가능한 콘텐츠 패키지 하나를 만들어낸다.

**위치:** `youtube-content-harness/`

**트리거:** 유튜브 영상 기획·콘텐츠 제작 관련 요청(소재 발굴, 대본, 제목/태그, 썸네일, 검수 — 부분 요청 포함) 시 `youtube-content-orchestrator` 스킬을 사용하라. 단순 질문("유튜브 알고리즘이 뭐야")은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-23 | 초기 구성 — 감독자 + 팀원 5명(trend-researcher, script-writer, seo-optimizer, thumbnail-planner, content-reviewer), 스킬 6개 | 전체 | issue #2 |
| 2026-07-23 | content-reviewer 추가 (이슈 명시 4명 외) | agents/content-reviewer.md, skills/youtube-content-review | 산출물 간 정합성 검증 축이 없으면 제목·대본·썸네일이 서로 다른 영상을 가리킴 |
| 2026-07-23 | 대본 스킬을 롱폼/숏폼 레퍼런스로 분리 | skills/youtube-script-writing/references/ | 두 포맷의 구조·평가지표가 근본적으로 달라 단일 문서로는 오버피팅 |
| 2026-07-23 | 에이전트 정의에 경로 기준 명시 | agents/*.md | 팀원은 저장소 루트에서 실행되므로 `_workspace/`만으로는 엉뚱한 위치에 파일을 쓴다 |
| 2026-07-23 | 워커 스킬 description에 경계 조건 추가 | skills/youtube-{trend-research,script-writing,seo-optimization,thumbnail-concept,content-review} | 트리거 검증에서 오케스트레이터와의 충돌 및 도메인 누수(블로그 SEO, 이미지 생성) 발견 |
