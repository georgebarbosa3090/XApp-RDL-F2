#!/usr/bin/env python3
"""
Scientific Documentation Emoji & Icon Sanitizer
Permanently strips all decorative emojis, icons, and non-academic unicode pictographs
from all Markdown (.md) documentation files across Phase 1 and Phase 2.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Semantic replacements for status indicators in tables
STATUS_REPLACEMENTS = {
    "🟢": "[CONFORME]",
    "🟡": "[EM VALIDACAO]",
    "🔴": "[NAO CONFORME]",
    "✓": "[OK]",
    "✔": "[OK]",
    "❌": "[FALHA]",
    "⚠️": "[ALERTA]",
}

# Regex pattern matching emoji / pictograph unicode blocks
# Emoticons, Misc Symbols, Dingbats, Transport/Map, Supplemental, Symbols & Pictographs
EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff"
    r"\u2600-\u26ff"
    r"\u2700-\u27bf"
    r"\u2300-\u23ff"
    r"\u2b00-\u2bff"
    r"\ufe00-\ufe0f"
    r"\u200d\u200b"
    r"\u25aa\u25ab\u25fe\u25fd\u25fb\u25fc\u25b6\u25c0\u3030\u303d\u3297\u3299"
    r"]",
    flags=re.UNICODE,
)


def sanitize_markdown_text(content: str) -> str:
    # First, handle semantic replacements if any
    for sym, repl in STATUS_REPLACEMENTS.items():
        content = content.replace(sym, repl)
    
    # Remove all other emojis
    cleaned = EMOJI_PATTERN.sub("", content)
    
    # Clean up awkward whitespace left behind, like "###  Titulo" -> "### Titulo"
    cleaned = re.sub(r"^(#+\s+)\s+", r"\1", cleaned, flags=re.MULTILINE)
    # Clean up double spaces in bullet points like "*  **Text**" -> "* **Text**"
    cleaned = re.sub(r"^(\s*[\*\-]\s+)\s+", r"\1", cleaned, flags=re.MULTILINE)
    # Clean up "  " -> " " inside headings or text where an emoji was removed
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Restore newlines properly
    # But note: re.sub above might collapse newlines if not careful with spaces. Let's do line by line.
    return cleaned


def process_file(filepath: Path) -> int:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
        original = fp.read()

    lines = original.splitlines(keepends=True)
    new_lines = []
    emojis_removed = 0

    for line in lines:
        mod_line = line
        for sym, repl in STATUS_REPLACEMENTS.items():
            if sym in mod_line:
                mod_line = mod_line.replace(sym, repl)
                emojis_removed += 1

        matches = EMOJI_PATTERN.findall(mod_line)
        if matches:
            emojis_removed += len(matches)
            mod_line = EMOJI_PATTERN.sub("", mod_line)

        # Fix headings spacing: e.g. "###  Navegação" -> "### Navegação"
        mod_line = re.sub(r"^(#+\s+)\s+", r"\1", mod_line)
        # Fix list item spacing: e.g. "*  **Grafana**" -> "* **Grafana**"
        mod_line = re.sub(r"^(\s*[\*\-]\s+)\s+", r"\1", mod_line)

        new_lines.append(mod_line)

    sanitized = "".join(new_lines)
    if emojis_removed > 0:
        with open(filepath, "w", encoding="utf-8") as fp:
            fp.write(sanitized)
    return emojis_removed


def main():
    total_files = 0
    modified_files = 0
    total_emojis = 0

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Ignore git, venv, node_modules
        dirs[:] = [d for d in dirs if d not in (".git", ".venv", "venv", ".venv-rdl", "node_modules", ".pytest_cache", ".idea", ".vscode")]
        for f in files:
            if f.endswith(".md"):
                filepath = Path(root) / f
                total_files += 1
                cnt = process_file(filepath)
                if cnt > 0:
                    modified_files += 1
                    total_emojis += cnt
                    print(f"[REMOVED {cnt:>2} ICONS] {filepath.relative_to(PROJECT_ROOT)}")

    print("=" * 70)
    print(f"Sanitização Concluída:")
    print(f"  • Total de arquivos .md examinados: {total_files}")
    print(f"  • Arquivos .md modificados: {modified_files}")
    print(f"  • Total de ícones/emojis removidos: {total_emojis}")
    print("=" * 70)


if __name__ == "__main__":
    main()
