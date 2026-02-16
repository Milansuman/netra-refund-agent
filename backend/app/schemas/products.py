from typing import TypedDict

class Product(TypedDict):
    id: int | None
    title: str
    description: str | None
    price: int
    tax_percent: float
    quantity: int | None