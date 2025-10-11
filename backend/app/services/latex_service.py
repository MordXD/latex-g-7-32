import os
import subprocess
import shutil
import tempfile
import uuid
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager

from app.models.compilation import CompilationStatus, CompilationResponse

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    def __init__(self):
        self.timeout = int(os.getenv("LATEX_TIMEOUT", "60"))
        self.output_dir = os.getenv("LATEX_OUTPUT_DIR", "pdf")
        self.work_dir = os.getenv("LATEX_WORK_DIR", "latex")

        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def check_pdflatex_available() -> bool:
        """Check if pdflatex is available in the system"""
        try:
            result = subprocess.run(
                ["pdflatex", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    @contextmanager
    def temporary_work_dir(self):
        """Create a temporary working directory for LaTeX compilation"""
        temp_dir = tempfile.mkdtemp(prefix="latex_compile_")
        try:
            yield temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def prepare_latex_file(self, content: str, work_dir: str, filename: str = "document.tex") -> str:
        """Prepare LaTeX file for compilation"""
        # Copy styles directory structure if working with main latex directory
        main_latex_dir = Path(self.work_dir)
        temp_work_dir = Path(work_dir)

        if main_latex_dir.exists():
            # Copy styles directory
            styles_src = main_latex_dir / "styles"
            if styles_src.exists():
                styles_dst = temp_work_dir / "styles"
                shutil.copytree(styles_src, styles_dst)

            # Copy images directory
            images_src = main_latex_dir / "images"
            if images_src.exists():
                images_dst = temp_work_dir / "images"
                shutil.copytree(images_src, images_dst)

            # Copy bibliography files
            for bib_file in main_latex_dir.glob("*.bib"):
                shutil.copy2(bib_file, temp_work_dir)

        # Write the main LaTeX file
        tex_file = temp_work_dir / filename
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return str(tex_file)

    def compile_latex_file(
        self,
        tex_file_path: str,
        output_dir: str,
        compiler_options: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str, str, str]:
        """
        Compile LaTeX file using pdflatex

        Returns:
            tuple: (success, stdout, stderr, pdf_path)
        """
        if compiler_options is None:
            compiler_options = {}

        tex_path = Path(tex_file_path)
        work_dir = tex_path.parent
        tex_name = tex_path.stem

        # Build pdflatex command
        cmd = ["pdflatex"]

        # Add compiler options
        if compiler_options.get("interaction"):
            cmd.extend(["-interaction", compiler_options["interaction"]])

        if compiler_options.get("shell_escape"):
            cmd.append("-shell-escape")

        if compiler_options.get("output_directory"):
            cmd.extend(["-output-directory", output_dir])
        else:
            cmd.extend(["-output-directory", output_dir])

        cmd.append(str(tex_path))

        logger.info(f"Running LaTeX compilation: {' '.join(cmd)}")

        try:
            # Run compilation
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            # Check if PDF was created
            pdf_path = Path(output_dir) / f"{tex_name}.pdf"
            pdf_exists = pdf_path.exists()

            success = result.returncode == 0 and pdf_exists

            logger.info(f"Compilation completed. Success: {success}, PDF exists: {pdf_exists}")

            return (
                success,
                result.stdout,
                result.stderr,
                str(pdf_path) if pdf_exists else ""
            )

        except subprocess.TimeoutExpired:
            error_msg = f"LaTeX compilation timed out after {self.timeout} seconds"
            logger.error(error_msg)
            return False, "", error_msg, ""

        except Exception as e:
            error_msg = f"LaTeX compilation failed: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg, ""

    def run_bibtex_if_needed(self, tex_file_path: str, output_dir: str) -> bool:
        """Run bibtex if bibliography is needed"""
        tex_path = Path(tex_file_path)
        work_dir = tex_path.parent
        tex_name = tex_path.stem
        aux_file = Path(output_dir) / f"{tex_name}.aux"

        # Check if there's a bibliography
        if not aux_file.exists():
            return True

        try:
            with open(aux_file, 'r', encoding='utf-8') as f:
                aux_content = f.read()
                if '\\bibdata{' not in aux_content:
                    return True  # No bibliography needed
        except Exception:
            return True

        # Run bibtex
        cmd = ["bibtex", f"{output_dir}/{tex_name}"]
        try:
            result = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Bibtex failed: {e}")
            return True  # Continue without bibtex

    def compile_latex_document(
        self,
        content: Optional[str] = None,
        file_path: Optional[str] = None,
        compiler_options: Optional[Dict[str, Any]] = None
    ) -> CompilationResponse:
        """
        Main method to compile a LaTeX document

        Args:
            content: LaTeX content as string
            file_path: Path to existing .tex file
            compiler_options: Additional options for pdflatex

        Returns:
            CompilationResponse with results
        """
        start_time = time.time()
        compilation_id = str(uuid.uuid4())

        # Validate input
        if not content and not file_path:
            return CompilationResponse(
                success=False,
                status=CompilationStatus.ERROR,
                message="Either content or file_path must be provided",
                compilation_time=time.time() - start_time,
                error="No input provided"
            )

        try:
            with self.temporary_work_dir() as work_dir:
                tex_file_path = ""

                # Prepare LaTeX file
                if content:
                    tex_file_path = self.prepare_latex_file(content, work_dir, "document.tex")
                elif file_path and Path(file_path).exists():
                    # Copy existing file and its dependencies
                    src_path = Path(file_path)
                    tex_file_path = self.prepare_latex_file(
                        src_path.read_text(encoding='utf-8'),
                        work_dir,
                        src_path.name
                    )
                else:
                    return CompilationResponse(
                        success=False,
                        status=CompilationStatus.ERROR,
                        message="Invalid file path provided",
                        compilation_time=time.time() - start_time,
                        error="File not found or content empty"
                    )

                # First compilation
                logger.info(f"Starting first compilation pass for {compilation_id}")
                success1, stdout1, stderr1, pdf_path1 = self.compile_latex_file(
                    tex_file_path, work_dir, compiler_options
                )

                # Check if bibtex is needed and run it
                if success1:
                    self.run_bibtex_if_needed(tex_file_path, work_dir)

                # Second compilation for proper references
                logger.info(f"Starting second compilation pass for {compilation_id}")
                success2, stdout2, stderr2, pdf_path2 = self.compile_latex_file(
                    tex_file_path, work_dir, compiler_options
                )

                # Third compilation for final PDF
                logger.info(f"Starting third compilation pass for {compilation_id}")
                success3, stdout3, stderr3, pdf_path3 = self.compile_latex_file(
                    tex_file_path, work_dir, compiler_options
                )

                # Combine all output
                total_stdout = stdout1 + stdout2 + stdout3
                total_stderr = stderr1 + stderr2 + stderr3

                final_success = success3 and Path(pdf_path3).exists()
                compilation_time = time.time() - start_time

                if final_success:
                    # Copy PDF to final output directory
                    final_pdf_name = f"{compilation_id}.pdf"
                    final_pdf_path = Path(self.output_dir) / final_pdf_name
                    shutil.copy2(pdf_path3, final_pdf_path)

                    # Create log file
                    log_file_path = Path(self.output_dir) / f"{compilation_id}.log"
                    with open(log_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"=== LaTeX Compilation Log for {compilation_id} ===\n")
                        f.write(f"Compilation time: {compilation_time:.2f} seconds\n")
                        f.write(f"Status: Success\n\n")
                        f.write("=== STDOUT ===\n")
                        f.write(total_stdout)
                        f.write("\n=== STDERR ===\n")
                        f.write(total_stderr)

                    return CompilationResponse(
                        success=True,
                        status=CompilationStatus.SUCCESS,
                        message="Compilation successful",
                        pdf_url=f"/pdf/{final_pdf_name}",
                        compilation_time=compilation_time,
                        warnings=total_stderr if total_stderr.strip() else None,
                        output=total_stdout,
                        log_file=f"/pdf/{final_pdf_name}.log"
                    )
                else:
                    # Create error log
                    log_file_path = Path(self.output_dir) / f"{compilation_id}_error.log"
                    with open(log_file_path, 'w', encoding='utf-8') as f:
                        f.write(f"=== LaTeX Compilation Error Log for {compilation_id} ===\n")
                        f.write(f"Compilation time: {compilation_time:.2f} seconds\n")
                        f.write(f"Status: Failed\n\n")
                        f.write("=== STDERR ===\n")
                        f.write(total_stderr)
                        f.write("\n=== STDOUT ===\n")
                        f.write(total_stdout)

                    return CompilationResponse(
                        success=False,
                        status=CompilationStatus.ERROR,
                        message="Compilation failed",
                        compilation_time=compilation_time,
                        error=total_stderr,
                        output=total_stdout,
                        log_file=f"/pdf/{compilation_id}_error.log"
                    )

        except Exception as e:
            logger.error(f"Unexpected error during compilation: {e}")
            return CompilationResponse(
                success=False,
                status=CompilationStatus.ERROR,
                message=f"Unexpected error: {str(e)}",
                compilation_time=time.time() - start_time,
                error=str(e)
            )

# Global instance
latex_service = LaTeXCompiler()