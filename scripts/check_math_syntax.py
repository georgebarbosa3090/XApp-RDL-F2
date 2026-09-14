import os
import re

directories = ["docs", "experiments", "."]
files = []
for d in directories:
    if os.path.exists(d):
        for f in os.listdir(d):
            if f.endswith(".md"):
                files.append(os.path.join(d, f))

print(f"Checking {len(files)} markdown files...")

issues_found = 0

for filepath in sorted(files):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        lines = content.splitlines()

    for i, line in enumerate(lines, 1):
        # Ignore code blocks
        if line.strip().startswith("```") or line.strip().startswith("`"):
            continue

        # 1. Check for bad sub/superscript with \text without braces, e.g. ^\text{...} or _\text{...}
        bad_subsup = re.findall(r'(?<!\{)[\^_]\\(?:text|mathrm|mathbf)\{[^\}]+\}', line)
        bad_subsup_nobrace = re.findall(r'[\^_]\\(?:text|mathrm|mathbf)(?![a-zA-Z\{])', line)
        if bad_subsup or bad_subsup_nobrace:
            print(f"[SUB/SUP ERROR] {filepath}:{i}")
            print(f"   Line: {line.strip()}")
            issues_found += 1

        # 2. Check for double subscripts like a_b_c without braces
        double_sub = re.findall(r'(?<!\$)\$(?!\$)[^\$]*\b\w+_\w+_\w+[^\$]*\$', line)
        if double_sub:
            print(f"[DOUBLE SUBSCRIPT ERROR] {filepath}:{i}")
            print(f"   Line: {line.strip()}")
            issues_found += 1

        # 3. Check for accented characters inside math expressions $...$ or $$...$$
        parts = line.split("$$")
        if len(parts) > 1:
            for idx in range(1, len(parts), 2):
                math_text = parts[idx]
                accents = [c for c in math_text if c in "áéíóúâêîôûãõàèìòùçÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ"]
                if accents:
                    print(f"[ACCENT IN DISPLAY MATH] {filepath}:{i}")
                    print(f"   Math: {math_text.strip()} (found: {set(accents)})")
                    issues_found += 1

        for part in parts[::2]:
            inline_math = re.findall(r'(?<!\\)\$(.*?)(?<!\\)\$', part)
            for im in inline_math:
                accents = [c for c in im if c in "áéíóúâêîôûãõàèìòùçÁÉÍÓÚÂÊÎÔÛÃÕÀÈÌÒÙÇ"]
                if accents:
                    print(f"[ACCENT IN INLINE MATH] {filepath}:{i}")
                    print(f"   Math: ${im}$ (found: {set(accents)})")
                    issues_found += 1

print(f"\nTotal issues found: {issues_found}")

