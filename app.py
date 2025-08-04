from flask import Flask, request, jsonify, render_template, redirect
from sqlalchemy import create_engine, text
import os
import pandas as pd

app = Flask(__name__)

# Получение URL базы данных от Render
db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)

# Создание таблицы, если её нет
with engine.connect() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS records (id SERIAL PRIMARY KEY, data TEXT)"))

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Загрузка файла
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return "Файл не выбран", 400

    ext = file.filename.split('.')[-1].lower()
    try:
        if ext == 'csv':
            df = pd.read_csv(file)
        elif ext == 'xlsx':
            df = pd.read_excel(file)
        elif ext == 'json':
            df = pd.read_json(file)
        elif ext == 'txt':
            content = file.read().decode('utf-8')
            df = pd.DataFrame({'data': content.splitlines()})
        else:
            return "Неподдерживаемый формат", 400

        if 'data' not in df.columns:
            df['data'] = df.astype(str).agg(' '.join, axis=1)

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM records"))
            for row in df['data']:
                conn.execute(text("INSERT INTO records (data) VALUES (:data)"), {"data": row})
        return redirect("/")
    except Exception as e:
        return f"Ошибка при обработке файла: {e}", 500

# Поиск
@app.route('/search')
def search():
    query = request.args.get('q', '')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT data FROM records WHERE data ILIKE :q"), {"q": f"%{query}%"})
        results = [row[0] for row in result]
    return jsonify(results)

# Запуск Flask на нужном порту для Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
