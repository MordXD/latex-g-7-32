from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import os
import subprocess
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'latex-editor-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compile_latex_safe():
    """Безопасная компиляция LaTeX с обработкой различных сценариев"""
    try:
        # Сначала пробуем базовую компиляцию
        result = subprocess.run([
            'pdflatex', 
            '-interaction=nonstopmode',
            '-output-directory=.',
            'main.tex'
        ], capture_output=True, text=True, cwd='.', timeout=60)
        
        return result
        
    except subprocess.TimeoutExpired:
        logger.error("Таймаут компиляции (60 секунд)")
        raise
    except FileNotFoundError:
        logger.error("pdflatex не найден в системе")
        raise
    except Exception as e:
        logger.error(f"Исключение при компиляции: {str(e)}")
        raise

class LatexFileHandler(FileSystemEventHandler):
    def __init__(self, socketio_instance):
        self.socketio = socketio_instance
        self.last_modified = 0
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        if event.src_path.endswith('main.tex'):
            current_time = time.time()
            # Предотвращаем множественные срабатывания
            if current_time - self.last_modified > 1:
                self.last_modified = current_time
                logger.info(f"Файл {event.src_path} изменен, запускаем компиляцию")
                threading.Thread(target=self.compile_latex).start()
    
    def compile_latex(self):
        try:
            result = compile_latex_safe()
            
            # Проверяем результат компиляции
            if result.returncode == 0:
                logger.info("Компиляция успешна")
                self.socketio.emit('compilation_success', {
                    'message': 'PDF обновлен',
                    'warnings': result.stdout if result.stdout else None
                })
            else:
                # Даже при ошибках пытаемся найти PDF
                if os.path.exists('main.pdf'):
                    logger.warning(f"Компиляция с предупреждениями: {result.stderr}")
                    self.socketio.emit('compilation_warning', {
                        'message': 'PDF создан с предупреждениями',
                        'warnings': result.stderr,
                        'output': result.stdout
                    })
                else:
                    logger.error(f"Ошибка компиляции: {result.stderr}")
                    self.socketio.emit('compilation_error', {
                        'message': 'Ошибка компиляции',
                        'error': result.stderr,
                        'output': result.stdout
                    })
                    
        except subprocess.TimeoutExpired:
            logger.error("Таймаут компиляции (60 секунд)")
            self.socketio.emit('compilation_error', {
                'message': 'Таймаут компиляции',
                'error': 'Компиляция заняла слишком много времени (более 60 секунд)'
            })
        except FileNotFoundError:
            logger.error("pdflatex не найден в системе")
            self.socketio.emit('compilation_error', {
                'message': 'pdflatex не найден',
                'error': 'Убедитесь, что LaTeX установлен и pdflatex доступен в PATH'
            })
        except Exception as e:
            logger.error(f"Исключение при компиляции: {str(e)}")
            self.socketio.emit('compilation_error', {
                'message': 'Ошибка компиляции',
                'error': str(e)
            })

# Инициализация наблюдателя файлов
file_handler = LatexFileHandler(socketio)
observer = Observer()
observer.schedule(file_handler, path='.', recursive=False)
observer.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/load_file')
def load_file():
    try:
        with open('main.tex', 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'success': True, 'content': content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save_file', methods=['POST'])
def save_file():
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        with open('main.tex', 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'message': 'Файл сохранен'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/pdf')
def get_pdf():
    try:
        if os.path.exists('main.pdf'):
            return send_file('main.pdf', as_attachment=False, mimetype='application/pdf')
        else:
            return jsonify({'error': 'PDF файл не найден'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@app.route('/api/compile', methods=['POST'])
def manual_compile():
    try:
        result = compile_latex_safe()
        
        # Проверяем результат
        if result.returncode == 0:
            return jsonify({
                'success': True, 
                'message': 'Компиляция успешна',
                'warnings': result.stdout if result.stdout else None
            })
        else:
            # Проверяем, создался ли PDF несмотря на ошибки
            if os.path.exists('main.pdf'):
                return jsonify({
                    'success': True,
                    'message': 'PDF создан с предупреждениями',
                    'warnings': result.stderr,
                    'output': result.stdout
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': result.stderr,
                    'output': result.stdout
                })
                
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False, 
            'error': 'Таймаут компиляции (60 секунд)'
        })
    except FileNotFoundError:
        return jsonify({
            'success': False, 
            'error': 'pdflatex не найден. Убедитесь, что LaTeX установлен.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@socketio.on('connect')
def handle_connect():
    logger.info('Клиент подключен')
    emit('connected', {'message': 'Подключение установлено'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Клиент отключен')

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 