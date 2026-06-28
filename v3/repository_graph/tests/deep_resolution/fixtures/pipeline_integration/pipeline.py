
from services import UserService, ProductService, create_service

def run_pipeline():
    names = ["alice", "bob", "charlie"]
    emails = [f"{n}@example.com" for n in names]

    user_service = UserService()
    for name, email in zip(names, emails):
        user = user_service.create_user(name, email)
        display = user.get_display_name()

    product_service = create_service("product")
    items = ["Widget", "Gadget", "Tool"]
    prices = [9.99, 19.99, 29.99]
    products = []
    for title, price in zip(items, prices):
        p = product_service.create_product(title, price)
        products.append(p.to_dict())

    all_users = user_service.get_all()
    result = {
        "users": len(all_users),
        "products": len(products),
    }
    return result
