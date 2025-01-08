from app.crud.crud_base import CRUDBase


class CartCRUD(CRUDBase):
    def __init__(self):
        super().__init__(prefix="cart", expire_time=86400)  # 24 hour expiry
        

crud_cart = CartCRUD()