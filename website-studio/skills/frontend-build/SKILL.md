---
name: frontend-build
description: "React/Next.js(App Router)로 페이지·컴포넌트·데이터 훅을 구현하고, 확정된 API 계약의 응답 shape을 정확히 소비하며, 디자인 토큰으로 일관된 반응형 UI를 만든다. 프론트엔드 구현, React/Next.js 컴포넌트·페이지·훅 작성, 화면 코드 작업 시 반드시 이 스킬을 사용할 것."
---

# Frontend Build — React/Next.js 구현

디자인 스펙을 동작하는 화면으로 만들되, **API 계약이 약속한 shape을 정확히 소비**한다. 계약을 어긋나게 읽으면 화면은 컴파일되지만 런타임에 죽는다.

## 왜 계약 소비가 핵심인가

`fetchJson<Project[]>()`는 런타임 응답이 `{ projects: [...] }`여도 컴파일을 통과한다. 그래서 TypeScript만 믿으면 `projects.filter is not a function`이 배포까지 살아남는다. 컴파일러가 아니라 **계약서(`01_api_contract.md`)를 직접 대조**해야 한다.

## 프로젝트 구조 (Next.js App Router)

앱 루트는 `website/`. 없으면 최소 구조를 스캐폴딩한다:

```
website/
  app/
    layout.tsx, page.tsx        # P1 (예: 랜딩)
    (auth)/login/page.tsx       # route group — URL에서 (auth) 제거됨
    dashboard/page.tsx          # /dashboard
    dashboard/projects/[id]/page.tsx  # /dashboard/projects/:id
  components/                    # 컴포넌트 인벤토리 구현
  hooks/                         # API 계약 소비 훅
  lib/                           # fetch 래퍼·타입·유틸
  app/globals.css                # 디자인 토큰 → CSS 변수/테마
```

`package.json`·`tsconfig`·(Tailwind 사용 시) 설정이 없으면 표준 Next.js 세팅을 만든다.

## 계약 소비 체크리스트

훅을 쓸 때마다 계약서와 대조한다:

- [ ] **래핑 일치**: 계약이 `{ projects: [...] }`면 훅에서 `.projects`를 꺼낸다. 배열이라고 가정해 바로 `.filter` 부르지 않는다
- [ ] **케이싱 일치**: 계약이 `thumbnailUrl`이면 `thumbnail_url`로 접근하지 않는다
- [ ] **필드 존재**: 계약에 없는 필드를 기대하지 않는다. 필요하면 계약 변경을 협상
- [ ] **동기/비동기**: 계약이 202 즉시 응답이면, 즉시 응답에서 최종 결과 필드(`data.result` 등)에 접근하지 않는다
- [ ] **엔드포인트 일치**: 훅의 fetch URL이 계약의 경로·메서드와 정확히 일치

## 훅 작성 패턴

```typescript
// lib/api.ts — 공통 fetch 래퍼 (계약의 래핑을 여기서 풀지 말고 각 훅에서 명시적으로)
async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> { ... }

// hooks/useProjects.ts — 계약: GET /api/projects → { projects: Project[] }
export function useProjects() {
  // T를 계약의 실제 응답 shape으로 지정 — 배열이 아니라 래핑된 형태
  const res = await fetchJson<{ projects: Project[] }>("/api/projects");
  return res.projects;   // 계약이 명시한 대로 unwrap
}
```

훅↔엔드포인트 매핑을 로그에 표로 남긴다 — QA가 1:1 매핑을 검증한다.

## 라우팅 정합성

- route group `(group)`은 URL에서 빠진다: `app/(auth)/login/page.tsx` → `/login`
- 중첩 경로는 접두사를 갖는다: `app/dashboard/projects/[id]` → `/dashboard/projects/:id`
- 모든 `href`·`router.push()`·`redirect()`가 **실제 존재하는 page 경로**를 가리키는지 확인. 파일 구조와 링크를 대조

## 스타일링

- 디자인 토큰만 사용. 색·간격을 하드코딩하지 않는다 → CSS 변수나 Tailwind 테마로 토큰을 옮겨 쓴다
- 반응형: 스펙의 브레이크포인트대로 구현 (모바일에서 무엇이 접히는지)
- 상태별 UI: 빈/로딩/에러를 스펙대로 구현. 급조하지 않는다

## 출력

- 앱 코드: `website/app`, `website/components`, `website/hooks`, `website/lib`
- `website/_workspace/02_frontend_log.md`: 구현 화면(P번호), **훅↔엔드포인트 매핑 표**, 계약 이탈 발생 시 내역

## 원칙

- **계약이 유일한 진실.** 계약에 없는 데이터가 필요하면 목업으로 때우지 말고 build-lead·backend에 계약 변경을 요청한다. 완료 전까지 로딩/플레이스홀더로 두고 로그에 명시
- **런타임 shape이 계약과 다르면** 프론트를 임의로 맞추지 말고 QA·backend에 경계면 불일치로 보고 — 어느 쪽이 계약을 어겼는지 판정 후 수정
- **재호출 시** 전면 재작성하지 않고 지목된 화면·훅만 수정. 계약이 갱신됐으면 영향받는 훅의 소비부만 맞춘다
