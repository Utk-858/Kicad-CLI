from fluxdiff.models.pcb_models import PCBData

def build_connectivity_graph(pcb: PCBData):
    """
    Build a connectivity dictionary of the form:
    {
        net_name: set of (component_ref, pad_number)
    }
    where entries for each net include all (ref, pad#) participating from
    pads, traces, and vias.
    """
    graph = dict()

    # --- 1. From pads ---
    for comp in pcb.components:
        ref = getattr(comp, "ref", None)
        for pad in getattr(comp, "pads", []):
            pad_net = getattr(pad, "net", None)
            pad_num = getattr(pad, "number", None)
            if pad_net and pad_num and ref:
                entry = (ref, str(pad_num))
                graph.setdefault(pad_net, set()).add(entry)

    # --- 2. From traces (edges between pads/endpoints) ---
    for trace in getattr(pcb, "traces", []):
        net = getattr(trace, "net", None)
        start_ref = getattr(trace, "start_component_ref", None)
        start_pad = getattr(trace, "start_pad_number", None)
        end_ref = getattr(trace, "end_component_ref", None)
        end_pad = getattr(trace, "end_pad_number", None)

        # If endpoint info (component/pad) is present, include it.
        if net:
            trace_entries = set()
            if start_ref and start_pad:
                trace_entries.add((start_ref, str(start_pad)))
            if end_ref and end_pad:
                trace_entries.add((end_ref, str(end_pad)))
            for entry in trace_entries:
                graph.setdefault(net, set()).add(entry)
            # If no ref/pad, just ignore (could extend to x/y coordinate if needed)

    # --- 3. From vias (each via is a node on a net, with optional component/pad info) ---
    for via in getattr(pcb, "vias", []):
        net = getattr(via, "net", None)
        ref = getattr(via, "component_ref", None)
        pad_num = getattr(via, "pad_number", None)
        # If via connected directly to a component pad, add
        if net:
            if ref and pad_num:
                entry = (ref, str(pad_num))
                graph.setdefault(net, set()).add(entry)
            else:
                # For generic (ref-less) vias, represent by unique coordinates (optional)
                pos = getattr(via, "position", None)
                if pos:
                    entry = ("VIA", f"{pos[0]:.3f},{pos[1]:.3f}")
                    graph.setdefault(net, set()).add(entry)
    return graph

def compare_connectivity(graph_old, graph_new):
    """
    Compare two connectivity graphs, report nets that gained/lost connections,
    and nets that have disappeared (present in old, absent in new).
    Returns a list of human-readable messages.
    """
    messages = []

    old_nets = set(graph_old.keys())
    new_nets = set(graph_new.keys())

    # Nets that disappeared
    for vanished in sorted(old_nets - new_nets):
        messages.append(f"Net disappeared: {vanished}")

    # Nets that are new (appear only in new)
    for newnet in sorted(new_nets - old_nets):
        messages.append(f"Net added: {newnet}")

    # Nets in both, check for gained/lost connections
    for net in sorted(old_nets & new_nets):
        old_set = graph_old.get(net, set())
        new_set = graph_new.get(net, set())
        lost = old_set - new_set
        gained = new_set - old_set

        if gained:
            gain_str = ", ".join(sorted(f"{ref}:{pad}" for ref, pad in gained))
            messages.append(f"Net {net} gained connections: {gain_str}")
        if lost:
            lost_str = ", ".join(sorted(f"{ref}:{pad}" for ref, pad in lost))
            messages.append(f"Net {net} lost connections: {lost_str}")

    return messages