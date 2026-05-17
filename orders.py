def generate_order_summary(order):
    total = 0
    for item in order["items"]:
        total += item["price"] * item["quantity"]

    return {
        "status": "confirmed",
        "total": total
    }