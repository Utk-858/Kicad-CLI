import random
import time

def fetch_inventory_from_erp(component_value: str):
    """
    Simulates an ERP API call to fetch stock availability.
    """

    # Simulate network delay
    time.sleep(0.1)

    # Simulated stock values
    stock = random.choice([0, 1, 2, 5, 10, 50])

    return {
        "value": component_value,
        "stock": stock
    }
