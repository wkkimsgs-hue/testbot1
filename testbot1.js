const scriptName = "testbot1";

function response(room, msg, sender, isGroupChat, replier, imageDB, packageName) {
  if (msg.trim() === "재시작") {
    try {
      Bridge.reload();
      replier.reply("재시작했습니다.");
    } catch (e) {
      replier.reply("[재시작 실패] " + e.toString());
    }
    return;
  }

  try {
    var url = new java.net.URL("http://127.0.0.1:8080/api");
    var conn = url.openConnection();
    conn.setRequestMethod("POST");
    conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
    conn.setDoOutput(true);
    conn.setConnectTimeout(5000);
    conn.setReadTimeout(130000);

    var body = JSON.stringify({ msg: msg, room: room, sender: sender });
    var bytes = new java.lang.String(body).getBytes("UTF-8");
    conn.getOutputStream().write(bytes);

    var reader = new java.io.BufferedReader(
      new java.io.InputStreamReader(conn.getInputStream(), "UTF-8")
    );
    var sb = new java.lang.StringBuilder();
    var line;
    while ((line = reader.readLine()) !== null) {
      sb.append(line);
    }
    reader.close();

    var result = JSON.parse(sb.toString());
    if (result.reply) {
      replier.reply(result.reply);
    } else if (result.error) {
      replier.reply("[오류] " + result.error);
    }
  } catch (e) {
    var errMsg = e.toString();
    replier.reply("[오류] " + errMsg);
    try {
      var errConn = new java.net.URL("http://127.0.0.1:8080/report_error").openConnection();
      errConn.setRequestMethod("POST");
      errConn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
      errConn.setDoOutput(true);
      errConn.setConnectTimeout(5000);
      var errBody = JSON.stringify({ error: errMsg, room: room, sender: sender, msg: msg });
      errConn.getOutputStream().write(new java.lang.String(errBody).getBytes("UTF-8"));
      errConn.getInputStream();
    } catch (e2) {
      // 에러 보고 자체 실패는 무시
    }
  }
}

function onCreate(savedInstanceState, activity) {
  var textView = new android.widget.TextView(activity);
  textView.setText("Hello, World!");
  textView.setTextColor(android.graphics.Color.DKGRAY);
  activity.setContentView(textView);
}

function onStart(activity) {}
function onResume(activity) {}
function onPause(activity) {}
function onStop(activity) {}
