# 프레임워크별 라우트 탐색 전략

감지된 스택에 해당하는 섹션만 읽어라. 각 섹션은 (1) 라우트 등록 지점을 어디서 찾는지, (2) 파라미터·응답·인증을 어디서 읽는지를 담는다. 목표는 언제나 동일하다 — **전 엔드포인트 열거 + `파일:라인` 근거가 붙은 계약 추출**.

## 목차
- [Node.js — Express / Koa / Fastify](#nodejs)
- [Node.js — NestJS](#nestjs)
- [파일 기반 — Next.js / Nuxt / SvelteKit](#파일-기반)
- [Python — FastAPI](#fastapi)
- [Python — Flask](#flask)
- [Python — Django REST Framework](#django-rest)
- [Ruby on Rails](#rails)
- [Java/Kotlin — Spring](#spring)
- [Go — net/http / Gin / Echo / Chi](#go)
- [GraphQL / RPC (경계 판단)](#graphql-rpc)
- [프레임워크 미상 / 커스텀](#미상)

---

## <a id="nodejs"></a>Node.js — Express / Koa / Fastify
- **등록 지점**: `app.use(...)`, `router.get/post/put/patch/delete(...)`, `app.route(...)`. 부트스트랩(`app.js`, `server.js`, `index.js`)에서 시작해 `express.Router()` 인스턴스를 따라간다.
- **마운트 접두사**: `app.use('/api/v1', usersRouter)` → 그 라우터의 모든 경로에 `/api/v1` 접두사. 중첩 라우터는 접두사를 누적한다.
- **파라미터**: `req.params.x`(경로), `req.query.x`(쿼리), `req.body.x`(본문), `req.headers[...]`. 본문 스키마는 zod/joi/express-validator 미들웨어에서 읽는다.
- **응답**: `res.json(...)`, `res.send(...)`, `res.status(n).json(...)`.
- **인증**: 라우터/앱에 걸린 미들웨어(`router.use(authMiddleware)`, `app.get('/x', requireAuth, handler)`).
- Fastify: `fastify.route({method, url, schema, handler})` — `schema`에 요청/응답 JSON Schema가 명시적으로 있는 경우가 많다(추출에 최적).

## <a id="nestjs"></a>Node.js — NestJS
- **등록 지점**: `@Controller('prefix')` 클래스 + 메서드의 `@Get() @Post() @Put() @Patch() @Delete()` 데코레이터. 경로 = 컨트롤러 접두사 + 메서드 데코레이터 인자.
- **파라미터**: `@Param() @Query() @Body() @Headers()` 데코레이터. 본문 타입은 DTO 클래스(class-validator 데코레이터로 필수·제약 표시).
- **응답**: 메서드 리턴 타입 + `@ApiResponse`(Swagger 데코레이터가 있으면 상태코드·형태가 명시적).
- **인증**: `@UseGuards(AuthGuard)` — 클래스/메서드 레벨.

## <a id="파일-기반"></a>파일 기반 — Next.js / Nuxt / SvelteKit
- **등록 지점 = 디렉토리 구조.** 라우트 등록부가 없다. 파일 경로가 URL 경로다.
  - Next.js App Router: `app/**/route.ts`의 `export async function GET/POST/...`. 경로 = 폴더 구조, `[id]` = 동적 세그먼트.
  - Next.js Pages: `pages/api/**/*.ts`의 default export 핸들러.
  - Nuxt: `server/api/**/*.ts`, 파일명 접미사(`.get.ts`, `.post.ts`)가 메서드.
  - SvelteKit: `src/routes/**/+server.ts`의 `GET/POST/...` export.
- **파라미터**: 동적 세그먼트는 폴더명(`[id]`), 쿼리·본문은 핸들러 안 `request`/`searchParams`에서 읽는다.
- **인증**: 미들웨어(`middleware.ts`) 또는 핸들러 내 세션 검사.

## <a id="fastapi"></a>Python — FastAPI
- **등록 지점**: `@app.get/post/...` 또는 `@router.get/...`. `app.include_router(router, prefix='/api')`로 접두사 확인.
- **파라미터**: 함수 시그니처가 곧 스펙이다 — 경로 파라미터, `Query(...)`, `Body`, Pydantic 모델(요청 본문). 타입 힌트·기본값이 필수/선택·타입을 규정한다(추출에 최적).
- **응답**: `response_model=` 인자(명시적 응답 스키마) 또는 리턴 타입. 상태코드는 `status_code=`.
- **인증**: `Depends(get_current_user)` 등 의존성 주입.

## <a id="flask"></a>Python — Flask
- **등록 지점**: `@app.route('/x', methods=[...])` 또는 `@blueprint.route(...)`. `app.register_blueprint(bp, url_prefix='/api')`로 접두사 확인. `methods` 미지정이면 GET.
- **파라미터**: 경로는 `<int:id>` 컨버터, 쿼리는 `request.args`, 본문은 `request.get_json()` / `request.form`.
- **응답**: `return jsonify(...), status` 또는 `make_response`. Flask-RESTful은 `Resource` 클래스의 메서드가 곧 HTTP 메서드.
- **인증**: `@login_required`, `@jwt_required()` 등 데코레이터.

## <a id="django-rest"></a>Python — Django REST Framework
- **등록 지점**: `urls.py`의 `urlpatterns` + `router.register(...)`(ViewSet). ViewSet은 CRUD 액션이 표준 엔드포인트로 확장된다(list/create/retrieve/update/destroy).
- **파라미터**: URL 캡처 그룹(경로), `request.query_params`, serializer(요청/응답 필드·필수·검증).
- **응답**: serializer 클래스가 응답 형태다. `Response(serializer.data, status=...)`.
- **인증**: `permission_classes`, `authentication_classes`.

## <a id="rails"></a>Ruby on Rails
- **등록 지점**: `config/routes.rb` — `resources :x`(RESTful 7액션 확장), `get/post '...'`. `rails routes` 출력이 있으면 최적의 인벤토리다.
- **파라미터**: `params[:x]`(경로·쿼리 통합), 본문은 `strong_params`(`params.require(:x).permit(...)`)에 필드·필수 명시.
- **응답**: 컨트롤러 액션의 `render json:` + jbuilder/serializer 뷰.
- **인증**: `before_action :authenticate_user!`.

## <a id="spring"></a>Java/Kotlin — Spring
- **등록 지점**: `@RestController` + `@RequestMapping/@GetMapping/@PostMapping/...`. 클래스 레벨 `@RequestMapping('/api')`가 접두사.
- **파라미터**: `@PathVariable @RequestParam @RequestBody @RequestHeader`. 본문은 DTO 클래스(`@Valid` + bean validation 애노테이션으로 제약).
- **응답**: 리턴 타입(`ResponseEntity<T>`, DTO), `@ResponseStatus`. 상태코드는 `ResponseEntity.status(...)`.
- **인증**: Spring Security 설정(`SecurityFilterChain`) + `@PreAuthorize`.

## <a id="go"></a>Go — net/http / Gin / Echo / Chi
- **등록 지점**:
  - net/http: `http.HandleFunc('/x', ...)`, `mux.Handle(...)`.
  - Gin: `r.GET/POST/...('/x', handler)`, 그룹 `r.Group('/api')`.
  - Echo: `e.GET(...)`, 그룹 `e.Group('/api')`.
  - Chi: `r.Route('/x', ...)`, `r.Get(...)`.
- **파라미터**: 경로 파라미터(`c.Param('id')`, `chi.URLParam`), 쿼리(`c.Query`, `r.URL.Query()`), 본문(`c.ShouldBindJSON(&dto)` — 구조체 태그가 필드·필수).
- **응답**: `c.JSON(status, obj)`, `json.NewEncoder(w).Encode(...)`. 응답 구조체가 형태.
- **인증**: 미들웨어(`r.Use(AuthMiddleware)`, 그룹에 걸린 미들웨어).

## <a id="graphql-rpc"></a>GraphQL / RPC — 경계 판단
이 하네스는 REST 스타일 HTTP 엔드포인트 문서화에 최적화돼 있다. 대상이 다음이면 **doc-lead에 즉시 보고해 범위·전략을 재설계한다:**
- **GraphQL**: 단일 엔드포인트(`/graphql`) + 스키마/리졸버가 실제 API 표면. 엔드포인트 열거가 아니라 타입·쿼리·뮤테이션 추출이 필요 — 다른 접근이다.
- **gRPC/tRPC**: `.proto`·프로시저 정의가 계약. HTTP 라우트 열거로는 안 잡힌다.
REST와 혼재하면 REST 부분만 이 절차로 추출하고, 나머지는 "범위 밖 — 별도 접근 필요"로 명시한다.

## <a id="미상"></a>프레임워크 미상 / 커스텀
- HTTP 메서드 문자열(`'GET'`, `'POST'`)과 경로 패턴(`'/...'`)을 전역 grep해 라우팅 테이블·디스패처를 찾는다.
- 요청 객체에서 파라미터를 읽는 지점(`request.`, `req.`, 컨텍스트 객체)을 추적한다.
- 등록부를 못 찾으면 폴백을 선언하고("추출 모드: 제한적"), 확인된 핸들러만 레코드화한다. 커스텀 프레임워크 구조를 doc-lead에 보고해 사용자에게 라우트 정의 위치를 확인받는다.
