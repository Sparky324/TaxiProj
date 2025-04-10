from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Нужно для работы с сессиями

DATABASE = 'users.db'


# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Функция для инициализации базы данных (создание таблицы users и trips)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            destination TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()


# Инициализация базы данных
init_db()


@app.route("/")
def home():
    # Если пользователь вошел в систему, передаем его имя в шаблон
    if 'user_id' in session:
        return render_template("index.html", username=session['username'])
    return render_template("index.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        conn = get_db_connection()
        # Попробуем найти пользователя по имени или email
        user = conn.execute('''
            SELECT * FROM users WHERE username = ? OR email = ?
        ''', (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            # Сохраняем информацию о пользователе в сессии
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('home'))
        else:
            flash('Неверное имя пользователя или пароль.')

    return render_template("login.html")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверим, что все поля заполнены
        if not username or not email or not password:
            flash('Пожалуйста, заполните все поля!')
            return redirect(url_for('register'))

        # Хэшируем пароль
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password)
                VALUES (?, ?, ?)
            ''', (username, email, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем или email уже существует!')
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Регистрация прошла успешно! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route("/account", methods=['GET', 'POST'])
def account():
    if 'user_id' not in session:
        flash("Пожалуйста, войдите в систему.")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Получаем данные пользователя
    conn = get_db_connection()
    user = conn.execute('''
        SELECT * FROM users WHERE id = ?
    ''', (user_id,)).fetchone()

    # Получаем историю поездок
    trips = conn.execute('''
        SELECT * FROM trips WHERE user_id = ?
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template("account.html", user=user, trips=trips)


@app.route("/logout")
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
