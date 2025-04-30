from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import requests

app = Flask(__name__)
app.secret_key = 'f440b5015952421a8da7c24d297d120f'

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
            password TEXT NOT NULL
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

# Функция для получения адреса по координатам через Яндекс API
def get_address_from_coords(lat, lon):
    api_key = "ce095acd-05a3-4919-9cf4-7e64c641af28"  # Ваш ключ API
    url = f"https://geocode-maps.yandex.ru/v1/?apikey={api_key}&geocode={lon},{lat}&format=json"
    response = requests.get(url)
    data = response.json()

    try:
        address = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
        return address
    except KeyError:
        return None

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
        phone = request.form['phone']
        full_name = request.form['full_name']

        # Проверим, что все поля заполнены
        if not username or not email or not password:
            flash('Пожалуйста, заполните все поля!')
            return redirect(url_for('register'))

        # Хэшируем пароль
        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password, phone, full_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed_password, phone, full_name))
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

@app.route("/change")
def change():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    return render_template("change.html", user_id=user_id)

@app.route("/get_address", methods=['GET'])
def get_address():
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    address = get_address_from_coords(lat, lon)
    if address:
        return jsonify({'address': address})
    else:
        return jsonify({'address': 'Адрес не найден'}), 404

if __name__ == "__main__":
    app.run(debug=True)
