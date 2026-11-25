# dependencies/coordination.py
from services.cordination.cordination import MemoryCoordinator

_coordinator = MemoryCoordinator()

def get_coordinator() -> MemoryCoordinator:
    return _coordinator