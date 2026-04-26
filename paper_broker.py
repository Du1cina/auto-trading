import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("paper_broker_module", str(BASE / "07.paper_broker.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PaperBroker = module.PaperBroker