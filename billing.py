def calculate_invoice_total(items, tax_rate=0.05):
    total = 0
    for item in items:
        total += item["price"] * item["quantity"]
    return total + (total * tax_rate)