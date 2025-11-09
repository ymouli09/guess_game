from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import database as db

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

db.init_db()

rooms = {}   # runtime cache: room_id -> {players:{A:sid,B:sid}}

def check_guess(secret, guess):
    correct = sum(1 for i in range(4) if secret[i] == guess[i])
    partial = sum(min(secret.count(d), guess.count(d)) for d in set(guess)) - correct
    return correct, partial

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("create_room")
def create_room():
    gid = db.create_game()
    rooms[gid] = {"players":{"A":request.sid}}
    join_room(gid)
    emit("room_created", {"room":gid,"role":"A"})

@socketio.on("join_room")
def join_room_event(data):
    gid = data["room"]
    game = db.get_game(gid)
    if not game:
        emit("error",{"msg":"Room not found"}); return
    if gid not in rooms: rooms[gid]={"players":{}}
    if "B" in rooms[gid]["players"]:
        emit("error",{"msg":"Room full"}); return
    rooms[gid]["players"]["B"]=request.sid
    join_room(gid)
    emit("room_joined",{"room":gid,"role":"B"})
    socketio.emit("both_joined",room=gid)
    send_state(gid)

@socketio.on("set_secret")
def set_secret(data):
    gid,role,secret = data["room"],data["role"],data["secret"]
    db.set_secret(gid,role,secret)
    send_state(gid)

@socketio.on("make_guess")
def make_guess(data):
    gid,role,guess = data["room"],data["role"],data["guess"]
    game = db.get_game(gid)
    if not game:
        emit("error",{"msg":"Invalid room"}); return
    _,a_secret,b_secret,turn,winner = game
    if winner:
        emit("error",{"msg":"Game finished"}); return
    if turn!=role:
        emit("error",{"msg":"Not your turn"}); return

    opponent_secret = b_secret if role=="A" else a_secret
    if not opponent_secret:
        emit("error",{"msg":"Opponent hasn't set secret"}); return

    correct,partial = check_guess(opponent_secret,guess)
    db.save_guess(gid,role,guess,correct,partial)
    if correct==4:
        db.update_turn(gid,winner=role)
    else:
        next_turn="B" if role=="A" else "A"
        db.update_turn(gid,turn=next_turn)
    send_state(gid)

def send_state(gid):
    game=db.get_game(gid)
    if not game: return
    guesses=db.get_guesses(gid)
    _,a_secret,b_secret,turn,winner=game
    socketio.emit("state_update",{
        "room":gid,
        "turn":turn,
        "winner":winner,
        "guesses":[{"player":g[0],"guess":g[1],"correct":g[2],"partial":g[3]} for g in guesses]
    },room=gid)

@socketio.on("disconnect")
def handle_disconnect():
    for gid,g in list(rooms.items()):
        if request.sid in g["players"].values():
            socketio.emit("player_left",room=gid)
            del rooms[gid]; break

if __name__=="__main__":
    socketio.run(app,host="0.0.0.0",port=5000)
