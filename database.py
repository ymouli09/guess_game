import sqlite3, datetime, uuid

DB_NAME = "number_duel.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS games(
                    id TEXT PRIMARY KEY,
                    player_a_secret TEXT,
                    player_b_secret TEXT,
                    turn TEXT,
                    winner TEXT
                )""")
    c.execute("""CREATE TABLE IF NOT EXISTS guesses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT,
                    player TEXT,
                    guess TEXT,
                    correct INTEGER,
                    partial INTEGER,
                    ts TEXT
                )""")
    conn.commit()
    conn.close()

def create_game():
    gid = str(uuid.uuid4())[:6].upper()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO games(id,turn) VALUES(?,?)",(gid,"A"))
    conn.commit()
    conn.close()
    return gid

def set_secret(gid, player, secret):
    field = "player_a_secret" if player=="A" else "player_b_secret"
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(f"UPDATE games SET {field}=? WHERE id=?",(secret,gid))
    conn.commit(); conn.close()

def get_game(gid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id,player_a_secret,player_b_secret,turn,winner FROM games WHERE id=?",(gid,))
    g = c.fetchone()
    conn.close()
    return g

def save_guess(gid, player, guess, correct, partial):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO guesses(game_id,player,guess,correct,partial,ts)
                 VALUES(?,?,?,?,?,?)""",(gid,player,guess,correct,partial,datetime.datetime.now().isoformat()))
    conn.commit(); conn.close()

def update_turn(gid, turn=None, winner=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if winner:
        c.execute("UPDATE games SET winner=? WHERE id=?",(winner,gid))
    elif turn:
        c.execute("UPDATE games SET turn=? WHERE id=?",(turn,gid))
    conn.commit(); conn.close()

def get_guesses(gid):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT player,guess,correct,partial FROM guesses WHERE game_id=? ORDER BY id",(gid,))
    data = c.fetchall()
    conn.close()
    return data
