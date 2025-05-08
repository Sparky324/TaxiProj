from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

DATABASE = 'users.db'


# Функция для подключения к базе данных
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Функция для инициализации базы данных
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Создание таблицы users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

    # Создание таблицы trips
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            destination TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Создание таблицы drivers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            middle_name TEXT,
            citizenship TEXT NOT NULL,
            phone TEXT NOT NULL,
            car_number TEXT NOT NULL,
            car_model TEXT NOT NULL,
            car_color TEXT NOT NULL,
            status TEXT DEFAULT 'free'
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER,
            user_id INTEGER,
            driver_id INTEGER,
            status TEXT
        );
    """)

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

        user = conn.execute('''
            SELECT * FROM users WHERE username = ? OR email = ?
        ''', (username_or_email, username_or_email)).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['is_admin'] = user['is_admin']
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
        name = request.form['name']

        if not username or not email or not password:
            flash('Пожалуйста, заполните все поля!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password, name)
                VALUES (?, ?, ?, ?)
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


@app.route("/admin", methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session or not session.get('is_admin', False):
        flash("У вас нет прав для доступа к этой странице.")
        return redirect(url_for('home'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form['middle_name']
        citizenship = request.form['citizenship']
        phone = request.form['phone']
        car_number = request.form['car_number']
        car_model = request.form['car_model']
        car_color = request.form['car_color']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO drivers (first_name, last_name, middle_name, citizenship, phone, car_number, car_model, car_color)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, middle_name, citizenship, phone, car_number, car_model, car_color))
        conn.commit()
        conn.close()

        flash("Водитель успешно добавлен!")
        return redirect(url_for('admin'))

    return render_template("admin.html")


@app.route("/logout")
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect(url_for('home'))


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


@app.route("/change")
def change():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    return render_template("change.html", user_id=user_id)


@app.route('/find_car', methods=['POST'])
def find_car():
    # Получаем данные из формы или сессии
    user_id = session.get('user_id')  # или другой способ получения данных о пользователе

    # Ищем первого свободного водителя в базе данных
    conn = get_db_connection()
    driver = conn.execute("SELECT * FROM drivers WHERE status = 'free' LIMIT 1").fetchone()

    if driver:
        # Генерируем уникальный ID для заказа
        order_id = random.randint(1000, 9999)

        # Обновляем статус водителя на "занят"
        conn.execute("UPDATE drivers SET status = 'busy' WHERE id = ?", (driver['id'],))
        conn.commit()

        # Сохраняем информацию о заказе (пока заглушка)
        conn.execute("INSERT INTO orders (order_id, user_id, driver_id, status) VALUES (?, ?, ?, ?)",
                     (order_id, user_id, driver['id'], 'pending'))
        conn.commit()

        # Переадресуем на страницу заказа
        return redirect(url_for('order', order_id=order_id))

    return "Свободных водителей нет", 404


@app.route('/order/<int:order_id>')
def order(order_id):
    # Получаем информацию о заказе
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()

    if not order:
        return "Заказ не найден", 404

    driver = conn.execute("SELECT * FROM drivers WHERE id = ?", (order['driver_id'],)).fetchone()
    if not driver:
        return "Водитель не найден", 404

    # Время прибытия (заглушка: 5 минут)
    arrival_time = 5

    return render_template('order.html', order=order, driver=driver, arrival_time=arrival_time)



if __name__ == "__main__":
    app.run(debug=True)
