"""
Find and show where mermaid syntax errors are 
"""
import re

# Check both files
for fname in ['output/logistic_regression_study_guide.html', 'output/logistic_regression_study_guide_fixed.html']:
    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print('='*60)
    
    with open(fname, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find mermaid blocks
    pattern = r'<div class="mermaid">(.*?)</div>'
    matches = re.findall(pattern, content, re.DOTALL)
    
    errors = []
    for i, m in enumerate(matches):
        # Check for common issues
        issues = []
        
        # Double brackets
        if ']]' in m or '[[' in m:
            issues.append('double brackets')
        
        # Unbalanced brackets
        if m.count('[') != m.count(']'):
            issues.append(f'unbalanced [ ]: {m.count("[")} vs {m.count("]")}')
        
        # Extra arrows or mixed lines (heuristic: too many -->)
        arrows = m.count('-->')
        lines = len([l for l in m.strip().split('\n') if l.strip()])
        if arrows > lines * 1.5:
            issues.append(f'too many arrows: {arrows} arrows for {lines} lines')
        
        if issues:
            errors.append((i+1, issues, m[:150]))
    
    print(f"\nTotal blocks: {len(matches)}")
    print(f"Errors found: {len(errors)}")
    
    for idx, issues, preview in errors:
        print(f"\n--- Block {idx} ---")
        for iss in issues:
            print(f"  * {iss}")
        print(f"Preview: {preview}...")
