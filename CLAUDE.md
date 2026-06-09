# s10e_media_node — 통합 Flask 서버

## 응답 규칙 (Claude에게)
- 매 응답 마지막에 아래 형식으로 표기할 것:
  `📊 ~XX,XXX/200K/X%  |  chat.md: X,XXX bytes`
- 작업 중 확인 질문 금지 — 판단이 필요하면 스스로 결정하고 실행. 막히면 결과 보고 후 대안 제시.
- 장기메모리 저장은 사용자가 기억해라고 명시할 때만.

---

## 프로젝트 개요
YouTube MP3 다운로더 + Claude 채팅을 하나의 Flask 앱으로 통합한 서버.
원격 기기(Android Termux)에서 runit 서비스로 상시 실행.

---

## 환경 정보

| 항목 | 값 |
|------|----|
| 기기 (로컬) | 192.168.0.11 — Flask + Claude (port 5000) |
| 기기 (원격) | 192.168.0.10 / 공인 118.32.140.85 |
| SSH 접속 | `sshpass -p rladhksrb1 ssh -o StrictHostKeyChecking=no -p 8022 u0_a216@118.32.140.85` |
| GitHub 레포 | https://github.com/wkkimsgs-hue/testbot1 |
| Flask 포트 | 8080 |
| 서비스 이름 | testbot1-flask (runit) |

---

## 디렉토리 구조
```
s10e_media_node/
├── run.py                        # 진입점
├── requirements.txt
├── CLAUDE.md                     # 이 파일
├── chat.md                       # /chat, /api 엔드포인트 사용법
├── config/
│   └── settings.env              # 환경변수 (DISCORD_TOKEN, FLASK_PORT 등)
├── app/
│   ├── web/
│   │   ├── routes.py             # Flask 라우트 (미디어 + Claude 통합)
│   │   └── templates/
│   │       ├── index.html        # YouTube 다운로더 UI
│   │       └── claude.html       # Claude 채팅 UI
│   ├── downloader/
│   │   └── core.py               # yt-dlp MP3 다운로드 로직
│   ├── discord_bot/
│   │   └── bot.py                # Discord 봇 (/mp3, !mp3 커맨드)
│   └── common/
│       └── config.py             # 공통 설정 (포트, 경로 등)
├── downloads/                    # MP3 저장 폴더
└── logs/                         # 로그
```

---

## 라우트

| 경로 | 메서드 | 설명 |
|------|--------|------|
| / | GET | YouTube 다운로더 UI |
| /claude | GET | Claude 채팅 UI |
| /download | POST | YouTube MP3 다운로드 시작 |
| /status/\<job_id\> | GET | 다운로드 작업 상태 조회 |
| /files/\<filename\> | GET | MP3 파일 다운로드 |
| /files/\<filename\> | DELETE | MP3 파일 삭제 |
| /chat | POST | Claude 채팅 (UI용, JSON: {message}) |
| /api | POST | Claude API (봇용, JSON: {msg} or {message}) |

---

## Claude 호출 구조

```
ask_claude(message)
  └─ subprocess: proot-distro login alpine --bind ~/:/root
       └─ /data/.../claude-code-linux-arm64-musl/claude -p <message>
```

- **인증**: ~/.claude/.credentials.json (로컬 기기에서 복사, Claude Code 세션 공유)
- **타임아웃**: 120초

### Claude 바이너리 관련 배경
Termux에서 `execve`는 shebang/ELF 없이 실행 불가 → proot-distro Alpine(musl) 환경에서 실행.
glibc 바이너리는 ld-linux 없어 불가 → musl 빌드만 동작.

---

## 서비스 관리 (runit)

```bash
sv status  $PREFIX/var/service/testbot1-flask   # 상태 확인
sv restart $PREFIX/var/service/testbot1-flask   # 재시작
sv stop    $PREFIX/var/service/testbot1-flask   # 중지
sv start   $PREFIX/var/service/testbot1-flask   # 시작
```

- 서비스 파일: `$PREFIX/var/service/testbot1-flask/run`
- 로그: ~/logs/testbot1-flask/ (svlogd 자동 로테이션)
- Termux 재시작 시 자동 복구: ~/.bashrc에 runsvdir 등록됨

---

## 메신저봇 연동

| 기기 | 봇 파일 | 연동 서버 | 반응 방 |
|------|---------|-----------|---------|
| 로컬(0.11) | /sdcard/chatbot/BotData/testbot1/... | 0.11:5000/api | 대장간2 |
| 원격(0.10) | /storage/emulated/0/msgbot/Bots/testbot1/testbot1.js | 0.11:5000/api | 대장간3, 김완규 |

※ 원격 기기 testbot1.js는 현재 로컬 기기(0.11:5000)를 호출 중. 원격 서버(0.10:8080)로 변경 가능.

---

## Git 관리

```bash
# 원격 기기에서 (GIT_DIR 지정 필요)
export GIT_DIR=/storage/emulated/0/msgbot/Bots/testbot1/.git
export GIT_WORK_TREE=/storage/emulated/0/msgbot/Bots/testbot1
git pull origin main
```

---

## 작업 이력

| 날짜 | 내용 |
|------|------|
| 2026-06-09 | 로컬 기기에 Flask + Claude Chat 앱 구축 |
| 2026-06-09 | proot-distro Alpine + musl 바이너리로 Claude 호출 문제 해결 |
| 2026-06-10 | GitHub 레포 생성 (testbot1), 코드 푸시 |
| 2026-06-10 | 원격 기기에 proot-distro + Alpine + npm + claude 설치 |
| 2026-06-10 | runit 서비스 등록, 상시 실행 설정 |
| 2026-06-10 | s10e_media_node(YouTube봇)와 Claude 채팅 서버 통합 (port 8080) |
| 2026-06-10 | 공인IP(118.32.140.85:8022) SSH 접속 확인 |
