import uuid
from typing import List

from pydantic import BaseModel


class CartItemSchema(BaseModel):
    id: uuid.UUID
    
    cart_id: uuid.UUID
    product_detail_id: uuid.UUID
    product_id: uuid.UUID
    
    object_type: str
    warehouse_code: str
    sku_code: str
    type: str
    quantity: int
    display_price: float
    discounted_price: float

    product: dict
    
    
class CartItemCreateSchema(BaseModel):
    """
    Attributes:
        object_type: This is the data type of object_id, specifically 'product_detail'
        object_id: This is the id of the product detail
        quantity: The quantity of the product detail added to the cart
    Author:
        dev09@allyai.ai
    """
    object_type: str
    object_id: uuid.UUID
    quantity: int
    
class CartItemDeleteMultiSchema(BaseModel):
    """
    Attributes:
        object_ids: A list of product detail ids to be removed from the cart
    Author:
        dev09@allyai.ai
    """
    object_ids: List[uuid.UUID]
    
    

class CartItemEditSchema(BaseModel):
    """
    Attributes:
        object_id: This is the id of the product detail
        quantity: This is the quantity of the product detail updated in the cart
    Author:
        dev09@allyai.ai
    """
    object_id: uuid.UUID
    quantity: int