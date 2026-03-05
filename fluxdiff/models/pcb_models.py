from dataclasses import dataclass, field
from typing import List, Tuple

@dataclass
class Pad:
    number: str
    net: str

@dataclass
class Component:
    ref: str
    value: str
    footprint: str
    x: float
    y: float
    rotation: float
    layer: str
    pads: List[Pad] = field(default_factory=list)

@dataclass
class Net:
    net_id: int
    name: str

@dataclass
class Trace:
    layer: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    net: str

@dataclass
class Via:
    x: float
    y: float
    net: str

@dataclass
class PCBData:
    components: List[Component] = field(default_factory=list)
    nets: List[Net] = field(default_factory=list)
    traces: List[Trace] = field(default_factory=list)
    vias: List[Via] = field(default_factory=list)

@dataclass
class DiffResult:
    component_changes: List[str] = field(default_factory=list)
    net_changes: List[str] = field(default_factory=list)
    routing_changes: List[str] = field(default_factory=list)