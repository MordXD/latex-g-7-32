"""
OpenWebUI Custom Tool for LaTeX Compilation

This tool integrates with the FastAPI LaTeX compilation backend
to compile LaTeX documents directly from the chat interface.
"""

import json
import logging
from typing import Dict, Any, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LaTeXCompilerTool:
    def __init__(self, base_url: str = "http://backend:8000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=60.0)

    async def compile_latex(
        self,
        content: str,
        description: str = "LaTeX document",
        compiler_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compile LaTeX document content

        Args:
            content: LaTeX source code
            description: Description of what the document contains
            compiler_options: Additional pdflatex options

        Returns:
            Dictionary with compilation results
        """
        try:
            payload = {
                "content": content,
                "compiler_options": compiler_options or {}
            }

            response = await self.client.post(
                f"{self.base_url}/api/compile",
                json=payload
            )
            response.raise_for_status()

            result = response.json()

            # Format response for user
            if result["success"]:
                return {
                    "success": True,
                    "message": f"✅ {description} compiled successfully!",
                    "pdf_url": f"http://localhost:8000{result['pdf_url']}",
                    "compilation_time": result["compilation_time"],
                    "warnings": result.get("warnings"),
                    "download_url": f"http://localhost:8000{result['pdf_url']}"
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Failed to compile {description}",
                    "error": result.get("error", "Unknown error"),
                    "output": result.get("output", "")
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during compilation: {e}")
            return {
                "success": False,
                "message": "❌ Compilation service error",
                "error": f"HTTP {e.response.status_code}: {e.response.text}"
            }
        except Exception as e:
            logger.error(f"Compilation error: {e}")
            return {
                "success": False,
                "message": "❌ Compilation failed",
                "error": str(e)
            }

    async def get_templates(self) -> Dict[str, Any]:
        """Get available LaTeX templates"""
        try:
            response = await self.client.get(f"{self.base_url}/api/templates")
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get templates: {e}")
            return {"templates": []}

    async def get_template_content(self, template_name: str) -> Dict[str, Any]:
        """Get content of a specific template"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/templates/{template_name}"
            )
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get template {template_name}: {e}")
            return {"error": str(e)}

    async def compile_template(
        self,
        template_name: str,
        modifications: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Compile a template with optional modifications"""
        try:
            # Get template content
            template_data = await self.get_template_content(template_name)
            if "error" in template_data:
                return template_data

            content = template_data["content"]

            # Apply modifications if provided
            if modifications:
                for placeholder, replacement in modifications.items():
                    content = content.replace(placeholder, replacement)

            # Compile the modified template
            return await self.compile_latex(
                content,
                description=f"Template '{template_name}'"
            )

        except Exception as e:
            logger.error(f"Failed to compile template {template_name}: {e}")
            return {
                "success": False,
                "message": f"❌ Failed to compile template '{template_name}'",
                "error": str(e)
            }

# Tool specification for OpenWebUI
TOOL_SPECIFICATION = {
    "name": "latex_compiler",
    "description": "Compile LaTeX documents with ГОСТ 7-32 templates",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["compile", "get_templates", "compile_template"],
                "description": "Action to perform"
            },
            "content": {
                "type": "string",
                "description": "LaTeX source code to compile (for compile action)"
            },
            "template_name": {
                "type": "string",
                "description": "Name of template to compile (for compile_template action)"
            },
            "modifications": {
                "type": "object",
                "description": "Key-value pairs to replace in template (for compile_template action)"
            }
        },
        "required": ["action"]
    }
}

# OpenWebUI tool function
async def latex_compiler_tool(
    action: str,
    content: Optional[str] = None,
    template_name: Optional[str] = None,
    modifications: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Main tool function for OpenWebUI integration

    Args:
        action: Action to perform (compile, get_templates, compile_template)
        content: LaTeX content (for compile action)
        template_name: Template name (for compile_template action)
        modifications: Template modifications (for compile_template action)

    Returns:
        Compilation results or template information
    """
    compiler = LaTeXCompilerTool()

    try:
        if action == "compile":
            if not content:
                return {
                    "success": False,
                    "message": "❌ LaTeX content is required for compilation",
                    "error": "Missing content parameter"
                }

            return await compiler.compile_latex(content)

        elif action == "get_templates":
            templates_data = await compiler.get_templates()
            templates = templates_data.get("templates", [])

            if not templates:
                return {
                    "success": False,
                    "message": "❌ No LaTeX templates available",
                    "available_templates": []
                }

            template_list = []
            for template in templates:
                template_list.append(f"• {template['name']} ({template['filename']})")

            return {
                "success": True,
                "message": f"📄 Found {len(templates)} LaTeX templates:",
                "templates": templates,
                "template_list": "\n".join(template_list)
            }

        elif action == "compile_template":
            if not template_name:
                return {
                    "success": False,
                    "message": "❌ Template name is required",
                    "error": "Missing template_name parameter"
                }

            return await compiler.compile_template(template_name, modifications)

        else:
            return {
                "success": False,
                "message": f"❌ Unknown action: {action}",
                "error": f"Supported actions: compile, get_templates, compile_template"
            }

    except Exception as e:
        logger.error(f"LaTeX tool error: {e}")
        return {
            "success": False,
            "message": "❌ LaTeX compilation tool error",
            "error": str(e)
        }

# Help text for users
HELP_TEXT = """
**LaTeX Document Compiler Tool**

This tool allows you to compile LaTeX documents with ГОСТ 7-32 formatting.

**Available actions:**

1. **Compile LaTeX content**
   - Action: `compile`
   - Provide: LaTeX source code
   - Returns: Compiled PDF with download link

2. **List available templates**
   - Action: `get_templates`
   - Shows all available ГОСТ 7-32 templates

3. **Compile a template**
   - Action: `compile_template`
   - Provide: Template name
   - Optional: Modifications to replace placeholders
   - Returns: Compiled PDF template

**Example usage:**
- "Compile this LaTeX document: \\documentclass... (full content)"
- "Show me available LaTeX templates"
- "Compile the main template with my name"
- "Compile the coursework template replacing the title"

The tool handles the complete LaTeX compilation process including bibliography
processing and multiple compilation passes for proper references.
"""

def get_tool_specification():
    """Return tool specification for OpenWebUI"""
    return TOOL_SPECIFICATION

def get_help_text():
    """Return help text for users"""
    return HELP_TEXT