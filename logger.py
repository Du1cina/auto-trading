import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("logger_module", str(BASE / "04.logger.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

Logger = module.Logger