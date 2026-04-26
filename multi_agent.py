import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("multi_agent_module", str(BASE / "11.multi_agent.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

MultiAgentSystem = module.MultiAgentSystem