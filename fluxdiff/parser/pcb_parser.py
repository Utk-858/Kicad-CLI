from fluxdiff.models.pcb_models import PCBData, Component, Net, Trace, Via, Pad
from fluxdiff.parser.sexp_parser import parse_sexp

def parse_pcb(file_path):
    root = parse_sexp(file_path)
    nets = extract_nets(root)
    components = extract_components(root, nets)
    traces = extract_traces(root, nets)
    vias = extract_vias(root, nets)
    return PCBData(
        components=components,
        nets=nets,
        traces=traces,
        vias=vias
    )

def find_nodes(node, target_name):
    """Recursively find all nodes with .name == target_name."""
    results = []
    if getattr(node, "name", None) == target_name:
        results.append(node)
    for child in getattr(node, "children", []):
        results.extend(find_nodes(child, target_name))
    return results

def extract_pads(footprint_node):
    pads = []

    for child in footprint_node.children:
        if child.name == "pad":

            pad_number = child.values[0].strip('"') if child.values else ""

            net_name = ""

            for pad_child in child.children:
                if pad_child.name == "net":
                    # net structure: (net <id> "NAME")
                    if len(pad_child.values) >= 2:
                        net_name = pad_child.values[1].strip('"')

            pads.append(Pad(number=pad_number, net=net_name))

    return pads

def extract_nets(root):
    """
    Extract all net definitions from the KiCad PCB tree.

    KiCad nets look like:
        (net 1 "GND")
        (net 2 "VCC")
    """

    nets = []

    for net_node in find_nodes(root, "net"):

        if len(net_node.values) >= 2:
            try:
                net_id = int(net_node.values[0])
                net_name = net_node.values[1].strip('"')
                if net_id != 0:
                    nets.append(Net(net_id=net_id, name=net_name))
            except Exception:
                pass

    return nets


def extract_components(root, nets):
    components = []
    net_mapping = {n.net_id: n.name for n in nets}

    for fp in find_nodes(root, "footprint"):

        ref = ""
        value = ""
        footprint_name = fp.values[0] if fp.values else ""
        x, y, rotation = 0.0, 0.0, 0.0
        layer = ""

        for child in fp.children:

            if child.name == "at":
                try:
                    x = float(child.values[0]) if len(child.values) > 0 else 0
                    y = float(child.values[1]) if len(child.values) > 1 else 0
                    rotation = float(child.values[2]) if len(child.values) > 2 else 0
                except:
                    pass

            elif child.name == "layer":
                layer = child.values[0] if child.values else ""

            elif child.name == "property":
                if len(child.values) >= 2:
                    key = child.values[0].strip('"')
                    val = child.values[1].strip('"')

                    if key == "Reference":
                        ref = val
                    elif key == "Value":
                        value = val

        pads = extract_pads(fp)

        comp = Component(
            ref=ref,
            value=value,
            footprint=footprint_name,
            x=x,
            y=y,
            rotation=rotation,
            layer=layer,
            pads=pads
        )

        components.append(comp)

    return components

def extract_traces(root, nets):
    # traces come from (segment ...)
    net_mapping = {n.net_id: n.name for n in nets}
    traces = []
    for segment in find_nodes(root, "segment"):
        layer = ""
        net_id = None
        net_name = ""
        start = (0.0, 0.0)
        end = (0.0, 0.0)
        for child in segment.children:
            if child.name == "layer":
                layer = child.values[0] if child.values else ""
            elif child.name == "net":
                try:
                    net_id = int(child.values[0])
                    net_name = net_mapping.get(net_id, "")
                except Exception:
                    net_name = ""
            elif child.name == "start":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                    start = (x, y)
                except Exception:
                    pass
            elif child.name == "end":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                    end = (x, y)
                except Exception:
                    pass
        if layer and start and end and net_name:
            traces.append(Trace(layer=layer, start=start, end=end, net=net_name))
    return traces

def extract_vias(root, nets):
    # (via ... (at x y) (net id))
    net_mapping = {n.net_id: n.name for n in nets}
    vias = []
    for via in find_nodes(root, "via"):
        x, y = 0.0, 0.0
        net_id = None
        net_name = ""
        for child in via.children:
            if child.name == "at":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                except Exception:
                    pass
            elif child.name == "net":
                try:
                    net_id = int(child.values[0])
                    net_name = net_mapping.get(net_id, "")
                except Exception:
                    net_name = ""
        if net_name:
            vias.append(Via(x=x, y=y, net=net_name))
    return vias