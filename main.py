from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Нужно для работы с сессиями

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Здесь позже добавим обработку входа
        return redirect(url_for('home'))
    return render_template("login.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Здесь позже добавим обработку регистрации
        return redirect(url_for('login'))
    return render_template("register.html")

if __name__ == "__main__":
    app.run(debug=True)