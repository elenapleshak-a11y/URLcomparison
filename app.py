from flask import Flask, render_template, request, jsonify
import urllib.parse
from typing import Dict, List, Tuple
import os

app = Flask(__name__)

def extract_path(url: str) -> str:
    """Извлекает нормализованный путь из URL"""
    try:
        # Чистим URL
        url = url.strip()
        if not url:
            return None
            
        # Добавляем протокол если отсутствует
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        
        # Нормализуем путь
        if not path:
            path = "/"
        else:
            # Приводим к нижнему регистру
            path = path.lower()
            # Убираем конечный слеш (кроме корня)
            if path != '/' and path.endswith('/'):
                path = path.rstrip('/')
            # Добавляем начальный слеш если отсутствует
            if not path.startswith('/'):
                path = '/' + path
        
        return path
        
    except Exception as e:
        print(f"Ошибка обработки URL: {url} - {e}")
        return None

def compare_url_lists(old_urls_text: str, new_urls_text: str) -> Dict:
    """Сравнивает два списка URL"""
    
    # Разбиваем тексты на списки URL
    old_urls = [url.strip() for url in old_urls_text.split('\n') if url.strip()]
    new_urls = [url.strip() for url in new_urls_text.split('\n') if url.strip()]
    
    # Обрабатываем старый сайт
    old_supplement_to_url = {}
    for url in old_urls:
        supplement = extract_path(url)
        if supplement:
            old_supplement_to_url[supplement] = url
    
    # Обрабатываем новый сайт
    new_supplement_to_url = {}
    for url in new_urls:
        supplement = extract_path(url)
        if supplement:
            new_supplement_to_url[supplement] = url
    
    # Сравниваем
    old_supplements = set(old_supplement_to_url.keys())
    new_supplements = set(new_supplement_to_url.keys())
    
    common_supplements = old_supplements.intersection(new_supplements)
    only_in_old = old_supplements - new_supplements
    only_in_new = new_supplements - old_supplements
    
    # Формируем результаты
    results = {
        "статистика": {
            "всего_в_старом": len(old_urls),
            "всего_в_новом": len(new_urls),
            "одинаковые": len(common_supplements),
            "только_в_старом": len(only_in_old),
            "только_в_новом": len(only_in_new)
        },
        "одинаковые_URL": [
            {"старый": old_supplement_to_url[s], "новый": new_supplement_to_url[s], "путь": s}
            for s in common_supplements
        ],
        "только_в_старом": [
            {"url": old_supplement_to_url[s], "путь": s}
            for s in only_in_old
        ],
        "только_в_новом": [
            {"url": new_supplement_to_url[s], "путь": s}
            for s in only_in_new
        ]
    }
    
    return results

import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

def upload_to_google_sheets(results: Dict, old_urls: List[str], new_urls: List[str]):
    """Выгружает результаты в Google Sheets"""
    try:
        # Настройка доступа к Google Sheets (нужно будет настроить один раз)
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        # Создайте файл credentials.json с вашим API ключом
        creds = Credentials.from_service_account_file('credentials.json', scopes=scope)
        client = gspread.authorize(creds)
        
        # Создаем новую таблицу
        spreadsheet_name = f"URL Comparison {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        spreadsheet = client.create(spreadsheet_name)
        
        # Настройка общего доступа (опционально)
        spreadsheet.share(None, perm_type='anyone', role='writer')
        
        # Лист 1: Одинаковые URL
        worksheet1 = spreadsheet.get_worksheet(0)
        worksheet1.update_title("Одинаковые URL")
        worksheet1.update('A1', [['Старый URL', 'Новый URL', 'Путь']])
        
        same_data = []
        for item in results["одинаковые_URL"]:
            same_data.append([item["старый"], item["новый"], item["путь"]])
        if same_data:
            worksheet1.update('A2', same_data)
        
        # Лист 2: Только в старом
        worksheet2 = spreadsheet.add_worksheet(title="Только в старом", rows="1000", cols="3")
        worksheet2.update('A1', [['URL', 'Путь']])
        
        only_old_data = []
        for item in results["только_в_старом"]:
            only_old_data.append([item["url"], item["путь"]])
        if only_old_data:
            worksheet2.update('A2', only_old_data)
        
        # Лист 3: Только в новом
        worksheet3 = spreadsheet.add_worksheet(title="Только в новом", rows="1000", cols="3")
        worksheet3.update('A1', [['URL', 'Путь']])
        
        only_new_data = []
        for item in results["только_в_новом"]:
            only_new_data.append([item["url"], item["путь"]])
        if only_new_data:
            worksheet3.update('A2', only_new_data)
        
        return spreadsheet.url
        
    except Exception as e:
        print(f"Ошибка выгрузки в Google Sheets: {e}")
        return None

# Обновите функцию compare_url_lists - добавьте в возвращаемые данные полные списки
def compare_url_lists(old_urls_text: str, new_urls_text: str) -> Dict:
    """Сравнивает два списка URL"""
    
    # Разбиваем тексты на списки URL
    old_urls = [url.strip() for url in old_urls_text.split('\n') if url.strip()]
    new_urls = [url.strip() for url in new_urls_text.split('\n') if url.strip()]
    
    # Обрабатываем старый сайт
    old_supplement_to_url = {}
    old_url_to_supplement = {}
    for url in old_urls:
        supplement = extract_path(url)
        if supplement:
            old_supplement_to_url[supplement] = url
            old_url_to_supplement[url] = supplement
    
    # Обрабатываем новый сайт
    new_supplement_to_url = {}
    new_url_to_supplement = {}
    for url in new_urls:
        supplement = extract_path(url)
        if supplement:
            new_supplement_to_url[supplement] = url
            new_url_to_supplement[url] = supplement
    
    # Сравниваем
    old_supplements = set(old_supplement_to_url.keys())
    new_supplements = set(new_supplement_to_url.keys())
    
    common_supplements = old_supplements.intersection(new_supplements)
    only_in_old = old_supplements - new_supplements
    only_in_new = new_supplements - old_supplements
    
    # Формируем результаты
    results = {
        "статистика": {
            "всего_в_старом": len(old_urls),
            "всего_в_новом": len(new_urls),
            "одинаковые": len(common_supplements),
            "только_в_старом": len(only_in_old),
            "только_в_новом": len(only_in_new)
        },
        "одинаковые_URL": [
            {"старый": old_supplement_to_url[s], "новый": new_supplement_to_url[s], "путь": s}
            for s in common_supplements
        ],
        "только_в_старом": [
            {"url": old_supplement_to_url[s], "путь": s}
            for s in only_in_old
        ],
        "только_в_новом": [
            {"url": new_supplement_to_url[s], "путь": s}
            for s in only_in_new
        ],
        # Полные списки для выгрузки
        "полные_списки": {
            "старый_сайт": old_urls,
            "новый_сайт": new_urls
        }
    }
    
    return results

# Добавьте новый маршрут для выгрузки в Google Sheets
@app.route('/export-to-sheets', methods=['POST'])
def export_to_sheets():
    try:
        data = request.json
        old_urls = data.get('old_urls', '')
        new_urls = data.get('new_urls', '')
        
        results = compare_url_lists(old_urls, new_urls)
        sheet_url = upload_to_google_sheets(
            results, 
            results["полные_списки"]["старый_сайт"],
            results["полные_списки"]["новый_сайт"]
        )
        
        if sheet_url:
            return jsonify({
                "success": True,
                "sheet_url": sheet_url,
                "message": "Данные успешно выгружены в Google Sheets"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Не удалось выгрузить в Google Sheets"
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

from flask import send_file
import csv
import io

def create_csv_file(data, filename):
    """Создает CSV файл в памяти"""
    output = io.StringIO()
    writer = csv.writer(output)
    
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    return output

@app.route('/download-results', methods=['POST'])
def download_results():
    try:
        data = request.json
        old_urls = data.get('old_urls', '')
        new_urls = data.get('new_urls', '')
        
        results = compare_url_lists(old_urls, new_urls)
        
        # Создаем ZIP архив с результатами
        import zipfile
        import tempfile
        import os
        
        # Создаем временный файл
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, 'url_comparison_results.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Файл с одинаковыми URL
            same_data = [['Старый URL', 'Новый URL', 'Путь']]
            for item in results["одинаковые_URL"]:
                same_data.append([item["старый"], item["новый"], item["путь"]])
            
            same_csv = io.StringIO()
            csv.writer(same_csv).writerows(same_data)
            zipf.writestr('одинаковые_url.csv', same_csv.getvalue())
            
            # Файл с URL только в старом
            only_old_data = [['URL', 'Путь']]
            for item in results["только_в_старом"]:
                only_old_data.append([item["url"], item["путь"]])
            
            only_old_csv = io.StringIO()
            csv.writer(only_old_csv).writerows(only_old_data)
            zipf.writestr('только_в_старом.csv', only_old_csv.getvalue())
            
            # Файл с URL только в новом
            only_new_data = [['URL', 'Путь']]
            for item in results["только_в_новом"]:
                only_new_data.append([item["url"], item["путь"]])
            
            only_new_csv = io.StringIO()
            csv.writer(only_new_csv).writerows(only_new_data)
            zipf.writestr('только_в_новом.csv', only_new_csv.getvalue())
            
            # Полные списки URL
            full_old_data = [['URL старого сайта']] + [[url] for url in results["полные_списки"]["старый_сайт"]]
            full_new_data = [['URL нового сайта']] + [[url] for url in results["полные_списки"]["новый_сайт"]]
            
            full_old_csv = io.StringIO()
            csv.writer(full_old_csv).writerows(full_old_data)
            zipf.writestr('полный_список_старый_сайт.csv', full_old_csv.getvalue())
            
            full_new_csv = io.StringIO()
            csv.writer(full_new_csv).writerows(full_new_data)
            zipf.writestr('полный_список_новый_сайт.csv', full_new_csv.getvalue())
        
        return send_file(zip_path, 
                        as_attachment=True, 
                        download_name='url_comparison_results.zip',
                        mimetype='application/zip')
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare', methods=['POST'])
def compare():
    try:
        data = request.json
        old_urls = data.get('old_urls', '')
        new_urls = data.get('new_urls', '')
        
        results = compare_url_lists(old_urls, new_urls)
        
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
