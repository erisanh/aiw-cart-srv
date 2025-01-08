import uuid

from aioredis import Redis
from fastapi import APIRouter, BackgroundTasks, Depends

from app.api import deps
from app.schema.cart_item_schema import (CartItemCreateSchema,
                                         CartItemDeleteMultiSchema,
                                         CartItemEditSchema)
from app.schema.cart_schema import CartSchema
from app.service.abc.cart_service import CartService
from app.service.impl.cart_service_impl import CartServiceImpl

cart_service: CartService = CartServiceImpl()
router = APIRouter()

@router.get("/test", status_code=200)
async def test(
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(deps.get_redis),
) -> bool:
    return await cart_service.test(
        redis=redis,
        background_tasks=background_tasks
    )


@router.get("/cart?store_id={store_id}&buyer_id={buyer_id}", 
                response_model=CartSchema,
                status_code=200
            )
async def get_cart_item_list(
    store_id: uuid.UUID,
    buyer_id: str,
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(deps.get_redis),
) -> CartSchema:
    return await cart_service.get_cart_item_list(
        redis=redis,
        background_tasks=background_tasks,
        store_id=store_id,
        buyer_id=buyer_id
    )

@router.post("/cart?store_id={store_id}&buyer_id={buyer_id}&product_detail_id={product_detail_id}", 
                response_model=CartSchema,
                status_code=201
            )
async def add_product_detail_to_cart(
    store_id: uuid.UUID,
    buyer_id: str,
    product_detail_id: uuid.UUID,
    cart_item_create: CartItemCreateSchema,
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(deps.get_redis),
) -> CartSchema:
    return await cart_service.add_product_detail_to_cart(
        redis=redis,
        background_tasks=background_tasks,
        store_id=store_id,
        buyer_id=buyer_id,
        product_detail_id=product_detail_id,
        cart_item_create=cart_item_create
    )
    
@router.delete("/cart?store_id={store_id}&buyer_id={buyer_id}", 
                response_model=CartSchema,
                status_code=200
            )
async def delete_one_or_all_items_in_the_cart(
    store_id: uuid.UUID,
    buyer_id: str,
    cart_item_delete_multi: CartItemDeleteMultiSchema,
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(deps.get_redis),
) -> CartSchema:
    return await cart_service.delete_one_or_all_items_in_the_cart(
        redis=redis,
        background_tasks=background_tasks,
        store_id=store_id,
        buyer_id=buyer_id,
        cart_item_delete_multi=cart_item_delete_multi
    )
    
@router.put("/cart?store_id={store_id}&buyer_id={buyer_id}",
                response_model=CartSchema,
                status_code=200
            )
async def edit_cart_item(
    store_id: uuid.UUID,
    buyer_id: str,
    cart_item_edit: CartItemEditSchema,
    background_tasks: BackgroundTasks,
    redis: Redis = Depends(deps.get_redis),
) -> CartSchema:
    return await cart_service.edit_cart_item(
        redis=redis,
        background_tasks=background_tasks,
        store_id=store_id,
        buyer_id=buyer_id,
        cart_item_edit=cart_item_edit
    )