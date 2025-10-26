from flask import Flask, render_template, request, jsonify
import urllib.parse
from typing import Dict, List, Tuple
import os

app = Flask(__name__)

def extract_path(url: str) -> str:
    """Извлекает путь из URL (без протокола и домена)"""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        path = parsed.path
        
        if not path:
            return "/"
        
        if not path.startswith('/'):
            path = '/' + path
            
        return path
    except Exception:
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
