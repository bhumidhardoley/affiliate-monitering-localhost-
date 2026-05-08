from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: str
    password: str
    company_name: str
    role: str

class affiliate_link(BaseModel):
    user_id: str
    product_id: str
    ref_code: str
    link: str

class Product(BaseModel):
    id: str
    name: str
    category: str
    price: str
    commission: str

class Click(BaseModel):
    user_id: Optional[str] = None
    ref_code: str
    timestamp: Optional[str] = None
    product_id: str

class Sales(BaseModel):
    user_id: Optional[str] = None
    ref_code: str
    timestamp: Optional[str] = None
    product_id: str
    amount: Optional[float] = None