import os
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

patterns = [
    # file:/// URLs with local absolute path
    (re.compile(r'file:///c:/Users/george\.barbosa/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'file:///mnt/c/Users/george\.barbosa/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'file:///[a-zA-Z]:/[^)]*?/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>]+)', re.IGNORECASE), r'\1'),
    
    # WSL / Linux paths
    (re.compile(r'/mnt/c/Users/george\.barbosa/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>`]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'/mnt/c/Users/george\.barbosa/\/iqos-xapp-rdl-phase2', re.IGNORECASE), r'.'),
    
    # Windows paths with forward or backward slashes
    (re.compile(r'[a-zA-Z]:/Users/george\.barbosa/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>`]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'[a-zA-Z]:\\Users\\george\.barbosa\\\.gemini\\antigravity\\scratch\\iqos-xapp-rdl-phase2\\([^\s\)\"\'>`]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'Users/george\.barbosa/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>`]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'/\/iqos-xapp-rdl-phase2/([^\s\)\"\'>`]+)', re.IGNORECASE), r'\1'),
    (re.compile(r'/\', re.IGNORECASE), r''),
    (re.compile(r'\', re.IGNORECASE), r'')
]

count = 0
for root, dirs, files in os.walk(ROOT_DIR):
    if ".git" in root or ".venv" in root:
        continue
    for f in files:
        if f.endswith((".md", ".json", ".txt", ".sh", ".py")):
            filepath = os.path.join(root, f)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()
            
            new_content = content
            for regex, repl in patterns:
                new_content = regex.sub(repl, new_content)
            
            if new_content != content:
                with open(filepath, "w", encoding="utf-8") as fp:
                    fp.write(new_content)
                print(f"[REPLACED] {os.path.relpath(filepath, ROOT_DIR)}")
                count += 1

print(f"Total files updated: {count}")
