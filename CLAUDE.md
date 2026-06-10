# testbot1 — KakaoTalk 메신저봇R 매크로

## 개요
`testbot1.js`는 KakaoTalk 메시지를 받아 [s10e-media-node](https://github.com/wkkimsgs-hue/s10e-media-node) Flask 서버의
`/api` 엔드포인트로 전달하고, Claude(자비스)의 응답을 다시 채팅방에 보내는 메신저봇R 매크로.

서버 측 코드(Flask 앱, Claude 호출, DB 로깅/개입 로직 등)는 모두 `s10e-media-node` 레포에 있음.
이 레포에는 `testbot1.js` + 문서만 있음.

## 메신저봇R API 레퍼런스
`messengerbot_api_guide.txt` — Api/Bridge/Bot/Device/FileStream/Log/Utils 등 레거시 API 전체 정리.
새 기능 추가/수정 시 이 파일을 먼저 참고할 것 (Bridge에는 reload/compile 없음 등 주의사항 포함).

## 배포 위치
- 서버(원본): `~/testbot1` (이 GitHub 레포)
- 폰 배포 경로: `/storage/emulated/0/msgbot/Bots/testbot1/testbot1.js` (메신저봇R이 로드)

## 동작

### 1. 일반 메시지
- `room`(방 이름), `msg`(내용), `sender`(화자)를 JSON으로 묶어 `http://127.0.0.1:8080/api`(s10e-media-node)에 POST.
- 응답의 `reply`가 있으면 채팅방에 전송. `reply`가 빈 문자열이면 아무것도 보내지 않음(서버의 활동량 임계치 로직에 의한 침묵).
- `error`가 있으면 `[오류] ...` 형식으로 전송.
- **반응 방 제한 없음** — 봇이 로드된 모든 방에서 동작 (2026-06-10, 기존 "대장간3"/"김완규" 화이트리스트 제거됨).
- `/api` 호출 중 예외 발생 시 `http://127.0.0.1:8080/report_error`로 에러 보고 (s10e-media-node의 `logs/client_errors.log`에 기록, 자비스가 세션 시작 시 확인/처리).

### 2. "재시작" 명령
- 메시지가 정확히 "재시작"이면 `Api.reload(scriptName)`을 호출해 봇 스크립트를 리로드 시도.
- 성공 시 "재시작했습니다.", 실패 시 `[재시작 실패] <에러>`를 전송.
- (2026-06-10) 기존 `Bridge.reload()`는 존재하지 않는 함수(TypeError 발생)였음 — `Api.reload(scriptName)`으로 수정 완료.
  단, "재시작" 자체가 스크립트 리로드 기능이라 코드 수정 후 첫 적용은 메신저봇R 앱에서 수동 재컴파일 필요.

## 서버 연동 상세
`room`/`sender`를 함께 보내면 서버(`s10e-media-node`)에서:
- 메시지를 `chat_logs`에 기록하고, 최근 5분간 해당 방의 전체 발화수를 계산.
- "쟈비스"/"자비스" 호명 시 무조건 응답.
- 발화수가 임계치(5) 미만이면 빈 응답(봇 침묵).
- 임계치 이상이면 최근 5개 메시지를 묶어 Claude에게 "대화 개입" 프롬프트로 질의 후 응답.

상세 로직은 `s10e-media-node` 레포의 `CLAUDE.md` / `docs/api.md` 참고.

## Git 관리
- origin: `https://github.com/wkkimsgs-hue/testbot1.git`
- 작업 흐름: 로컬에서 `testbot1.js` 수정 → 커밋/푸시 → 서버(`~/testbot1` 또는 폰 경로)에서 `git pull` (또는 `git fetch && git reset --hard origin/main`) → 폰 배포 경로에 반영 후 메신저봇R에서 "재시작" 또는 수동 리로드.

## 작업 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-10 | testbot1.js를 `127.0.0.1:8080/api` 호출로 전환 (기존 `192.168.0.10:5000/api`에서 변경) |
| 2026-06-10 | `room`/`sender` 필드를 `/api` 요청에 포함하도록 수정 |
| 2026-06-10 | "쟈비스"/"자비스" 호명 시 항상 응답하는 로직은 서버(`s10e-media-node`)의 `/api`에서 처리하도록 구현 (이 레포 변경 없음) |
| 2026-06-10 | 반응 방 화이트리스트(대장간3, 김완규) 제거 — 모든 방에서 동작 |
| 2026-06-10 | "재시작" 명령 추가 (`Bridge.reload()`, API 시그니처 미확인) |
| 2026-06-10 | `/api` 호출 예외 발생 시 `/report_error`로 에러 보고하는 로직 추가 |
| 2026-06-10 | "재시작" 명령 수정 — 존재하지 않는 `Bridge.reload()` 대신 `Api.reload(scriptName)` 사용 |
| 2026-06-10 | 메신저봇R API 레퍼런스(`messengerbot_api_guide.txt`) 추가 |
