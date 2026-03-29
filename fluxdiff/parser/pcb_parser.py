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

def extract_pads(footprint_node, net_mapping):
    pads = []

    for child in footprint_node.children:
        if child.name == "pad":

            pad_number = child.values[0].strip('"') if child.values else ""

            net_id = None
            net_name = None

            for pad_child in child.children:
                if pad_child.name == "net":
                    try:
                        net_id = int(pad_child.values[0])
                    except:
                        pass

            # 🔥 Resolve using global mapping
            if net_id is not None:
                net_name = net_mapping.get(net_id)

            pads.append(Pad(number=pad_number, net=net_name))

    return pads

def extract_nets(root):
    nets = []

    for node in root.children:
        if node.name == "net":
            if len(node.values) >= 2:
                try:
                    net_id = int(node.values[0])
                    net_name = node.values[1].strip('"')
                    if net_id != 0:
                        nets.append(Net(net_id=net_id, name=net_name))
                except:
                    pass

    return nets

def extract_components(root, nets):
    components = []
    net_mapping = {n.net_id: n.name for n in nets}

    # Support both KiCad formats:
    # KiCad 6+  -> (footprint ...)
    # KiCad 5   -> (module ...)
    footprints = find_nodes(root, "footprint") + find_nodes(root, "module")

    for fp in footprints:

        ref = ""
        value = ""
        footprint_name = fp.values[0] if fp.values else ""
        x, y, rotation = 0.0, 0.0, 0.0
        layer = ""

        for child in fp.children:

            # --- position ---
            if child.name == "at":
                try:
                    x = float(child.values[0]) if len(child.values) > 0 else 0
                    y = float(child.values[1]) if len(child.values) > 1 else 0
                    rotation = float(child.values[2]) if len(child.values) > 2 else 0
                except Exception:
                    pass

            # --- layer ---
            elif child.name == "layer":
                layer = child.values[0] if child.values else ""

            # --- KiCad 6+ property format ---
            # AFTER — handles value as either values[1] OR first child's value
            elif child.name == "property":
                if len(child.values) >= 1:
                   key = child.values[0].strip('"')

                   # Try values[1] first (simple case)
                   if len(child.values) >= 2:
                     val = child.values[1].strip('"')
                  # Fall back: KiCad 8 puts the value as a bare token in children
                   elif child.children and child.children[0].values:
                     val = child.children[0].values[0].strip('"')
                   else:
                    val = ""

                   if key == "Reference":
                    ref = val
                   elif key == "Value":
                    value = val

            # --- KiCad 5 text format ---
            elif child.name == "fp_text":
                if len(child.values) >= 2:
                    text_type = child.values[0].strip('"')
                    text_val = child.values[1].strip('"')

                    if text_type.lower() == "reference":
                        ref = text_val
                    elif text_type.lower() == "value":
                        value = text_val

        pads = extract_pads(fp, net_mapping)

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

        # ignore placeholder references
        if ref and ref != "REF**":
            components.append(comp)

    return components

def extract_traces(root, nets):
    # traces come from (segment ...)
    net_mapping = {n.net_id: n.name for n in nets}
    traces = []
    for segment in find_nodes(root, "segment"):
        layer = ""
        net_id = None
        net_name = None
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