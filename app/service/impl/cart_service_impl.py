import uuid

from aioredis import Redis
from fastapi import BackgroundTasks

from app.crud.crud_cart import crud_cart
from app.schema.cart_item_schema import (CartItemCreateSchema,
                                         CartItemDeleteMultiSchema,
                                         CartItemEditSchema)
from app.schema.cart_schema import CartSchema
from app.service.abc.cart_service import CartService
from app.util.logger import setup_logger

logger = setup_logger()


class CartServiceImpl(CartService):
    def __init__(self):
        self._crud_cart = crud_cart
    
    async def test(
        self,
        redis: Redis,
        background_tasks: BackgroundTasks
    ) -> bool:
        """
        Test all CRUD operations in CRUDBase to ensure correctness.
        
        Args:
            redis (Redis): Redis connection instance
            background_tasks (BackgroundTasks): FastAPI BackgroundTasks for logging
            
        Returns:
            bool: True if all operations succeed, False otherwise
        """
        try:
            logger.info("Starting CRUDBase test operations...")

            # Test set
            test_set = await self._crud_cart.set(redis=redis, key="fb123456789", value={"name": "TestUser", "age": 25})
            background_tasks.add_task(logger.info, f"Set operation successful: {test_set}")

            # Test get
            test_value = await self._crud_cart.get(redis=redis, key="fb123456789")
            background_tasks.add_task(logger.info, f"Get operation result: {test_value}")

            # # Test exists
            # exists = await self._crud_cart.exists(redis=redis, key="test")
            # background_tasks.add_task(logger.info, f"Exists operation result: {exists}")

            # # Test expire
            # expire_result = await self._crud_cart.expire(redis=redis, key="test", seconds=10)
            # background_tasks.add_task(logger.info, f"Expire operation successful: {expire_result}")

            # # Test TTL
            # ttl = await self._crud_cart.ttl(redis=redis, key="test")
            # background_tasks.add_task(logger.info, f"TTL operation result: {ttl} seconds remaining")

            # # Test incr
            # await self._crud_cart.set(redis=redis, key="counter", value=0)  # Initialize counter
            # incr_value = await self._crud_cart.incr(redis=redis, key="counter")
            # background_tasks.add_task(logger.info, f"Incr operation result: {incr_value}")

            # # Test hset
            # hset_result = await self._crud_cart.hset(redis=redis, key="test_hash", mapping={"field1": "value1", "field2": "value2"})
            # background_tasks.add_task(logger.info, f"HSet operation result: {hset_result}")

            # # Test hget
            # hget_value = await self._crud_cart.hget(redis=redis, key="test_hash", field="field1")
            # background_tasks.add_task(logger.info, f"HGet operation result for 'field1': {hget_value}")

            # # Test delete
            # delete_result = await self._crud_cart.delete(redis=redis, key="test")
            # background_tasks.add_task(logger.info, f"Delete operation successful: {delete_result}")

            # # Test key existence after deletion
            # exists_after_delete = await self._crud_cart.exists(redis=redis, key="test")
            # background_tasks.add_task(logger.info, f"Exists after delete: {exists_after_delete}")

            # Log success if all operations completed without errors
            logger.info("All CRUDBase test operations completed successfully.")
            return True

        except Exception as e:
            logger.error(f"Error during CRUDBase test operations: {e}")
            return False

    async def get_cart_item_list(
        self,
        redis: Redis,
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID,
        buyer_id: str
    ) -> CartSchema:
        pass

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
    
    async def delete_one_or_all_items_in_the_cart(
        self, 
        redis: Redis, 
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID, 
        buyer_id: str, 
        cart_item_delete_multi: CartItemDeleteMultiSchema
    ) -> CartSchema:
        pass
    
    async def edit_cart_item(
        self, 
        redis: Redis, 
        background_tasks: BackgroundTasks,
        store_id: uuid.UUID, 
        buyer_id: str, 
        cart_item_edit: CartItemEditSchema
    ) -> CartSchema:
        pass