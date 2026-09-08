#!/usr/bin/env python3
"""
Wrapper para o gerador completo de figuras e cenários da Fase 2.
Executa o gerador unificado com garantia de layout sem sobreposição.
"""

import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from generate_all_diagrams import main

if __name__ == "__main__":
    main()
