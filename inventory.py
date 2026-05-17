# inventory.py — Inventory module
def get_stock_value(items, markup):
    total = sum(item['cost'] * item['qty'] for item in items)
    return total * (1 + markup)

def format_currency(amount):
    return f"${amount:.2f}"