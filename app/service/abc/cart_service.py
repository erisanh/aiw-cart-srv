import uuid
from abc import ABC, abstractmethod

from aioredis import Redis
from fastapi import BackgroundTasks

from app.schema.cart_item_schema import (CartItemCreateSchema,
                                         CartItemDeleteMultiSchema,
                                         CartItemEditSchema)
from app.schema.cart_schema import CartSchema


class CartService(ABC):
    
    @abstractmethod
    async def test(
        self,
        redis: Redis, 
        background_tasks: BackgroundTasks
    ) -> bool:
        pass
    

    @abstractmethod
    async def get_cart_item_list(
        self,
        redis: Redis,
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID,
        buyer_id: str
    ) -> CartSchema:
        pass

    @abstractmethod
    async def add_product_detail_to_cart(
        self, 
        redis: Redis, 
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID, 
        buyer_id: str, 
        product_detail_id: uuid.UUID, 
        cart_item_create: CartItemCreateSchema
    ) -> CartSchema:
        pass
    
    @abstractmethod
    async def delete_one_or_all_items_in_the_cart(
        self, 
        redis: Redis, 
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID, 
        buyer_id: str, 
        cart_item_delete_multi: CartItemDeleteMultiSchema
    ) -> CartSchema:
        pass
    
    @abstractmethod
    async def edit_cart_item(
        self, 
        redis: Redis, 
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID, 
        buyer_id: str, 
        cart_item_edit: CartItemEditSchema
    ) -> CartSchema:
        pass