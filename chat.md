# Claude 채팅 엔드포인트 사용법

## /chat — 웹 UI용

**요청**
```
POST /chat
Content-Type: application/json

{ message: 안녕 }
```

**응답**
```json
{ reply: 안녕하세요! 무엇을 도와드릴까요? }
```

---

## /api — 메신저봇 연동용

msg / message 필드명 모두 허용. ?format=text로 plain text 응답 가능.

**요청 (JSON)**
```
POST /api
Content-Type: application/json

{ msg: 1+1은? }
```

**요청 (plain text 응답)**
```
POST /api?format=text
Content-Type: application/json

{ msg: 안녕 }
```

**응답 예시**
```json
{ reply: 2 }
```

---

## Claude 호출 구조
```
Flask /chat, /api
  └─ ask_claude(message)
       └─ subprocess: proot-distro login alpine --bind ~/:/root
            └─ claude-code-linux-arm64-musl -p <message>
```

- 타임아웃: 120초
- 인증: ~/.claude/.credentials.json (Claude Code 세션 공유)
- 오류 시: { error: ... } 반환
