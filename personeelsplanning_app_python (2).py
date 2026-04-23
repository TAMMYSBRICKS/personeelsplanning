# 🚀 ADVANCED PERSONEELSPLANNING APP (DEPLOY READY - RENDER)
# -----------------------------------------------------
# 🌐 DEPLOY INSTRUCTIES (MAAK ONLINE LINK)
#
# 1. Maak GitHub repo (bijv. personeelsplanning)
# 2. Upload DIT bestand als: app.py
#
# 3. Voeg BESTANDEN TOE:
#
# requirements.txt
# flask
# gunicorn
#
# Procfile (zonder extensie):
# web: gunicorn app:app
#
# 4. Ga naar https://render.com
# 5. New → Web Service → connect GitHub
# 6. Settings:
#    Build command: pip install -r requirements.txt
#    Start command: gunicorn app:app
#
# 7. Klik DEPLOY → je krijgt live link 🔥
#
# -----------------------------------------------------
# 📱 APP (PWA + APK)
# - Open link op telefoon → “Toevoegen aan beginscherm”
# - Of gebruik https://www.pwabuilder.com → APK downloaden
# -----------------------------------------------------

from flask import Flask, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"
DB = "database.db"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT,
        wage REAL
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        status TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        date TEXT,
        start TEXT,
        end TEXT
    )""")

    # default admin login
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username,password,role,wage) VALUES (?,?,?,?)",
                  ("admin","admin","admin",0))

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect(DB)

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[3]
            return redirect("/dashboard")
        return "Login fout"

    return """
    <h2>Login</h2>
    <form method='post'>
    Gebruiker: <input name='username'><br>
    Wachtwoord: <input name='password'><br>
    <button>Login</button>
    </form>
    """

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")
    return redirect("/admin" if session["role"]=="admin" else "/employee")

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    conn = get_db()
    c = conn.cursor()

    users = c.execute("SELECT id,username,wage FROM users WHERE role='employee'").fetchall()
    shifts = c.execute("SELECT s.id,u.username,s.date,s.start,s.end FROM shifts s JOIN users u ON s.user_id=u.id").fetchall()

    conn.close()

    users_html = "<br>".join([f"{u[1]} (€{u[2]})" for u in users])
    shifts_html = "<br>".join([f"{s[1]} - {s[2]} {s[3]}-{s[4]}" for s in shifts])

    return f"""
    <h1>Admin</h1>

    <h3>Medewerker toevoegen</h3>
    <form method='post' action='/add_user'>
    Naam: <input name='username'><br>
    Wachtwoord: <input name='password'><br>
    Uurloon: <input name='wage'><br>
    <button>Toevoegen</button>
    </form>

    <h3>Dienst maken</h3>
    <form method='post' action='/add_shift'>
    User ID: <input name='user_id'><br>
    Datum: <input name='date'><br>
    Start: <input name='start'><br>
    Eind: <input name='end'><br>
    <button>Opslaan</button>
    </form>

    <h3>Medewerkers</h3>
    {users_html}

    <h3>Rooster</h3>
    {shifts_html}
    """

@app.route("/add_user", methods=["POST"])
def add_user():
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO users (username,password,role,wage) VALUES (?,?,?,?)",
              (request.form["username"], request.form["password"], "employee", float(request.form["wage"])))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/add_shift", methods=["POST"])
def add_shift():
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO shifts (user_id,date,start,end) VALUES (?,?,?,?)",
              (request.form["user_id"], request.form["date"], request.form["start"], request.form["end"]))
    conn.commit()
    conn.close()
    return redirect("/admin")

# ---------------- EMPLOYEE ----------------
@app.route("/employee")
def employee():
    conn = get_db()
    c = conn.cursor()

    shifts = c.execute("SELECT date,start,end FROM shifts WHERE user_id=?", (session["user_id"],)).fetchall()

    total_hours = 0
    for s in shifts:
        start = int(s[1].split(":")[0])
        end = int(s[2].split(":")[0])
        total_hours += (end - start)

    wage = c.execute("SELECT wage FROM users WHERE id=?", (session["user_id"],)).fetchone()[0]
    salary = total_hours * wage

    conn.close()

    shifts_html = "<br>".join([f"{s[0]} {s[1]}-{s[2]}" for s in shifts])

    return f"""
    <h1>Mijn rooster</h1>
    {shifts_html}

    <h3>Totaal uren: {total_hours}</h3>
    <h3>Salaris: €{salary}</h3>
    """

# ---------------- RUN ----------------
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port, debug=False)
