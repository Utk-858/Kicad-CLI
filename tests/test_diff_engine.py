import pytest
from types import SimpleNamespace

from fluxdiff.diff.diff_engine import compare_pcbs

# Helper: Minimalistic Pad and Component mock classes for PCBData structure
class Pad:
    def __init__(self, number, net):
        self.number = number
        self.net = net

class Component:
    def __init__(self, ref, value="R", footprint="0402", x=0, y=0, rotation=0, layer="F", pads=None):
        self.ref = ref
        self.value = value
        self.footprint = footprint
        self.x = x
        self.y = y
        self.rotation = rotation
        self.layer = layer
        self.pads = pads if pads is not None else []

class Trace:
    def __init__(self, net, points):
        self.net = net
        self.points = points  # List of (x, y)

@pytest.fixture
def minimal_pcbs():
    # Common elements
    pad1 = Pad("1", "N1")
    pad2 = Pad("1", "N1")
    comp1 = Component("R1", pads=[pad1], x=10, y=10)
    comp2 = Component("C1", pads=[pad2], x=20, y=20)
    trace = Trace("N1", [(10, 10), (20, 20)])
    # PCBData is a namespace with .components and .traces
    pcb = SimpleNamespace(
        components=[comp1, comp2],
        traces=[trace],
        nets=["N1"],
        vias=[],
    )
    return pcb, comp1, comp2, trace

def make_pcb(components, traces):
    # Helper to return a PCBData-like object
    return SimpleNamespace(
        components=components,
        traces=traces,
        nets=["N1"],
        vias=[],
    )

def test_component_move(minimal_pcbs):
    pcb_before, comp1, comp2, trace = minimal_pcbs
    # Move R1 by +2mm in X
    moved_r1 = Component("R1", pads=comp1.pads, x=comp1.x + 2, y=comp1.y)
    pcb_after = make_pcb([moved_r1, comp2], [trace])
    result = compare_pcbs(pcb_before, pcb_after)
    # Check message for component moved
    assert any("Component moved: R1" in msg for msg in result.component_changes)

def test_net_change(minimal_pcbs):
    pcb_before, comp1, comp2, trace = minimal_pcbs
    # Change C1 pad net from N1 to N2
    changed_pad = Pad("1", "N2")
    changed_c2 = Component("C1", pads=[changed_pad], x=comp2.x, y=comp2.y)
    pcb_after = make_pcb([comp1, changed_c2], [trace])
    result = compare_pcbs(pcb_before, pcb_after)
    # Should report CRITICAL net change for C1 pad 1
    msg = f"CRITICAL: C1 pad 1 changed from N1 -> N2"
    assert any(msg in change for change in result.net_changes)

def test_trace_addition(minimal_pcbs):
    pcb_before, comp1, comp2, trace = minimal_pcbs
    # Add a new trace to the same net
    new_trace = Trace("N1", [(20, 20), (30, 30)])
    pcb_after = make_pcb([comp1, comp2], [trace, new_trace])
    result = compare_pcbs(pcb_before, pcb_after)
    # Should show a routing change
    assert any("routing" in msg.lower() or "trace" in msg.lower() for msg in result.routing_changes) or len(result.routing_changes) > 0
