def run_erc_checks(graph):
    """
    Run basic Electrical Rule Checks (ERC) on a connectivity graph.

    Args:
        graph (dict): { net_name: set of (component_ref, pad_number) }

    Returns:
        list of str: ERC check messages.
    """
    messages = []

    # Check for power short circuits
    # Build a reverse lookup: { (component_ref, pad_number): net_name }
    for net_name, connections in graph.items():
        # Check if net contains both VCC and GND pins
        found_gnd = False
        found_vcc = False
        for cref, _ in connections:
            # Heuristic checks for power references
            # Accept component references like 'VCC', 'GND', or pins named 'VCC', 'GND'
            if cref is not None:
                ref_upper = str(cref).upper()
                if "GND" == ref_upper or ref_upper.startswith("GND"):
                    found_gnd = True
                if "VCC" == ref_upper or ref_upper.startswith("VCC"):
                    found_vcc = True
        if found_gnd and found_vcc:
            messages.append("CRITICAL: Possible short between VCC and GND")

    # Check floating nets (only one connection) and empty nets (zero connection)
    for net_name, connections in graph.items():
        if not connections or len(connections) == 0:
            messages.append(f"INFO: Net {net_name} has no connections")
        elif len(connections) == 1:
            messages.append(f"WARNING: Net {net_name} is floating (only one connection)")

    return messages