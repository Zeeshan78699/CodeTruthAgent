
from models import User, Product

class UserService:
    def __init__(self):
        self.users = []
    def create_user(self, name: str, email: str) -> User:
        user = User(name, email)
        user.save()
        self.users.append(user)
        return user
    def get_all(self) -> list:
        return self.users.copy()

class ProductService:
    def create_product(self, title: str, price: float) -> Product:
        product = Product(title, price)
        product.save()
        return product

def create_service(service_type: str):
    if service_type == "user":
        return UserService()
    return ProductService()
