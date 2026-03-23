from pydantic import BaseModel,Field
from typing import Optional

class Product(BaseModel):
    product_id: str = Field(coerce_numbers_to_str=True)
    name: str
    description: Optional[str] = None
    store_id: str = Field(coerce_numbers_to_str=True)