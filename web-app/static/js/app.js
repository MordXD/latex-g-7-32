class LatexEditor {
    constructor() {
        this.editor = document.getElementById('editor');
        this.pdfViewer = document.getElementById('pdfViewer');
        this.pdfPlaceholder = document.getElementById('pdfPlaceholder');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusDot = this.statusIndicator.querySelector('.status-dot');
        this.statusText = this.statusIndicator.querySelector('.status-text');
        this.notifications = document.getElementById('notifications');
        
        this.saveTimeout = null;
        this.isCompiling = false;
        this.lastSavedContent = '';
        
        this.initializeSocketIO();
        this.initializeEditor();
        this.initializeButtons();
        this.initializeResizer();
        this.loadFile();
    }
    
    initializeSocketIO() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Подключено к серверу');
            this.updateStatus('ready', 'Подключен');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Отключено от сервера');
            this.updateStatus('error', 'Отключен');
        });
        
        this.socket.on('compilation_success', (data) => {
            this.isCompiling = false;
            this.updateStatus('ready', 'PDF обновлен');
            this.refreshPdf();
            
            if (data.warnings) {
                this.showNotification('success', 'Компиляция завершена', 'PDF успешно обновлен (есть предупреждения)');
                console.log('Предупреждения компиляции:', data.warnings);
            } else {
                this.showNotification('success', 'Компиляция завершена', 'PDF успешно обновлен');
            }
        });
        
        this.socket.on('compilation_warning', (data) => {
            this.isCompiling = false;
            this.updateStatus('warning', 'PDF создан с предупреждениями');
            this.refreshPdf();
            this.showNotification('warning', 'Компиляция с предупреждениями', 
                'PDF создан, но есть предупреждения. Проверьте консоль для деталей.');
            console.log('Предупреждения компиляции:', data.warnings);
            console.log('Вывод компиляции:', data.output);
        });
        
        this.socket.on('compilation_error', (data) => {
            this.isCompiling = false;
            this.updateStatus('error', 'Ошибка компиляции');
            this.showNotification('error', 'Ошибка компиляции', 
                'Не удалось создать PDF. Проверьте консоль для деталей.');
            console.error('Ошибка компиляции:', data.error);
            if (data.output) {
                console.log('Вывод компиляции:', data.output);
            }
        });
    }
    
    initializeEditor() {
        // Автосохранение при изменении
        this.editor.addEventListener('input', () => {
            this.updateDocumentStats();
            this.updateCursorPosition();
            this.autoSave();
        });
        
        // Обновление позиции курсора
        this.editor.addEventListener('selectionchange', () => {
            this.updateCursorPosition();
        });
        
        this.editor.addEventListener('keyup', () => {
            this.updateCursorPosition();
        });
        
        this.editor.addEventListener('click', () => {
            this.updateCursorPosition();
        });
        
        // Горячие клавиши
        this.editor.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveFile();
            }
            
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.compileLatex();
            }
        });
        
        // Поддержка табуляции
        this.editor.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();
                const start = this.editor.selectionStart;
                const end = this.editor.selectionEnd;
                
                this.editor.value = this.editor.value.substring(0, start) + 
                                  '    ' + 
                                  this.editor.value.substring(end);
                
                this.editor.selectionStart = this.editor.selectionEnd = start + 4;
            }
        });
    }
    
    initializeButtons() {
        // Кнопка сохранения
        document.getElementById('saveBtn').addEventListener('click', () => {
            this.saveFile();
        });
        
        // Кнопка компиляции
        document.getElementById('compileBtn').addEventListener('click', () => {
            this.compileLatex();
        });
        
        // Кнопка обновления PDF
        document.getElementById('refreshPdf').addEventListener('click', () => {
            this.refreshPdf();
        });
        
        // Кнопка скачивания PDF
        document.getElementById('downloadPdf').addEventListener('click', () => {
            this.downloadPdf();
        });
        
        // Переключатель переноса строк
        document.getElementById('wrapToggle').addEventListener('click', () => {
            this.toggleWordWrap();
        });
    }
    
    initializeResizer() {
        const resizer = document.getElementById('resizer');
        const editorPanel = document.querySelector('.editor-panel');
        const pdfPanel = document.querySelector('.pdf-panel');
        
        let isResizing = false;
        
        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
        });
        
        function handleMouseMove(e) {
            if (!isResizing) return;
            
            const containerWidth = document.querySelector('.main-content').offsetWidth;
            const newEditorWidth = (e.clientX / containerWidth) * 100;
            
            if (newEditorWidth > 20 && newEditorWidth < 80) {
                editorPanel.style.flex = `0 0 ${newEditorWidth}%`;
                pdfPanel.style.flex = `0 0 ${100 - newEditorWidth}%`;
            }
        }
        
        function handleMouseUp() {
            isResizing = false;
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    }
    
    async loadFile() {
        try {
            this.updateStatus('loading', 'Загрузка файла...');
            const response = await fetch('/api/load_file');
            const data = await response.json();
            
            if (data.success) {
                this.editor.value = data.content;
                this.lastSavedContent = data.content;
                this.updateDocumentStats();
                this.updateCursorPosition();
                this.updateStatus('ready', 'Файл загружен');
                this.hidePdfPlaceholder();
            } else {
                this.showNotification('error', 'Ошибка загрузки', data.error);
                this.updateStatus('error', 'Ошибка загрузки');
            }
        } catch (error) {
            this.showNotification('error', 'Ошибка загрузки', error.message);
            this.updateStatus('error', 'Ошибка загрузки');
        }
    }
    
    async saveFile() {
        try {
            const content = this.editor.value;
            
            if (content === this.lastSavedContent) {
                this.showNotification('success', 'Файл актуален', 'Изменений для сохранения нет');
                return;
            }
            
            this.updateStatus('saving', 'Сохранение...');
            
            const response = await fetch('/api/save_file', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.lastSavedContent = content;
                this.updateStatus('ready', 'Файл сохранен');
                this.showNotification('success', 'Файл сохранен', 'main.tex успешно сохранен');
            } else {
                this.showNotification('error', 'Ошибка сохранения', data.error);
                this.updateStatus('error', 'Ошибка сохранения');
            }
        } catch (error) {
            this.showNotification('error', 'Ошибка сохранения', error.message);
            this.updateStatus('error', 'Ошибка сохранения');
        }
    }
    
    autoSave() {
        if (this.saveTimeout) {
            clearTimeout(this.saveTimeout);
        }
        
        this.saveTimeout = setTimeout(() => {
            this.saveFile();
        }, 2000); // Автосохранение через 2 секунды после последнего изменения
    }
    
    async compileLatex() {
        if (this.isCompiling) {
            this.showNotification('warning', 'Компиляция в процессе', 'Дождитесь завершения текущей компиляции');
            return;
        }
        
        try {
            this.isCompiling = true;
            this.updateStatus('compiling', 'Компиляция...');
            
            // Сначала сохраняем файл
            await this.saveFile();
            
            const response = await fetch('/api/compile', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.warnings) {
                    this.updateStatus('warning', 'PDF создан с предупреждениями');
                    this.showNotification('warning', 'Компиляция с предупреждениями', 
                        'PDF создан, но есть предупреждения. Проверьте консоль для деталей.');
                    console.log('Предупреждения:', data.warnings);
                    if (data.output) {
                        console.log('Вывод компиляции:', data.output);
                    }
                } else {
                    this.updateStatus('ready', 'Компиляция завершена');
                    this.showNotification('success', 'Компиляция завершена', 'PDF успешно создан');
                }
                this.refreshPdf();
            } else {
                this.updateStatus('error', 'Ошибка компиляции');
                this.showNotification('error', 'Ошибка компиляции', 
                    'Не удалось создать PDF. Проверьте консоль для деталей.');
                console.error('Ошибка компиляции:', data.error);
                if (data.output) {
                    console.log('Вывод компиляции:', data.output);
                }
            }
        } catch (error) {
            this.updateStatus('error', 'Ошибка компиляции');
            this.showNotification('error', 'Ошибка компиляции', error.message);
        } finally {
            this.isCompiling = false;
        }
    }
    
    refreshPdf() {
        const timestamp = new Date().getTime();
        this.pdfViewer.src = `/api/pdf?t=${timestamp}`;
        this.hidePdfPlaceholder();
    }
    
    downloadPdf() {
        window.open('/api/pdf', '_blank');
    }
    
    toggleWordWrap() {
        const currentWrap = this.editor.style.whiteSpace;
        if (currentWrap === 'pre-wrap') {
            this.editor.style.whiteSpace = 'pre';
            this.showNotification('success', 'Перенос строк отключен', '');
        } else {
            this.editor.style.whiteSpace = 'pre-wrap';
            this.showNotification('success', 'Перенос строк включен', '');
        }
    }
    
    updateStatus(type, message) {
        this.statusDot.className = 'status-dot';
        if (type !== 'ready') {
            this.statusDot.classList.add(type);
        }
        this.statusText.textContent = message;
    }
    
    updateDocumentStats() {
        const content = this.editor.value;
        const charCount = content.length;
        const lineCount = content.split('\n').length;
        
        document.getElementById('documentStats').textContent = 
            `${charCount} символов, ${lineCount} строк`;
    }
    
    updateCursorPosition() {
        const textarea = this.editor;
        const cursorPos = textarea.selectionStart;
        const textBeforeCursor = textarea.value.substring(0, cursorPos);
        const lines = textBeforeCursor.split('\n');
        const currentLine = lines.length;
        const currentColumn = lines[lines.length - 1].length + 1;
        
        document.getElementById('cursorPosition').textContent = 
            `Строка ${currentLine}, Столбец ${currentColumn}`;
    }
    
    hidePdfPlaceholder() {
        this.pdfPlaceholder.classList.add('hidden');
    }
    
    showPdfPlaceholder() {
        this.pdfPlaceholder.classList.remove('hidden');
    }
    
    showNotification(type, title, message) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        notification.innerHTML = `
            <div class="notification-title">${title}</div>
            ${message ? `<div class="notification-message">${message}</div>` : ''}
        `;
        
        this.notifications.appendChild(notification);
        
        // Автоматическое удаление уведомления (дольше для предупреждений и ошибок)
        const timeout = type === 'error' || type === 'warning' ? 10000 : 5000;
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, timeout);
        
        // Удаление по клику
        notification.addEventListener('click', () => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        });
    }
}

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    new LatexEditor();
});

// Предотвращение случайного закрытия страницы с несохраненными изменениями
window.addEventListener('beforeunload', (e) => {
    const editor = document.getElementById('editor');
    if (editor && editor.value !== editor.dataset.lastSaved) {
        e.preventDefault();
        e.returnValue = '';
    }
}); 