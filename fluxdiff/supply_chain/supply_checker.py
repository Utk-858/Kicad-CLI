from fluxdiff.supply_chain.erp_service import fetch_inventory_from_erp

def check_bom_with_erp(bom):
    """
    Compare BOM with ERP inventory.
    """

    results = []

    for item in bom:
        erp_data = fetch_inventory_from_erp(item["value"])

        stock = erp_data["stock"]
        required = item["count"]

        if stock == 0:
            status = "CRITICAL"
        elif stock < required:
            status = "WARNING"
        else:
            status = "OK"

        results.append({
            "name": item["display_name"],
            "required": required,
            "stock": stock,
            "status": status
        })

    return results
