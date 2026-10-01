"""Utility functions for demo application."""

def calculate_totals(items: list[dict]) -> tuple[float, int]:
    total_price = 0.0
    total_quantity = 0

    for item in items:
        price = item.get("price", 0.0)
        quantity = item.get("quantity", 0)
        subtotal = price * quantity
        total_price += subtotal
        total_quantity += quantity

    return total_price, total_quantity


def simulate_memory_growth(cycles: int = 10) -> list[bytes]:
    buf = []
    for i in range(cycles):
        buf.append(b"X" * (100 * 1024))  # 100KB chunks
    return buf
