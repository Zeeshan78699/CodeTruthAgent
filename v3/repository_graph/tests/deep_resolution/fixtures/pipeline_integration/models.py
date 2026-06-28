
class BaseModel:
    def save(self): pass
    def delete(self): pass
    def to_dict(self): return {}

class User(BaseModel):
    def __init__(self, name: str, email: str):
        self.name = name
        self.email = email
    def get_display_name(self): return self.name.upper()

class Product(BaseModel):
    def __init__(self, title: str, price: float):
        self.title = title
        self.price = price
    @property
    def formatted_price(self): return f"${self.price:.2f}"
