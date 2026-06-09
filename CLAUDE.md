# test1 — Flask + Claude Chat 앱

## 응답 규칙
매 응답 마지막에 아래 형식으로 토큰 추정치를 출력할 것:
```
📊 추정 컨텍스트: ~XX,XXX 토큰 / 200K (약 X%)
```

## 개요
사용자가 입력한 메시지를 Claude API로 전달하고 응답을 화면에 출력하는 단순 웹 채팅 앱.

## 디렉토리 구조
```
test1/
├── app.py                  # Flask 서버 + Claude API 호출
├── CLAUDE.md               # 이 문서
└── templates/
    └── index.html          # 프론트엔드 UI
```

## 기술 스택
- **백엔드**: Python / Flask 3.x
- **Claude 호출**: `proot-distro` Alpine 컨테이너 안에서 `claude-code-linux-arm64-musl` 바이너리를 subprocess로 실행
  - API 키 불필요 — 이미 로그인된 Claude Code 세션 인증 재사용
- **프론트엔드**: 순수 HTML/CSS/JS (프레임워크 없음)

## 주요 파일 설명

### app.py
- `GET /` — index.html 렌더링
- `POST /chat` — JSON `{ "message": "..." }` 수신 → `claude -p` 호출 → `{ "reply": "..." }` 반환
- subprocess 호출 방식: `proot-distro login alpine --bind ~/:/root -- <musl_bin> -p <message>`
- 타임아웃 120초

### templates/index.html
- 입력창 (`<textarea>`) — 메시지 작성
- **전송** 버튼 + `Ctrl+Enter` 단축키로 전송
- **지우기** 버튼으로 입/출력 초기화
- 출력창 — Claude 응답 표시 (read-only textarea)
- 응답 대기 중 버튼 비활성화, 오류 시 빨간색 표시

## 실행 방법

```bash
cd ~/test1
export ANTHROPIC_API_KEY="sk-ant-..."
python app.py
```

브라우저에서 `http://localhost:5000` 접속.

## 설치된 패키지 (Termux 환경)
```
flask
requests
proot
proot-distro (Alpine 컨테이너)
patchelf
@anthropic-ai/claude-code-linux-arm64-musl  (npm global, --force)
@anthropic-ai/claude-code-linux-arm64       (npm global, --force, 미사용)
```

## Termux에서 `claude -p` subprocess 실행 문제 해결 경위

### 문제
Flask에서 `subprocess.run(["claude", "-p", ...])` 호출 시 `[Errno 8] Exec format error` 발생.

### 원인 분석
1. `/usr/bin/claude` → `claude.exe` 는 shebang 없는 500바이트 셸 스크립트(에러 출력 후 종료)
2. Python `execve`는 shebang/ELF magic이 없으면 실패 (bash는 직접 읽어 실행하지만 execve는 불가)
3. `bash -lc "claude -p ..."` 도 동일하게 스크립트 내용 자체가 "native binary not installed" 에러
4. `cli-wrapper.cjs` 도 `linux-arm64-android` 플랫폼 미지원으로 거부
5. `@anthropic-ai/claude-code-linux-arm64-android` npm 패키지 자체가 존재하지 않음
6. glibc 바이너리(`linux-arm64`)는 `/lib/ld-linux-aarch64.so.1` 없어서 실행 불가
7. musl 바이너리(`linux-arm64-musl`)는 `/lib/ld-musl-aarch64.so.1` 없어서 실행 불가

### 해결책
`proot-distro`로 Alpine Linux(musl 기반) 컨테이너를 구축하고, musl 빌드 claude 바이너리를 그 안에서 실행.
홈 디렉토리를 `/root`로 바인딩해 기존 Claude Code 로그인 세션 인증을 공유.

```bash
proot-distro install alpine
proot-distro login alpine --bind ~/:/root -- \
  /data/data/com.termux/files/usr/lib/node_modules/@anthropic-ai/claude-code-linux-arm64-musl/claude \
  -p "메시지"
```

## 실행 방법

```bash
cd ~/test1
python app.py &
```

브라우저에서 `http://localhost:5000` 접속. API 키 불필요.

## 작업 이력
| 날짜       | 내용 |
|------------|------|
| 2026-06-09 | test1 폴더 생성 |
| 2026-06-09 | Flask 앱 및 HTML 템플릿 구현 |
| 2026-06-09 | Termux 환경 패키지 이슈로 anthropic SDK → requests 직접 호출로 변경 |
| 2026-06-09 | claude CLI subprocess 호출 방식으로 전환 시도 → Exec format error 문제 발생 |
| 2026-06-09 | proot-distro Alpine + musl 바이너리 방식으로 최종 해결, API 키 불필요 |
