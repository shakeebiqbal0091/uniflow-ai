import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from backend.app.main import app

for r in app.routes:
    path = getattr(r, 'path', None)
    name = getattr(r, 'name', None)
    methods = getattr(r, 'methods', None)
    if path and path.startswith('/api/requests'):
        print(path, methods, name)
