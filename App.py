from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this for production

# 🔧 Initialize DB
def init_db():
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        date TEXT,
                        time TEXT)''')
        # Add default admin
        c.execute("SELECT * FROM users WHERE username = 'admin'")
        if not c.fetchone():
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ('admin', 'admin123', 'admin'))
        conn.commit()

# 🏠 Home
@app.route('/')
def home():
    return render_template('login.html')

# 🔐 Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    with sqlite3.connect('attendance.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect('/admin' if user[3] == 'admin' else '/user')
    return render_template('login.html', error="Invalid credentials")

# 👤 User Dashboard
@app.route('/user')
def user():
    if 'role' in session and session['role'] == 'user':
        return render_template('user.html', username=session['username'])
    return redirect('/')

# ✅ Mark Attendance
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' in session:
        now = datetime.now()
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO attendance (user_id, date, time) VALUES (?, ?, ?)",
                      (session['user_id'], now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")))
            conn.commit()
        return render_template('user.html', success="Attendance marked!", username=session['username'])
    return redirect('/')

# 🧑‍💼 Admin Dashboard
@app.route('/admin')
def admin():
    if 'role' in session and session['role'] == 'admin':
        with sqlite3.connect('attendance.db') as conn:
            c = conn.cursor()
            c.execute('''SELECT users.username, attendance.date, attendance.time
                         FROM attendance
                         JOIN users ON users.id = attendance.user_id
                         ORDER BY attendance.id DESC''')
            records = c.fetchall()
        return render_template('admin.html', records=records)
    return redirect('/')

# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ▶️ Run App
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
