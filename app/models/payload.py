from pydantic import BaseModel, ConfigDict, model_serializer
from .delivery_register import DeliveryRegister
from .product import Product
from .store import Store


class Payload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    store: Store
    product: Product
    delivery_register: DeliveryRegister
    
    @model_serializer
    def serialize_model(self):
        data = {
            "store": self.store,
            "product": self.product,
        }
        delivery_data = self.delivery_register.model_dump() 
        return {**data, **delivery_data}