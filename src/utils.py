import os
import re
import markdown
from jinja2 import Environment, FileSystemLoader

def save_to_file(content, filename, directory="output"):
    """Saves content to a file in the specified directory."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath

def convert_markdown_to_html(text):
    """
    Converts Markdown text to HTML with proper code block AND LaTeX handling.
    
    Strategy:
    1. Extract ALL code blocks first (using robust pattern matching)
    2. Extract ALL LaTeX formulas (both inline $...$ and display $$...$$)
    3. Replace with unique placeholders that won't be processed by markdown
    4. Convert remaining markdown to HTML
    5. Restore code blocks and LaTeX formulas
    """
    code_blocks = []
    latex_blocks = []
    
    def extract_code_block(match):
        """Extract code block and replace with placeholder."""
        lang = match.group(1) or ''
        code = match.group(2)
        
        # Clean up the code
        code = code.strip('\n\r')
        
        # Create placeholder with triple pipes (won't be processed by markdown)
        placeholder = f'|||CODEBLOCK|||{len(code_blocks)}|||'
        
        # Handle Mermaid diagrams specially - wrap in div.mermaid for rendering
        if lang.lower() == 'mermaid':
            code_blocks.append(f'<div class="mermaid">\n{code}\n</div>')
        else:
            # Escape HTML entities in code (but not for mermaid)
            code = code.replace('&', '&amp;')
            code = code.replace('<', '&lt;')
            code = code.replace('>', '&gt;')
            code = code.replace('"', '&quot;')
            
            # Store the formatted code block
            if lang:
                code_blocks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            else:
                code_blocks.append(f'<pre><code>{code}</code></pre>')
        
        return placeholder
    
    def extract_latex(match):
        """Extract LaTeX formula and replace with placeholder."""
        full_match = match.group(0)
        
        # Create placeholder
        placeholder = f'|||LATEX|||{len(latex_blocks)}|||'
        latex_blocks.append(full_match)
        
        return placeholder
    
    # Pattern to match fenced code blocks
    code_pattern = r'```(\w*)\s*\n?(.*?)\n?```'
    
    # Extract code blocks first
    processed_text = re.sub(code_pattern, extract_code_block, text, flags=re.DOTALL)
    
    # Extract LaTeX display math ($$...$$) before inline
    display_latex_pattern = r'\$\$([^$]+)\$\$'
    processed_text = re.sub(display_latex_pattern, extract_latex, processed_text)
    
    # Extract LaTeX inline math ($...$) - but not escaped \$ 
    # Use a pattern that avoids matching empty $$ or ambiguous cases
    inline_latex_pattern = r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)'
    processed_text = re.sub(inline_latex_pattern, extract_latex, processed_text)
    
    # Configure markdown - removed 'extra' extension which causes underscore issues
    md = markdown.Markdown(extensions=[
        'tables',
        'sane_lists',
        'smarty',
    ])
    
    # Convert markdown to HTML
    html = md.convert(processed_text)
    
    # Restore code blocks
    for i, code_html in enumerate(code_blocks):
        placeholder = f'|||CODEBLOCK|||{i}|||'
        # Handle both raw placeholder and wrapped in <p> tags
        html = html.replace(f'<p>{placeholder}</p>', code_html)
        html = html.replace(placeholder, code_html)
    
    # Restore LaTeX blocks
    for i, latex in enumerate(latex_blocks):
        placeholder = f'|||LATEX|||{i}|||'
        # Handle both raw placeholder and wrapped in <p> tags
        html = html.replace(f'<p>{placeholder}</p>', f'<p>{latex}</p>')
        html = html.replace(placeholder, latex)
    
    # Clean up any remaining artifacts
    # Remove empty <p></p> tags
    html = re.sub(r'<p>\s*</p>', '', html)
    
    # Fix invalid <p><div> nesting (p should not contain block elements like div)
    html = re.sub(r'<p>\s*(<div[^>]*>)', r'\1', html)
    html = re.sub(r'(</div>)\s*</p>', r'\1', html)
    
    return html

def generate_html_report(topic, study_plan_data, study_material_data, interview_qa_data, total_tokens, template_dir="templates", output_dir="output"):
    """Generates an HTML report using Jinja2."""
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report_template.html")
    
    # Convert content to HTML
    study_plan_html = convert_markdown_to_html(study_plan_data['content'])
    study_material_html = convert_markdown_to_html(study_material_data['content'])
    interview_qa_html = convert_markdown_to_html(interview_qa_data['content'])

    html_content = template.render(
        topic=topic,
        study_plan=study_plan_html,
        study_material=study_material_html,
        interview_qa=interview_qa_html,
        token_usage=total_tokens
    )
    
    filename = f"{topic.replace(' ', '_').lower()}_study_guide.html"
    return save_to_file(html_content, filename, output_dir)

def clean_text(text):
    """Basic text cleaning if needed."""
    return text.strip()
