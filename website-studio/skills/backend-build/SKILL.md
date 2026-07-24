---
name: backend-build
description: "Next.js Route Handler 또는 API 서버로 엔드포인트·데이터 모델·비즈니스 로직·상태 전이를 구현하고, 확정된 API 계약이 명시한 정확한 응답 shape·필드명·케이싱·상태코드를 내보낸다. 백엔드·API·엔드포인트·데이터 모델·서버 로직 구현 시 반드시 이 스킬을 사용할 것."
---

# Backend Build — API·데이터 구현

화면 뒤의 데이터와 로직을 만들되, **API 계약이 약속한 shape을 정확히 반환**한다. 필드 하나를 다른 이름·케이싱으로 내보내면 프론트가 컴파일은 되지만 런타임에 빈 화면을 띄운다.

## 왜 계약 준수가 핵심인가

프론트는 계약대로 소비한다. 계약이 `{ projects: [...] }`인데 배열을 반환하면, 프론트의 `.projects`가 undefined가 되고 `undefined.filter`로 크래시한다. 각자 "맞게" 짰지만 연결부가 죽는다. 그래서 응답은 계약서와 **바이트 단위로 일치**해야 한다.

## 프로젝트 구조 (Next.js Route Handler)

앱 루트는 `website/`:

```
website/
  app/api/
    projects/route.ts           # GET/POST /api/projects
    projects/[id]/route.ts      # GET/PATCH/DELETE /api/projects/:id
  lib/
    db.ts                       # 데이터 저장소 (DB/파일/인메모리)
    models.ts                   # 엔티티 타입 + DB↔API 케이싱 변환
    validation.ts               # 요청 검증
```

지정된 스택이 별도 API 서버(Express 등)면 그 구조를 따르되, 계약 준수 원칙은 동일하다.

## 계약 준수 체크리스트

엔드포인트마다 계약서와 대조한다:

- [ ] **경로·메서드 일치**: 계약의 모든 엔드포인트가 실제 route로 존재 (없으면 프론트가 404)
- [ ] **응답 래핑 일치**: 계약이 `{ projects: [...] }`면 정확히 그 래핑. 배열이면 래핑 안 함
- [ ] **필드명·케이싱 일치**: DB가 `thumbnail_url`이어도 계약이 `thumbnailUrl`이면 변환해서 반환. DB 필드명이 새어나가지 않게
- [ ] **상태코드 일치**: 계약의 성공/에러 코드대로 (201 생성, 202 비동기 접수, 404 없음 등)
- [ ] **동기/비동기 일치**: 계약이 202 즉시 응답이면 상태만 반환, 최종 결과는 별도 조회 엔드포인트로

## 데이터 모델 & 케이싱 변환

DB 필드명이 API로 새어나가지 않게 경계에서 변환한다:

```typescript
// lib/models.ts
type ProjectRow = { id: string; thumbnail_url: string; updated_at: string };  // DB (snake_case)
type Project    = { id: string; thumbnailUrl: string; updatedAt: string };    // API (camelCase, 계약)

function toApi(row: ProjectRow): Project {
  return { id: row.id, thumbnailUrl: row.thumbnail_url, updatedAt: row.updated_at };
}
```

## 상태 전이 완전성

상태를 가진 엔티티는 전이 맵을 정의하고, **모든 전이가 실제 코드에 존재**하게 한다:

```typescript
// lib/models.ts
const STATE_TRANSITIONS = { todo: ["doing"], doing: ["done", "todo"], done: [] };
```

- **죽은 전이 금지**: 맵에 있으나 코드에 없는 전이 → 프론트가 그 상태에서 영원히 멈춤. 특히 중간 상태(예: `generating`)에서 최종 상태(`ready`)로의 전환 누락 주의
- **무단 전이 금지**: 코드에 있으나 맵에 없는 `.update({ status })` → 상태머신 붕괴
- 모든 `status` 업데이트가 맵의 허용 전이인지 검증하는 가드를 둔다

## 응답 패턴

```typescript
// app/api/projects/route.ts — 계약: GET → { projects: Project[] }
export async function GET() {
  const rows = await db.listProjects();
  return NextResponse.json({ projects: rows.map(toApi) });  // 계약대로 래핑 + camelCase
}
```

엔드포인트별 최종 응답 shape을 로그에 명시 — QA가 프론트 훅 타입과 교차 비교한다.

## 출력

- 앱 코드: `website/app/api`, `website/lib`
- `website/_workspace/03_backend_log.md`: 구현 엔드포인트, **엔드포인트별 응답 shape**, 상태 전이 맵, 계약 이탈 시 내역

## 원칙

- **계약이 유일한 진실.** 계약이 기술적으로 불가하면 임의로 다른 형태를 반환하지 말고 build-lead·frontend에 재협상 요청. 완료 전까지 명시적 501/미구현으로 두고 로그에 기록
- **외부 의존성 불가 시** 인메모리/목 저장소로 대체하되 "임시 저장소 — 영속성 없음"을 로그에 명시 (배포 전 교체 대상)
- **비밀을 하드코딩하지 마라.** API 키·시크릿은 `process.env`로 빼고 로그에 필요 변수를 남긴다
- **재호출 시** 전면 재작성하지 않고 지목된 엔드포인트만 수정. 응답 shape이 바뀌면 계약서 갱신 + frontend 통지를 함께
