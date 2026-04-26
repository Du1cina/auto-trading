import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("ml_selector_module", str(BASE / "08.ml_selector.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

MLStockSelector = module.MLStockSelector