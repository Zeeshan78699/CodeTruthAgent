def generate_finance_report(report):
    grand_total = 0
    for item in report["items"]:
        grand_total += item["price"] * item["quantity"]

    return {
        "report_type": "finance",
        "grand_total": grand_total
    }