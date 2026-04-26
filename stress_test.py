import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("stress_test_module", str(BASE / "13.stress_test.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

StressTest = module.StressTest