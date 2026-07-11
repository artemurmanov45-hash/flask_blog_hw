from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import bcrypt
from datetime import datetime, timedelta
import jwt
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # секретный ключ для сессий и JWT

# Настройка БД
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модель Notes (существующая)
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100), nullable=True)
    text = db.Column(db.Text, nullable=False)

# Новая модель Users
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # храним хэш
    token = db.Column(db.String(500), nullable=True)      # JWT токен
    token_expiry = db.Column(db.DateTime, nullable=True)  # срок действия токена

    def __repr__(self):
        return f"<User {self.username}>"

# Вспомогательная функция для генерации JWT
def generate_token(user_id):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)  # токен живёт 24 часа
    }
    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
    return token

# Проверка токена (декоратор или функция)
def verify_token(token):
    try:
        data = jwt.decode(token, app.secret_key, algorithms=['HS256'])
        return data['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Главная страница (перенаправляем на /home, если не авторизован)
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return redirect(url_for('home'))  # пока просто на /home

# Страница /home с кнопками
@app.route('/home')
def home():
    if 'user_id' in session:
        # Если пользователь уже авторизован, можно показать его имя
        user = Users.query.get(session['user_id'])
        return render_template('home.html', logged_in=True, username=user.username if user else None)
    return render_template('home.html', logged_in=False)

# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Проверка, что пользователь не существует
        existing_user = Users.query.filter((Users.username == username) | (Users.email == email)).first()
        if existing_user:
            return "Пользователь с таким именем или email уже существует", 400
        # Хэширование пароля
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = Users(username=username, email=email, password=hashed.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        # После регистрации перенаправляем на страницу входа
        return redirect(url_for('login'))
    return render_template('register.html')

# Страница логина
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if not user:
            return "Пользователь не найден", 400
        # Проверка пароля
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # Генерируем токен и сохраняем в сессию
            token = generate_token(user.id)
            user.token = token
            user.token_expiry = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()
            session['user_id'] = user.id
            session['token'] = token
            return redirect(url_for('home'))
        else:
            return "Неверный пароль", 400
    return render_template('login.html')

# Страница дневника (защищена – требуется авторизация)
@app.route('/notes')
def notes():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Проверка токена (можно дополнительно)
    token = session.get('token')
    if token:
        user_id = verify_token(token)
        if not user_id:
            # токен недействителен – очищаем сессию и редирект на логин
            session.clear()
            return redirect(url_for('login'))
    # Получаем записи из БД
    all_notes = Notes.query.all()
    return render_template('notes.html', entries=all_notes)

# (Опционально) Выход
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)