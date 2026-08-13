import os
import ast

def add_docstrings(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    
    # Simple regex-based approach for functions ending with `):`
    # A robust approach is hard without a full parser like libcst, 
    # but we will try a line-by-line heuristic.
    lines = source.split('\n')
    new_lines = []
    
    in_def = False
    indent = ""
    func_name = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        if not in_def:
            if line.lstrip().startswith("def ") or line.lstrip().startswith("async def "):
                in_def = True
                # Extract indent
                indent = line[:len(line) - len(line.lstrip())] + "    "
                
                parts = line.split("def ")
                if len(parts) > 1:
                    func_name = parts[1].split("(")[0].strip()
                    
        if in_def:
            # check if it's the end of the def signature
            if "):" in line or ") ->" in line or line.rstrip().endswith(":"):
                # Check next line if it already has a docstring
                if i + 1 < len(lines):
                    next_line = lines[i+1].strip()
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        in_def = False
                        i += 1
                        continue
                
                # Add docstring
                new_lines.append(f'{indent}"""Handles operations for {func_name}."""')
                in_def = False
        
        i += 1
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

if __name__ == "__main__":
    for root, _, files in os.walk('src'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                add_docstrings(os.path.join(root, file))
    print("Docstrings added successfully.")
