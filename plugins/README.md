# OpenWebUI Plugins Directory

This directory contains custom tools and plugins for OpenWebUI integration with the LaTeX compilation backend.

## Available Plugins

### LaTeX Compiler Tool (`latex_compiler.py`)

A comprehensive tool that integrates the FastAPI LaTeX compilation service with OpenWebUI's chat interface.

#### Features:

1. **Direct LaTeX Compilation**
   - Compile any LaTeX content directly from chat
   - Automatic GOST 7-32 formatting support
   - Real-time compilation status

2. **Template Management**
   - List available ГОСТ 7-32 templates
   - Compile templates with custom modifications
   - Replace placeholders in templates

3. **Error Handling**
   - Detailed compilation error reports
   - PDF download links
   - Compilation warnings and logs

#### Usage Examples:

```
User: "Compile this LaTeX document for me: \documentclass[14pt]{styles/gost-7-32} ..."

Assistant: [Uses latex_compiler tool]
✅ Document compiled successfully!
Download your PDF: http://localhost:8000/pdf/compilation_id.pdf
```

```
User: "Show me available LaTeX templates"

Assistant: [Uses latex_compiler tool]
📄 Found 3 LaTeX templates:
• main (main.tex) - Main coursework template
• report (report.tex) - Report template
• thesis (thesis.tex) - Thesis template
```

```
User: "Compile the main template, replace 'Ваше Имя' with 'Иван Петров'"

Assistant: [Uses latex_compiler tool with modifications]
✅ Template compiled with customizations!
Download your PDF: http://localhost:8000/pdf/compilation_id.pdf
```

#### Configuration:

The plugin automatically connects to the backend service at `http://backend:8000` when running in Docker, or `http://localhost:8000` when accessing directly.

#### Tool Endpoints:

- `action: "compile"` - Compile LaTeX content
- `action: "get_templates"` - List available templates
- `action: "compile_template"` - Compile a template with modifications

## Adding Custom Plugins

To add new plugins:

1. Create a new Python file in this directory
2. Follow the structure of `latex_compiler.py`
3. Define tool specification and main function
4. The plugin will be automatically loaded by OpenWebUI

### Plugin Structure:

```python
# Tool specification
TOOL_SPECIFICATION = {
    "name": "tool_name",
    "description": "Tool description",
    "parameters": { ... }
}

# Main tool function
async def tool_function(param1, param2):
    """Main function that OpenWebUI calls"""
    # Tool logic here
    return {"result": "tool output"}

# Optional help text
HELP_TEXT = "Tool usage instructions..."

def get_tool_specification():
    return TOOL_SPECIFICATION

def get_help_text():
    return HELP_TEXT
```

## Integration Notes

- Plugins mount automatically at `/app/tools/custom/` in the OpenWebUI container
- Ensure async/await patterns for network operations
- Use httpx for HTTP requests to backend services
- Include comprehensive error handling
- Provide clear user feedback and progress indicators

## Security Considerations

- Validate all input parameters
- Sanitize LaTeX content before compilation
- Limit compilation timeout and resource usage
- Log all compilation attempts for auditing
- Never expose system files through compilation