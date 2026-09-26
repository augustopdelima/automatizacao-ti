"""Garante que a raiz do projeto esteja no sys.path ao rodar `pytest`.

Permite importar os módulos de `src/` de qualquer lugar dos testes.
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))