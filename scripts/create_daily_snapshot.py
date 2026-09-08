#!/usr/bin/env python3
"""
Script de Snapshot Diário Local - xApp RDL.
Cria arquivo compactado (.zip) em .snapshots/ e gera tag/branch Git localmente.
NOTA DE SEGURANÇA: É PROIBIDO executar 'git push'. Todas as operações são 100% locais.
"""

import os
import sys
import datetime
import zipfile
import subprocess
from pathlib import Path

def create_local_snapshot():
    project_root = Path(__file__).resolve().parent.parent
    snapshots_dir = project_root / ".snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = snapshots_dir / f"snapshot_{timestamp}.zip"
    
    # 1. Pastas e arquivos essenciais para inclusão
    target_dirs = ["src", "docs", "deploy", "configs", "scripts", "tests"]
    target_files = ["README.md", "pyproject.toml", "requirements.txt", "setup.py", "Makefile", ".gitignore"]
    
    print(f"[*] Criando snapshot em: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zip_out:
        for t_dir in target_dirs:
            dir_path = project_root / t_dir
            if dir_path.exists():
                for file_path in dir_path.rglob("*"):
                    if "__pycache__" in file_path.parts or ".pytest_cache" in file_path.parts:
                        continue
                    if file_path.is_file():
                        rel_path = file_path.relative_to(project_root)
                        zip_out.write(file_path, rel_path)
                        
        for t_file in target_files:
            file_path = project_root / t_file
            if file_path.exists():
                zip_out.write(file_path, t_file)
                
    file_size_mb = zip_filename.stat().st_size / (1024 * 1024)
    print(f"[+] Snapshot ZIP criado com sucesso ({file_size_mb:.2f} MB).")
    
    # 2. Criar tag Git local
    try:
        tag_name = f"snapshot-{timestamp.replace('_', '-')}"
        branch_name = f"backup/snapshot-{timestamp.replace('_', '-')}"
        
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Snapshot automatico diario: {timestamp}"], cwd=project_root, check=False)
        subprocess.run(["git", "branch", branch_name], cwd=project_root, check=False)
        print(f"[+] Tag Git local '{tag_name}' e branch '{branch_name}' criadas com sucesso (sem push remoto).")
    except Exception as e:
        print(f"[!] Aviso: Nao foi possivel criar tag Git: {e}")

if __name__ == "__main__":
    create_local_snapshot()
