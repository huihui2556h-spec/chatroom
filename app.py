from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
# 允許跨域連線，並指定使用 eventlet 模式
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 紀錄線上使用者 { sid: {"username": str} }
clients = {}

@app.route("/")
def index():
    return render_template("index.html")

# 用戶連線時觸發
@socketio.on("connect")
def on_connect():
    clients[request.sid] = {"username": None}
    print(f"Client connected: {request.sid}")

# 用戶設定名稱（登入）
@socketio.on("set_name")
def on_set_name(data):
    username = data.get("username")
    clients[request.sid]["username"] = username
    # 廣播某人進入聊天室
    emit("status_message", {"msg": f"✨ {username} 進入了聊天室"}, broadcast=True)
    # 更新線上人數
    broadcast_user_count()

# 處理新訊息發送
@socketio.on("send_message")
def handle_message(data):
    username = clients.get(request.sid, {}).get("username", "匿名")
    emit("receive_message", {
        "username": username,
        "msg": data["msg"]
    }, broadcast=True)

# 處理「正在輸入」事件
@socketio.on("typing")
def handle_typing():
    username = clients.get(request.sid, {}).get("username", "匿名")
    # 告訴其他人誰在打字，不包含發送者自己
    emit("user_typing", {"username": username}, broadcast=True, include_self=False)

# 用戶離線時觸發
@socketio.on("disconnect")
def on_disconnect():
    info = clients.pop(request.sid, None)
    if info and info["username"]:
        emit("status_message", {"msg": f"👋 {info['username']} 離開了聊天室"}, broadcast=True)
        broadcast_user_count()
    print(f"Client disconnected: {request.sid}")

def broadcast_user_count():
    # 計算有設定名字的有效用戶
    count = len([c for c in clients.values() if c["username"]])
    emit("user_count", {"count": count}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)