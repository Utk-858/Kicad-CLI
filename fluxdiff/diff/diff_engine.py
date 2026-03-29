from fluxdiff.models.pcb_models import PCBData, DiffResult
import math
from fluxdiff.analysis.connectivity_graph import build_connectivity_graph, compare_connectivity
from fluxdiff.analysis.erc_checker import run_erc_checks

# ---------- Thresholds ----------
MOVE_THRESHOLD = 0.05     # mm
ROT_THRESHOLD = 1.0       # degrees
TRACE_ROUND = 5           # decimal precision for routing comparison


# ---------- Main API ----------
def compare_pcbs(old_pcb: PCBData, new_pcb: PCBData) -> DiffResult:
    result = DiffResult()

    # These will be filled in by component_diff
    component_stats = component_diff(old_pcb, new_pcb, result)
    net_diff(old_pcb, new_pcb, result)
    routing_diff(old_pcb, new_pcb, result)

    # --- Connectivity graph analysis ---
    graph_old = build_connectivity_graph(old_pcb)
    graph_new = build_connectivity_graph(new_pcb)
    connectivity_changes = compare_connectivity(graph_old, graph_new)
    result.net_changes.extend([f"CONNECTIVITY: {msg}" for msg in connectivity_changes])

    # --- ERC Checks ---
    erc_old = set(run_erc_checks(graph_old))
    erc_new = set(run_erc_checks(graph_new))
    new_erc_issues = erc_new - erc_old  # only warnings that are NEW in after
    result.net_changes.extend([f"ERC: {msg}" for msg in sorted(new_erc_issues)])

    # Sort outputs for consistent reporting
    result.net_changes.sort()
    result.routing_changes.sort()

    # Create summary
    summary_lines = []
    summary_lines.append("SUMMARY")
    summary_lines.append("-------")
    summary_lines.append(f"Components added: {component_stats['added']}")
    summary_lines.append(f"Components removed: {component_stats['removed']}")
    summary_lines.append(f"Components modified: {component_stats['modified']}")
    summary_lines.append(f"Net changes: {len(result.net_changes)}")
    summary_lines.append(f"Routing changes: {len(result.routing_changes)}")
    result.summary = "\n".join(summary_lines)

    return result


# ---------- Component Comparison ----------
def component_diff(old_pcb: PCBData, new_pcb: PCBData, result: DiffResult):
    # Helper to determine if a ref is valid (not placeholder/empty)
    def is_real_ref(ref):
        return bool(ref) and ref != "REF**"

    # Helper to compare positions with tolerance
    def pos_equal(pos1, pos2, tol):
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1]) <= tol

    # Filter components to ignore placeholder/empty references
    old_components = {c.ref: c for c in old_pcb.components if is_real_ref(c.ref)}
    new_components = {c.ref: c for c in new_pcb.components if is_real_ref(c.ref)}

    # Prepare lists to store grouped changes
    added = []
    removed = []
    modified = []
    modified_refs = set()

    # For swap detection: build position lookups for shared components
    shared_refs = sorted(old_components.keys() & new_components.keys())
    old_positions = {ref: (old_components[ref].x, old_components[ref].y) for ref in shared_refs}
    new_positions = {ref: (new_components[ref].x, new_components[ref].y) for ref in shared_refs}

    # Track which refs have been swapped or reported as a normal move
    swapped_refs = set()
    swap_msgs = []

    # Added components
    for ref in sorted(new_components.keys() - old_components.keys()):
        added.append(f"Component added: {ref}")

    # Removed components
    for ref in sorted(old_components.keys() - new_components.keys()):
        removed.append(f"Component removed: {ref}")

    # Detect swaps before individual moves
    # For each shared ref that moved, check if it swapped with another
    for i, ref_a in enumerate(shared_refs):
        if ref_a in swapped_refs:
            continue
        old_a = old_positions[ref_a]
        new_a = new_positions[ref_a]
        # Did ref_a move?
        if not pos_equal(old_a, new_a, MOVE_THRESHOLD):
            # Search for a possible swap pair (ref_b)
            for ref_b in shared_refs[i+1:]:
                if ref_b in swapped_refs or ref_a == ref_b:
                    continue
                old_b = old_positions[ref_b]
                new_b = new_positions[ref_b]
                # Both must have moved
                if not pos_equal(old_b, new_b, MOVE_THRESHOLD):
                    # If ref_a moved to old_b's position, and ref_b moved to old_a's position, within MOVE_THRESHOLD
                    if pos_equal(new_a, old_b, MOVE_THRESHOLD) and pos_equal(new_b, old_a, MOVE_THRESHOLD):
                        # Report swap, making ref order deterministic
                        r1, r2 = sorted([ref_a, ref_b])
                        swap_msgs.append(f"Components swapped: {r1} <-> {r2}")
                        swapped_refs.add(ref_a)
                        swapped_refs.add(ref_b)
                        break  # Only one swap per ref

    # Now do standard per-component comparison (but skip swapped refs)
    for ref in shared_refs:
        if ref in swapped_refs:
            continue  # Already reported as swapped

        old_c = old_components[ref]
        new_c = new_components[ref]
        changed = False

        # Movement
        distance = math.hypot(old_c.x - new_c.x, old_c.y - new_c.y)
        if distance > MOVE_THRESHOLD:
            modified.append(
                f"Component moved: {ref} ({old_c.x},{old_c.y} -> {new_c.x},{new_c.y})"
            )
            changed = True

        # Value change
        if old_c.value != new_c.value:
            modified.append(
                f"Component value changed: {ref} {old_c.value} -> {new_c.value}"
            )
            changed = True

        # Footprint change
        if old_c.footprint != new_c.footprint:
            modified.append(
                f"Component footprint changed: {ref} {old_c.footprint} -> {new_c.footprint}"
            )
            changed = True

        # Layer change
        if old_c.layer != new_c.layer:
            modified.append(
                f"Component layer changed: {ref} {old_c.layer} -> {new_c.layer}"
            )
            changed = True

        # Rotation change
        if abs(old_c.rotation - new_c.rotation) > ROT_THRESHOLD:
            modified.append(
                f"Component rotation changed: {ref} {old_c.rotation} -> {new_c.rotation}"
            )
            changed = True

        if changed:
            modified_refs.add(ref)

    # Maintain result.component_changes as a flat list, but ordered/grouped for readability
    result.component_changes.extend(added)
    result.component_changes.extend(removed)
    result.component_changes.extend(swap_msgs)
    result.component_changes.extend(modified)

    # For stats: count swapped pairs as one modification for each component
    n_mods = len(modified_refs) + len(swapped_refs)

    return {
        "added": len(added),
        "removed": len(removed),
        "modified": n_mods // 2 if n_mods and len(swapped_refs) > 0 else len(modified_refs) + len(swapped_refs),
    }


# ---------- Net Comparison ----------
def net_diff(old_pcb: PCBData, new_pcb: PCBData, result: DiffResult):

    def build_pad_map(components):
        pad_map = {}

        for comp in components:
            if not comp.ref or comp.ref == "REF**":
                continue

            for pad in comp.pads:
                if not pad.number:
                    continue

                pad_map[(comp.ref, pad.number)] = pad.net

        return pad_map

    old_map = build_pad_map(old_pcb.components)
    new_map = build_pad_map(new_pcb.components)

    all_pads = set(old_map.keys()) | set(new_map.keys())

    for pad_key in all_pads:
        old_net = old_map.get(pad_key)
        new_net = new_map.get(pad_key)

        if old_net != new_net:
            ref, pad_num = pad_key
            if not ref:
                continue

            # Pad changed from one net to another
            if old_net is not None and new_net is not None:
                result.net_changes.append(
                    f"CRITICAL: {ref} pad {pad_num} changed from {old_net} -> {new_net}"
                )
            # Pad got connected (None -> net)
            elif old_net is None and new_net is not None:
                result.net_changes.append(
                    f"INFO: {ref} pad {pad_num} connected to {new_net}"
                )
            # Pad became disconnected (net -> None)
            elif old_net is not None and new_net is None:
                # Only report if the pad still exists in the new file (not just unresolved)
                if any(c.ref == ref for c in new_pcb.components):
                   result.net_changes.append(
                      f"WARNING: {ref} pad {pad_num} disconnected from {old_net}"
        )


# ---------- Routing Comparison ----------
def routing_diff(old_pcb: PCBData, new_pcb: PCBData, result: DiffResult):

    # ----- Trace normalization -----
    def trace_key(trace):

        start = tuple(round(coord, TRACE_ROUND) for coord in trace.start)
        end = tuple(round(coord, TRACE_ROUND) for coord in trace.end)

        # normalize direction (A->B same as B->A)
        if start > end:
            start, end = end, start

        return (trace.layer, start, end, trace.net)

    old_traces = set(trace_key(t) for t in old_pcb.traces)
    new_traces = set(trace_key(t) for t in new_pcb.traces)

    # Added traces
    for trace in new_traces - old_traces:
        result.routing_changes.append(
            f"Trace added: net {trace[3]}, layer {trace[0]}, from {trace[1]} to {trace[2]}"
        )

    # Removed traces
    for trace in old_traces - new_traces:
        # The original code simply reports removed traces.
        result.routing_changes.append(
            f"Trace removed: net {trace[3]}, layer {trace[0]}, from {trace[1]} to {trace[2]}"
        )

    # ----- Via normalization -----
    def via_key(via):
        return (
            round(via.x, TRACE_ROUND),
            round(via.y, TRACE_ROUND),
            via.net,
        )

    old_vias = set(via_key(v) for v in old_pcb.vias)
    new_vias = set(via_key(v) for v in new_pcb.vias)

    for via in new_vias - old_vias:
        result.routing_changes.append(
            f"Via added: net {via[2]}, at ({via[0]}, {via[1]})"
        )

    for via in old_vias - new_vias:
        result.routing_changes.append(
            f"Via removed: net {via[2]}, at ({via[0]}, {via[1]})"
        )