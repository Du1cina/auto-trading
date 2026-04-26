import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("trader_module", str(BASE / "03.trader.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

Trader = module.Trader