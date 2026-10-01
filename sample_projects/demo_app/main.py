"""Demo app main entrypoint for testing code tracing and memory profiling."""

import time
from sample_projects.demo_app.utils import calculate_totals, simulate_memory_growth

def main():
    print("Starting demo app...")
    items = [
        {"name": "Item A", "price": 100, "quantity": 3},
        {"name": "Item B", "price": 250, "quantity": 2},
        {"name": "Item C", "price": 45, "quantity": 10},
    ]

    total, count = calculate_totals(items)
    print(f"Calculated total: ${total:.2f} across {count} items.")

    data = simulate_memory_growth(cycles=50)
    print(f"Simulated data payload size: {len(data)} items.")


if __name__ == "__main__":
    main()
