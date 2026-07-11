from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Настройка базы данных SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Модель Notes
class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    subtitle = db.Column(db.String(100), nullable=True)  # добавим позже
    text = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Notes('{self.title}', '{self.subtitle}')"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        subtitle = request.form.get('subtitle')
        content = request.form.get('content')
        if title and content:
            # Сохраняем запись в базу данных
            new_note = Notes(title=title, subtitle=subtitle, text=content)
            db.session.add(new_note)
            db.session.commit()
        return redirect(url_for('notes'))
    
    # GET запрос – получаем все записи из БД
    all_notes = Notes.query.all()
    return render_template('notes.html', entries=all_notes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)