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
    results = []
    if getattr(node, "name", None) == target_name:
        results.append(node)
    for child in getattr(node, "children", []):
        results.extend(find_nodes(child, target_name))
    return results


# ---------- NETS ----------
def extract_nets(root):
    nets = []

    for net_node in find_nodes(root, "net"):
        if len(net_node.values) >= 2:
            try:
                net_id = int(net_node.values[0])
                net_name = net_node.values[1].strip('"')
                if net_id != 0:
                    nets.append(Net(net_id=net_id, name=net_name))
            except:
                pass

    return nets


# ---------- PADS ----------
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

            if net_id is not None:
                net_name = net_mapping.get(net_id)

            pads.append(Pad(number=pad_number, net=net_name))

    return pads


# ---------- COMPONENTS ----------
def extract_components(root, nets):
    components = []
    net_mapping = {n.net_id: n.name for n in nets}

    footprints = find_nodes(root, "footprint") + find_nodes(root, "module")

    for fp in footprints:
        ref = ""
        value = ""
        footprint_name = fp.values[0].strip('"') if fp.values else ""
        x, y, rotation = 0.0, 0.0, 0.0
        layer = ""

        # ✅ FIX: ONLY use top-level (at ...)
        at_nodes = [c for c in fp.children if c.name == "at"]
        if at_nodes:
            at = at_nodes[0]
            try:
                vals = at.values
                if len(vals) >= 2:
                    x = float(vals[0])
                    y = float(vals[1])
                if len(vals) >= 3:
                    rotation = float(vals[2])
            except:
                pass

        # Extract other properties
        for child in fp.children:

            # --- Layer ---
            if child.name == "layer":
                layer = child.values[0] if child.values else ""

            # --- KiCad 6 property ---
            elif child.name == "property":
                if len(child.values) >= 2:
                    key = child.values[0].strip('"')
                    val = child.values[1].strip('"')

                    if key == "Reference":
                        ref = val
                    elif key == "Value":
                        value = val

            # --- KiCad 5 fallback ---
            elif child.name == "fp_text":
                if len(child.values) >= 2:
                    text_type = child.values[0].strip('"').lower()
                    text_val = child.values[1].strip('"')

                    if text_type == "reference":
                        ref = text_val
                    elif text_type == "value":
                        value = text_val

        # Ignore invalid refs
        if ref and ref != "REF**":
            comp = Component(
                ref=ref,
                value=value,
                footprint=footprint_name,
                x=x,
                y=y,
                rotation=rotation,
                layer=layer,
                pads=extract_pads(fp, net_mapping)  # ✅ FIXED
            )

            components.append(comp)

    return components


# ---------- TRACES ----------
def extract_traces(root, nets):
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
                    net_name = net_mapping.get(net_id)
                except:
                    net_name = None

            elif child.name == "start":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                    start = (x, y)
                except:
                    pass

            elif child.name == "end":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                    end = (x, y)
                except:
                    pass

        if layer and start and end and net_name:
            traces.append(Trace(layer=layer, start=start, end=end, net=net_name))

    return traces


# ---------- VIAS ----------
def extract_vias(root, nets):
    net_mapping = {n.net_id: n.name for n in nets}
    vias = []

    for via in find_nodes(root, "via"):
        x, y = 0.0, 0.0
        net_id = None
        net_name = None

        for child in via.children:
            if child.name == "at":
                try:
                    x = float(child.values[0])
                    y = float(child.values[1])
                except:
                    pass

            elif child.name == "net":
                try:
                    net_id = int(child.values[0])
                    net_name = net_mapping.get(net_id)
                except:
                    net_name = None

        if net_name:
            vias.append(Via(x=x, y=y, net=net_name))

    return vias