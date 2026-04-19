def generate_bom(components):
    """
    Generate BOM grouped by (value, footprint, type).

    Returns:
    [
        {
            "value": "5k",
            "type": "Resistor",
            "display_name": "5k Resistor",
            "footprint": "R_0603",
            "count": 10,
            "refs": "R1, R2, R3, R4, R5 (+5 more)"
        }
    ]
    """
    bom_map = {}

    for comp in components:
        # 1. Filter out invalid/non-electrical components
        if not comp.ref or comp.ref == "REF**":
            continue
        
        # Exclude mounting holes and mechanical parts
        if "MountingHole" in comp.footprint or "Mechanical" in comp.footprint:
            continue
            
        # Ignore empty values
        if not comp.value or comp.value.strip() == "":
            continue

        # 2. Improve Value Handling
        val = comp.value
        if val.upper() in ["LEFT", "RIGHT", "UP", "DOWN", "ENTER", "BACK", "PUSH"]:
            footprint_detail = comp.footprint.split(":")[-1]
            if "SW" in footprint_detail or "Push" in footprint_detail:
                val = "Switch"
            else:
                val = footprint_detail

        # 3. Clean Footprint Names
        # Remove library prefix
        footprint = comp.footprint.split(":")[-1]
        # Remove long dimension details (common in KiCad footprints)
        if "_L" in footprint:
            footprint = footprint.split("_L")[0]

        # 4. Determine Component Type
        ref = comp.ref
        if ref.startswith("R"):
            comp_type = "Resistor"
        elif ref.startswith("C"):
            comp_type = "Capacitor"
        elif ref.startswith("U"):
            comp_type = "IC"
        elif ref.startswith("D"):
            comp_type = "Diode"
        elif ref.startswith("Q"):
            comp_type = "Transistor"
        elif ref.startswith("SW") or ref.startswith("S"):
            comp_type = "Switch"
        elif ref.startswith("J") or ref.startswith("P"):
            comp_type = "Connector"
        else:
            comp_type = "Component"

        # 5. Create Grouping Key
        key = (val, footprint, comp_type)
        
        if key not in bom_map:
            bom_map[key] = {
                "value": val,
                "type": comp_type,
                "display_name": f"{val} {comp_type}",
                "footprint": footprint,
                "count": 0,
                "refs": set()
            }

        # 6. Add unique reference
        if comp.ref not in bom_map[key]["refs"]:
            bom_map[key]["refs"].add(comp.ref)
            bom_map[key]["count"] += 1

    # 7. Prepare Final Output
    bom_list = []
    for item in bom_map.values():
        # Limit Long Reference Lists
        refs_list = sorted(list(item["refs"]))
        if len(refs_list) > 5:
            display_refs = refs_list[:5]
            extra = len(refs_list) - 5
            item["refs"] = ", ".join(display_refs) + f" (+{extra} more)"
        else:
            item["refs"] = ", ".join(refs_list)
        
        bom_list.append(item)

    # 8. Sort by Component Type then Value
    return sorted(bom_list, key=lambda x: (x["type"], x["value"]))
