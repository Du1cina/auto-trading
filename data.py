import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("data_module", str(BASE / "02.data.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

get_stock_data = module.get_stock_data
get_market_regime = module.get_market_regime