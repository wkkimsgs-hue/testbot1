# testbot1

KakaoTalk 메신저봇R 매크로 스크립트.

`testbot1.js`는 카카오톡 메시지를 받아 [s10e-media-node](https://github.com/wkkimsgs-hue/s10e-media-node)의
Flask 서버 `/api` 엔드포인트로 전달하고, Claude의 응답을 다시 채팅방에 보냅니다.

서버 측 코드(Flask 앱, Claude 호출 로직, API 스펙 등)는 모두 `s10e-media-node` 레포로 통합되었습니다.
