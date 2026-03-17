"""
Веб-приложение Proxy Manager
"""
from flask import Flask, render_template, request, jsonify
import asyncio
import json
from datetime import datetime

from proxy_loader import ProxyLoader
from proxy_checker import ProxyChecker
from proxy_manager import ProxyManager
from logger import setup_logger

app = Flask(__name__)
logger = setup_logger(__name__)

# Глобальные объекты
loader = ProxyLoader()
checker = ProxyChecker()
manager = ProxyManager()


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Статус приложения"""
    return jsonify({
        'status': 'ok',
        'loaded_proxies': len(loader.get_all_proxies()),
        'checked_proxies': len(manager.proxies),
        'working_proxies': len(manager.get_working_proxies())
    })


@app.route('/api/load-proxies', methods=['POST'])
def load_proxies():
    """Загрузить прокси"""
    data = request.json
    source = data.get('source', 'both')
    
    try:
        if source == 'file' or source == 'both':
            file_proxies = loader.load_from_file()
        else:
            file_proxies = []
        
        if source == 'api' or source == 'both':
            api_proxies = asyncio.run(loader.load_from_api())
        else:
            api_proxies = []
        
        total = len(loader.get_all_proxies())
        
        return jsonify({
            'success': True,
            'file_count': len(file_proxies),
            'api_count': len(api_proxies),
            'total': total
        })
    except Exception as e:
        logger.error(f"Ошибка при загрузке: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/check-proxies', methods=['POST'])
def check_proxies_endpoint():
    """Проверить прокси"""
    proxies = loader.get_all_proxies()
    
    if not proxies:
        return jsonify({'success': False, 'error': 'Нет прокси для проверки'}), 400
    
    try:
        results = asyncio.run(checker.check_multiple(proxies))
        manager.add_results(results)
        
        working = len(manager.get_working_proxies())
        success_rate = (working / len(results) * 100) if results else 0
        
        return jsonify({
            'success': True,
            'total': len(results),
            'working': working,
            'failed': len(results) - working,
            'success_rate': round(success_rate, 1)
        })
    except Exception as e:
        logger.error(f"Ошибка при проверке: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/best-proxy')
def best_proxy():
    """Получить лучший прокси"""
    if not manager.proxies:
        return jsonify({'success': False, 'error': 'Прокси не проверены'}), 400
    
    best = manager.get_best_proxy()
    
    if best:
        return jsonify({
            'success': True,
            'proxy': best.proxy,
            'ping': round(best.response_time, 2),
            'status': 'working'
        })
    else:
        return jsonify({'success': False, 'error': 'Нет рабочих прокси'}), 400


@app.route('/api/top-proxies/<int:count>')
def top_proxies(count):
    """Получить топ прокси"""
    if not manager.proxies:
        return jsonify({'success': False, 'error': 'Прокси не проверены'}), 400
    
    top = manager.get_top_proxies(count)
    
    proxies_data = [
        {
            'proxy': p.proxy,
            'ping': round(p.response_time, 2),
            'status': 'working'
        }
        for p in top
    ]
    
    return jsonify({
        'success': True,
        'count': len(proxies_data),
        'proxies': proxies_data
    })


@app.route('/api/statistics')
def statistics():
    """Получить статистику"""
    if not manager.proxies:
        return jsonify({'success': False, 'error': 'Данные отсутствуют'}), 400
    
    stats = manager.get_statistics()
    
    return jsonify({
        'success': True,
        'total': stats['total'],
        'working': stats['working'],
        'failed': stats['not_working'],
        'success_rate': round(stats['success_rate'], 1),
        'avg_ping': round(stats['avg_response_time'], 2),
        'best_proxy': stats['best_proxy'],
        'best_ping': round(stats['best_response_time'], 2)
    })


@app.route('/api/save-results', methods=['POST'])
def save_results():
    """Сохранить результаты"""
    if not manager.proxies:
        return jsonify({'success': False, 'error': 'Нет результатов'}), 400
    
    try:
        manager.save_results()
        return jsonify({'success': True, 'message': 'Результаты сохранены'})
    except Exception as e:
        logger.error(f"Ошибка при сохранении: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400


if __name__ == '__main__':
    logger.info("🌐 Веб-приложение запущено")
    app.run(debug=True, host='0.0.0.0', port=5000)
