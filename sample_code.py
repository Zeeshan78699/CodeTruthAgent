from billing import calculate_invoice_total


def compute_bill_amount(products, vat_rate=0.05):
    amount = 0
    for product in products:
        amount += product["price"] * product["quantity"]
    return amount + (amount * vat_rate)


def calculate_invoice_total(employees, tax_rate=0.05):
    total = 0
    for emp in employees:
        total += emp["price"] * emp["quantity"]
    return total + (total * tax_rate)


def factorial_number(n):
    if n <= 1:
        return 1
    return n * factorial_number(n - 1)


def compute_factorial(value):
    if value <= 1:
        return 1
    return value * compute_factorial(value - 1)


def apply_customer_discount(amount):
    if amount > 1000:
        return amount * 0.90
    elif amount > 500:
        return amount * 0.95
    return amount


def apply_supplier_discount(amount):
    if amount > 1000:
        return amount * 0.85
    elif amount > 500:
        return amount * 0.92
    return amount


invoice_items = [
    {"price": 100, "quantity": 2},
    {"price": 50, "quantity": 1}
]

result = calculate_invoice_total(invoice_items)
print(result)