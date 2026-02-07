import asyncio
import re
import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Callable, Awaitable
from contextlib import contextmanager
from app.config import settings

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    def __init__(self):
        self.timeout = settings.LATEX_TIMEOUT

    @contextmanager
    def temporary_work_dir(self):
        """Создает изолированную временную директорию"""
        temp_dir = tempfile.mkdtemp(prefix="latex_worker_")
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_log_line(self, line: str) -> Optional[str]:
        """Парсит stdout pdflatex для извлечения прогресса"""
        # Поиск номеров страниц [1], [2]...
        page_match = re.search(r'\[(\d+)\]', line)
        if page_match:
            return f"Processing page {page_match.group(1)}..."
        
        # Ключевые сообщения
        if "Transcript written on" in line:
            return "Finalizing PDF..."
        if "LaTeX Warning:" in line:
            return f"Warning: {line.split('LaTeX Warning:')[1].strip()[:50]}..."
        if "! LaTeX Error:" in line:
            return f"Error: {line.split('! LaTeX Error:')[1].strip()[:50]}..."
            
        return None

    async def compile_latex_stream(
        self,
        content: str,
        work_dir: str,
        compiler_options: Dict[str, Any],
        progress_callback: Callable[[str], Awaitable[None]]
    ) -> Dict[str, Any]:
        """
        Компилирует LaTeX с асинхронным чтением логов
        """
        task_id = "stream" # Для логов
        
        # 1. Подготовка файлов
        main_file = Path(work_dir) / "main.tex"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Копируем стили если нужно (тут упрощено, предполагается наличие styles в image или volume)
        # В реальном K8s стили монтируются или скачиваются
        
        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            f"-output-directory={work_dir}",
            "main.tex"
        ]

        logger.info(f"Starting pdflatex stream in {work_dir}")
        
        # 2. Запуск процесса
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=work_dir
        )

        full_log = []
        
        # 3. Чтение stdout в реальном времени
        while True:
            line_bytes = await process.stdout.readline()
            if not line_bytes:
                break
            
            line = line_bytes.decode('utf-8', errors='replace').strip()
            full_log.append(line)
            
            # Парсинг и отправка прогресса
            status_msg = self._parse_log_line(line)
            if status_msg:
                await progress_callback(status_msg)

        await process.wait()
        
        success = (process.returncode == 0)
        pdf_path = Path(work_dir) / "main.pdf"
        log_path = Path(work_dir) / "main.log"

        return {
            "success": success and pdf_path.exists(),
            "pdf_path": str(pdf_path) if pdf_path.exists() else None,
            "log_path": str(log_path) if log_path.exists() else None,
            "full_log": "\n".join(full_log)
        }

latex_service = LaTeXCompiler()