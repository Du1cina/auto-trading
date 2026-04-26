import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("performance_module", str(BASE / "05.performance.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PerformanceAnalyzer = module.PerformanceAnalyzer