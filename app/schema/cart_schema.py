import uuid
from typing import List, Optional

from app.schema.cart_item_schema import CartItemSchema
from pydantic import BaseModel


class CartSchema(BaseModel):
    """
    WARN:
        user_id: Optional[uuid.UUID] = None
        store_id: uuid.UUID
    """
    id: uuid.UUID
    
    user_id: Optional[uuid.UUID] = None
    store_id: Optional[uuid.UUID] = None
    
    buyer_id: str
    product_type_id: uuid.UUID
    
    total_item: int
    total_display_price: float
    total_discounted_price: float

    items: List[CartItemSchema]