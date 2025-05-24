from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = '1bc56986ef1b4c88a237d73aa6745897'

DATABASE = 'database/users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            f_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            payment_method TEXT DEFAULT 'cash',
            is_admin BOOLEAN DEFAULT 0
        )
    ''')

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
            car_type TEXT NOT NULL,
            status TEXT DEFAULT 'free'
        );
    """)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            order_id    INTEGER PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            driver_id   INTEGER NOT NULL,
            status      TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            start_time  TEXT    NOT NULL,
            end_time    TEXT    NOT NULL,
            origin      TEXT    NOT NULL,
            destination TEXT    NOT NULL,
            wait_time   INTEGER NOT NULL,
            FOREIGN KEY (user_id)   REFERENCES users(id),
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        );
    ''')

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS driver_ratings (
            driver_id INTEGER NOT NULL,
            rate INTEGER NOT NULL,
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        );
    """)

    conn.commit()
    conn.close()


init_db()


@app.route("/")
def home():
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
        f_name = request.form['f_name']
        phone = request.form['phone']

        if not username or not email or not password:
            flash('Пожалуйста, заполните все поля!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (username, email, password, f_name, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, hashed_password, f_name, phone))
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
        car_type = request.form['car_type']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO drivers (first_name, last_name, middle_name, citizenship, phone, car_number, car_model, car_color, car_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (first_name, last_name, middle_name, citizenship, phone, car_number, car_model, car_color, car_type))
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


@app.route("/account")
def account():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    orders = conn.execute('''
        SELECT o.*, d.first_name, d.last_name, d.car_model, d.car_number 
          FROM orders o
          JOIN drivers d ON d.id = o.driver_id
         WHERE o.user_id = ?
         ORDER BY o.date DESC, o.start_time DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template("account.html", user=user, orders=orders)


@app.route("/update_payment_method", methods=['POST'])
def update_payment_method():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    payment_method = request.form.get('payment_method')
    if payment_method not in ('cash', 'card'):
        flash("Неверный способ оплаты")
        return redirect(url_for('account'))

    conn = get_db_connection()
    conn.execute(
      "UPDATE users SET payment_method = ? WHERE id = ?",
      (payment_method, session['user_id'])
    )
    conn.commit()
    conn.close()

    flash("Способ оплаты успешно обновлен!")
    return redirect(url_for('account'))


@app.route("/change", methods=['GET', 'POST'])
def change():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()

    if request.method == 'POST':
        new_username = request.form.get('username').strip()
        new_email    = request.form.get('email').strip()
        new_phone    = request.form.get('phone').strip()
        new_name     = request.form.get('full_name').strip()

        # Проверяем на уникальность username, email и phone
        exists = conn.execute(
            "SELECT id FROM users WHERE (username = ? OR email = ? OR phone = ?) AND id != ?",
            (new_username, new_email, new_phone, user_id)
        ).fetchone()
        if exists:
            flash("Имя пользователя, email или телефон уже заняты.", "error")

            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.close()
            return render_template("change.html", user=user)

        conn.execute("""
            UPDATE users
               SET username = ?, email = ?, phone = ?, f_name = ?
             WHERE id = ?
        """, (new_username, new_email, new_phone, new_name, user_id))
        conn.commit()
        conn.close()

        flash("Данные успешно обновлены!", "success")
        return redirect(url_for('account'))

    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return render_template("change.html", user=user)



@app.route('/find_car', methods=['POST'])
def find_car():
    user_id = session['user_id']
    conn = get_db_connection()
    car_type = request.form.get('carType')
    driver = conn.execute("""
            SELECT * FROM drivers 
            WHERE status = 'free' AND car_type = ? 
            LIMIT 1
        """, (car_type,)).fetchone()

    if not driver:
        flash("Свободных водителей нет.")
        return redirect(url_for('home'))

    order_id = random.randint(1000, 9999)
    now = datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    start_str = now.strftime('%H:%M:%S')

    origin = request.form.get('pointA', '')
    destination = request.form.get('pointB', '')

    if not origin or not destination:
        flash("Поля Пункт А и Пункт Б должны быть заполнены.")
        return redirect(url_for('home'))

    wait_time = 5

    conn.execute("UPDATE drivers SET status = 'busy' WHERE id = ?", (driver['id'],))

    conn.execute('''
        INSERT INTO orders 
          (order_id,user_id,driver_id,status,date,start_time,end_time,origin,destination,wait_time)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    ''', (order_id, user_id, driver['id'], 'В процессе',
          date_str, start_str, "", origin, destination, wait_time))
    conn.commit()
    conn.close()

    return redirect(url_for('order', order_id=order_id))


@app.route('/order/<int:order_id>')
def order(order_id):
    conn = get_db_connection()
    order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()

    if not order:
        return "Заказ не найден", 404

    driver = conn.execute("SELECT * FROM drivers WHERE id = ?", (order['driver_id'],)).fetchone()
    if not driver:
        return "Водитель не найден", 404

    arrival_time = 5

    row = conn.execute(
        """
        SELECT AVG(rate) AS avg_rate
          FROM (
            SELECT rate
              FROM driver_ratings
             WHERE driver_id = ?
             ORDER BY rowid DESC
             LIMIT 50
          )
        """,
        (driver['id'],)
    ).fetchone()
    avg_rating = row['avg_rate'] if row and row['avg_rate'] is not None else None

    return render_template('order.html', order=order, driver=driver, arrival_time=arrival_time, avg_rating=avg_rating)


@app.route('/finish_trip/<int:order_id>', methods=['POST'])
def finish_trip(order_id):
    now = datetime.now()
    end_str = now.strftime('%H:%M:%S')

    conn = get_db_connection()

    conn.execute('''
      UPDATE orders 
         SET status = 'Завершена', end_time = ?
       WHERE order_id = ?
    ''', (end_str, order_id))
    conn.commit()

    driver_id = conn.execute('SELECT driver_id FROM orders WHERE order_id = ?', (order_id,)).fetchone()['driver_id']
    conn.execute("UPDATE drivers SET status = 'free' WHERE id = ?", (driver_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('end_order', order_id=order_id))


@app.route('/end_order/<int:order_id>', methods=['GET', 'POST'])
def end_order(order_id):
    if request.method == 'POST':
        rate = request.form.get('rate')

        if rate is None or int(rate) < 1 or int(rate) > 5:
            flash("Пожалуйста, выберите корректную оценку от 1 до 5.")
            return redirect(url_for('end_order', order_id=order_id))

        conn = get_db_connection()

        driver_id = conn.execute('SELECT driver_id FROM orders WHERE order_id = ?', (order_id,)).fetchone()['driver_id']
        conn.execute('''
            INSERT INTO driver_ratings (driver_id, rate)
            VALUES (?, ?)
        ''', (driver_id, rate))
        conn.commit()
        conn.close()

        flash("Спасибо за вашу оценку!")
        return redirect(url_for('home'))

    return render_template('end_order.html', order_id=order_id)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

