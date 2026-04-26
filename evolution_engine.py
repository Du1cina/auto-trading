import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("evolution_engine_module", str(BASE / "12.evolution_engine.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

EvolutionEngine = module.EvolutionEngine