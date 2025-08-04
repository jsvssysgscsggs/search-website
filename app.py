from flask import Flask, request, jsonify, render_template
from sqlalchemy import create_engine, text
import os
import pandas as pd

app = Flask(__name__)

db_url = os.environ.get("DATABASE_URL")  # Render подставит эту переменную автоматически
engine = create_engine(db_url)

with engine.connect() as conn:
    conn.execute(text("CREATE TABLE IF NOT EXISTS records (id SERIAL PRIMARY KEY, data TEXT)"))

@app.route('/')
def index():
    return render_template('index.html')

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

        # Если нет колонки data, объединяем все колонки в строку
        if 'data' not in df.columns:
            df['data'] = df.astype(str).agg(' '.join, axis=1)

        with engine.begin() as conn:
            conn.execute(text("DELETE FROM records"))
            for row in df['data']:
                conn.execute(text("INSERT INTO records (data) VALUES (:data)"), {"data": row})
        return "Файл загружен и данные сохранены", 200
    except Exception as e:
        return f"Ошибка при обработке файла: {e}", 500

@app.route('/search')
def search():
    query = request.args.get('q', '')
    with engine.connect() as conn:
        result = conn.execute(text("SELECT data FROM records WHERE data ILIKE :q"), {"q": f"%{query}%"})
        results = [row[0] for row in result]
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)