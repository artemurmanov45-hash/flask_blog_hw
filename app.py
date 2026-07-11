from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Словарь для хранения записей дневника (ключ - заголовок, значение - текст)
diary_entries = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/notes', methods=['GET', 'POST'])
def notes():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            diary_entries[title] = content
        # После добавления перенаправляем обратно на страницу дневника (GET)
        return redirect(url_for('notes'))
    # GET-запрос – просто показываем страницу с формой и записями
    return render_template('notes.html', entries=diary_entries)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)