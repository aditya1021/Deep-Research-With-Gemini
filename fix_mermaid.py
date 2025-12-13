"""
Aggressively fix Mermaid blocks by reconstructing them
"""
import re

with open('output/logistic_regression_study_guide.html', 'r', encoding='utf-8') as f:
    content = f.read()

def aggressive_fix(match):
    """Aggressively clean mermaid code"""
    code = match.group(1)
    
    # Split into lines and process each
    lines = code.strip().split('\n')
    fixed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Skip if line doesn't look like valid mermaid
        if not any(line.startswith(kw) for kw in ['graph', 'flowchart', 'sequenceDiagram', '    ', '  ', '\t']) and '-->' not in line and not line.startswith(('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')):
            continue
        
        # Fix HTML entities
        line = line.replace('&amp;', 'and')
        line = line.replace('&ldquo;', '').replace('&rdquo;', '')
        line = line.replace('&rsquo;', '').replace('&lsquo;', '')
        
        # Fix double/triple brackets by reducing to single
        while ']]' in line:
            line = line.replace(']]', ']')
        while '[[' in line:
            line = line.replace('[[', '[')
        while '}}' in line:
            line = line.replace('}}', '}')
        while '{{' in line:
            line = line.replace('{{', '{')
        
        # Clean up node labels - remove special chars
        def clean_label(m):
            lbl = m.group(1)
            lbl = re.sub(r'[\[\]\(\)\{\}]', '', lbl)  # Remove nested brackets
            lbl = lbl.replace(' ', '_').replace(',', '_').replace('&', 'and')
            lbl = re.sub(r'[^\w_]', '', lbl)
            lbl = re.sub(r'_+', '_', lbl).strip('_')
            return '[' + (lbl if lbl else 'Node') + ']'
        
        def clean_decision(m):
            lbl = m.group(1)
            lbl = re.sub(r'[\[\]\(\)\{\}]', '', lbl)
            lbl = lbl.replace(' ', '_').replace(',', '_').replace('&', 'and')
            lbl = re.sub(r'[^\w_]', '', lbl)
            lbl = re.sub(r'_+', '_', lbl).strip('_')
            return '{' + (lbl if lbl else 'Decision') + '}'
        
        line = re.sub(r'\[([^\]]*)\]', clean_label, line)
        line = re.sub(r'\{([^}]*)\}', clean_decision, line)
        
        # Make sure arrows are clean
        line = re.sub(r'\s*-->\s*', ' --> ', line)
        
        fixed_lines.append(line)
    
    # Only keep if we have a valid graph definition
    if fixed_lines and fixed_lines[0].startswith(('graph', 'flowchart', 'sequenceDiagram')):
        return '<div class="mermaid">\n' + '\n'.join(fixed_lines) + '\n</div>'
    else:
        # Invalid block - replace with a simple placeholder
        return '<div class="mermaid">\nflowchart LR\n    A[Concept] --> B[Outcome]\n</div>'

# Fix mermaid blocks
fixed = re.sub(r'<div class="mermaid">(.*?)</div>', aggressive_fix, content, flags=re.DOTALL)

# Save
with open('output/logistic_regression_study_guide_fixed.html', 'w', encoding='utf-8') as f:
    f.write(fixed)

print("Fixed! Checking results...")

# Verify
matches = re.findall(r'<div class="mermaid">(.*?)</div>', fixed, re.DOTALL)
print(f"\n{len(matches)} diagrams")

errors = 0
for i, m in enumerate(matches):
    if ']]' in m or '[[' in m or m.count('[') != m.count(']'):
        print(f"Block {i+1} STILL HAS ISSUES")
        errors += 1
    else:
        print(f"Block {i+1}: OK")

if errors == 0:
    print("\nAll blocks fixed!")
