"""First duplicate."""

def calculate_invoice_total(items):
    total = 0
    for item in items:
        total = total + item
    return total
