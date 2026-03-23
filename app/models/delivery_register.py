from pydantic import BaseModel,Field,field_serializer
from datetime import datetime, time
from typing import Optional



class DeliveryRegister(BaseModel):
    store_id: str = Field(coerce_numbers_to_str=True)
    open_time: time
    close_time: time
    eta: int
    percentage_service_fee: Optional[float] = None
    service_fee: Optional[float] = None
    product_id: str = Field(coerce_numbers_to_str=True)
    store_status: str
    price: float
    discount_percentage: float
    ui_price: float
    eta_cost: float
    real_price: float
    created_at: datetime
    user_latitude: float
    user_longitude: float
    company: str

    @field_serializer('created_at')
    def serialize_dt(self, dt: datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S.%f')