from pydantic import BaseModel,Field
from typing import Optional

class Store(BaseModel):
    store_id: str = Field(coerce_numbers_to_str=True)
    name: str
    url: Optional[str] = None
    address: str
    postal_code: Optional[str] = None
    latitude: float
    longitude: float





