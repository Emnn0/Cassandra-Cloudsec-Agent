import sys
from pathlib import Path

# backend/ klasörünü Python path'ine ekle ki "from app...." import'ları çalışsın
sys.path.insert(0, str(Path(__file__).parent.parent))
