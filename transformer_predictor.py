import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("transformer_predictor_module", str(BASE / "09.transformer_predictor.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

TransformerPredictor = module.TransformerPredictor