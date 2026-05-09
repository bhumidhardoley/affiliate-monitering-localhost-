import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import users_collection , affiliate_links , products_collection , click_collection,sales_collection
from models import User , Sales
import jwt
from fastapi import Response ,HTTPException ,Request
import bcrypt
import uuid
from models import Click
from datetime import datetime, timezone
from bson import ObjectId
from fastapi import APIRouter


app = FastAPI()
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type","Authorization"]
)

SECRET_KEY ="IamBhumidharDoley123@atKazirangaUniversityStudying"


new_products = [
    {
        "name": "Apple iPhone 15 Pro",
        "category": "Mobiles",
        "price": "134900",
        "commission": "3"
    },
    {
        "name": "Sony WH-1000XM5 Wireless Headphones",
        "category": "Audio",
        "price": "29990",
        "commission": "8"
    },
    {
        "name": "MacBook Air M2 13-inch",
        "category": "Electronics",
        "price": "114900",
        "commission": "5"
    },
    {
        "name": "Levi's 511 Slim Fit Jeans",
        "category": "Fashion",
        "price": "3499",
        "commission": "12"
    },
    {
        "name": "Samsung Galaxy S24 Ultra",
        "category": "Mobiles",
        "price": "129999",
        "commission": "4"
    },
    {
        "name": "Marshall Emberton II Speaker",
        "category": "Audio",
        "price": "14999",
        "commission": "10"
    },
    {
        "name": "Logitech MX Master 3S Mouse",
        "category": "Accessories",
        "price": "10995",
        "commission": "7"
    },
    {
        "name": "Ray-Ban Aviator Classic",
        "category": "Fashion",
        "price": "12490",
        "commission": "15"
    },
    {
        "name": "Dell UltraSharp 27 Monitor",
        "category": "Electronics",
        "price": "45000",
        "commission": "6"
    },
    {
        "name": "Apple Watch Series 9",
        "category": "Accessories",
        "price": "41900",
        "commission": "5"
    }
]
# This will insert all 10 products at once
result = products_collection.insert_many(new_products)
print(f"Successfully inserted {len(result.inserted_ids)} products.")



@app.post("/signup")
async def singup(user: User,response: Response):
    if users_collection.find_one({"name":user.name,"company_name":user.company_name}):
        raise HTTPException(status_code=401,detail="User already exist")
    
    user_dict = user.model_dump()

    hased_password = bcrypt.hashpw(
        user_dict["password"].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    user_dict["password"] = hased_password
    
    users_collection.insert_one(user_dict)

    if "_id" in user_dict:
        user_dict["_id"] = str(user_dict["_id"])


    payload = {
        "user_id":user_dict["_id"],
        "name":user_dict["name"],
        "company_name":user_dict["company_name"],
        "role":user_dict["role"]
    }
    token = jwt.encode(payload,SECRET_KEY,algorithm="HS256")

    response.set_cookie(
        key="affiliatetracker",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
        secure=False
    )

    return {"message":"Account created and cookie set"}

@app.post("/generate-link")
async def generate_link(request: Request):

    token = request.cookies.get("affiliatetracker")

    if not token:
        raise HTTPException(status_code=401,detail="Not authenticated")
    
    try:
        payload = jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401,detail="Invalid Token")
    
    data = await request.json()
    product_id = data.get("product_id")

    if not product_id:
        raise HTTPException(status_code=400,detail="Product Id required")
    
    ref_code = uuid.uuid4().hex[:8]  
    link = f"http://localhost:3000/product?ref={ref_code}&product_id={product_id}"

    doc = {
        "user_id":user_id,
        "product_id": product_id,
        "ref_code": ref_code,
        "link":link
    }
    affiliate_links.insert_one(doc)
    return{"link":link}


@app.get("/products")
async def get_products():
    products = []
    for product in products_collection.find({}):
        product["id"] = str(product["_id"])
        del product["_id"]
        products.append(product)

    return {"products":products}

@app.post("/track-click")
async def track_click(click_data: Click,):
    
    click_dict = click_data.model_dump()

    affiliate = affiliate_links.find_one({
        "ref_code": click_dict["ref_code"],
    })
    
    if not affiliate:
        raise HTTPException(status_code=400,detail="Invalid ref code")
    
    click_dict["user_id"] = affiliate["user_id"]

    # adding server-side timestamp for accuracy
    click_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        click_collection.insert_one(click_dict)
        return {"status":"success","message":"Click tracked successfully"}
    except Exception as e:
        raise HTTPException(status_code=500,detail="Failed to track click")


@app.get("/admin/stats")
async def get_admin_stats():
    # Count total users with the role 'client' (affiliates)
    total_affiliates = users_collection.count_documents({"role": "client"})
    total_clicks = click_collection.count_documents({})
    total_sales = sales_collection.count_documents({})
    
    # Count every document in the affiliate_links collection
    total_links = affiliate_links.count_documents({})
    sales = sales_collection.find({})
    total_reveneu = 0
    for sale in sales:
        total_reveneu += sale["amount"]
    
    return {
        "totalAffiliates": total_affiliates,
        "totalLinks": total_links,
        "totalClicks": total_clicks,
        "totalSales": total_sales,
        "totalRevenue": total_reveneu
    }




@app.get("/admin/affiliates-summary")
async def get_affiliates_summary():
    affiliates = list(users_collection.find({"role": "client"}))
    summary_data = []
    
    total_network_clicks = 0
    total_network_links = 0

    for affiliate in affiliates:
        user_id = str(affiliate["_id"])
        link_count = affiliate_links.count_documents({"user_id": user_id})
        total_clicks = click_collection.count_documents({"user_id": user_id})

        total_network_clicks += total_clicks
        total_network_links += link_count

        summary_data.append({
            "id": user_id,
            "name": affiliate["name"],
            "company": affiliate["company_name"],
            "linkCount": link_count,
            "totalClicks": total_clicks
        })

    # Sort to find the best performer (highest clicks)
    best_performer = None
    if summary_data:
        best_performer = max(summary_data, key=lambda x: x['totalClicks'])

    return {
        "affiliates": summary_data,
        "bestPerformer": best_performer,
        "networkStats": {
            "totalClicks": total_network_clicks,
            "totalLinks": total_network_links
        }
    }
@app.post("/register-sale")
async def register_sale(sale: Sales):

    sale_dict = sale.model_dump()

    products = products_collection.find_one({
        "_id": ObjectId(sale_dict["product_id"])
    })

    sale_dict["amount"] = float(products["price"])

    # Add timestamp
    sale_dict["timestamp"] = datetime.now(
        timezone.utc
    ).isoformat()

    sales_collection.insert_one(sale_dict)

    return {
        "status": "success",
        "message": "Sale registered successfully"
    }

@app.post("/login")
async def login(request: Request, response: Response):

    data = await request.json()

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        raise HTTPException(
            status_code=400,
            detail="Name and password required"
        )

    user = users_collection.find_one({
        "name": name
    })

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    password_match = bcrypt.checkpw(
        password.encode('utf-8'),
        user["password"].encode('utf-8')
    )

    if not password_match:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    payload = {
        "user_id": str(user["_id"]),
        "name": user["name"],
        "company_name": user["company_name"],
        "role": user["role"]
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm="HS256"
    )

    response.set_cookie(
        key="affiliatetracker",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=86400
    )

    return {
        "message": "Login successful",
        "role": user["role"]
    }    




@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie("affiliatetracker")
    return {"message":"Logged out successfully"}

@app.get("/admin/click-sales-graph")
async def click_sales_graph():

    clicks = list(click_collection.find({}))
    sales = list(sales_collection.find({}))

    stats = {}

    # Count clicks per day
    for click in clicks:

        date = click["timestamp"][:10]

        if date not in stats:
            stats[date] = {
                "date": date,
                "clicks": 0,
                "sales": 0
            }

        stats[date]["clicks"] += 1

    # Count sales per day
    for sale in sales:

        date = sale["timestamp"][:10]

        if date not in stats:
            stats[date] = {
                "date": date,
                "clicks": 0,
                "sales": 0
            }

        stats[date]["sales"] += 1

    result = sorted(
        stats.values(),
        key=lambda x: x["date"]
    )

    return result


@app.get("/admin/revenue-graph")
async def revenue_graph():

    sales = list(sales_collection.find({}))

    revenue_stats = {}

    for sale in sales:

        date = sale["timestamp"][:10]

        if date not in revenue_stats:
            revenue_stats[date] = {
                "date": date,
                "revenue": 0
            }

        revenue_stats[date]["revenue"] += sale["amount"]

    result = sorted(
        revenue_stats.values(),
        key=lambda x: x["date"]
    )

    return result

@app.get("/me")
async def get_current_user(request: Request):

    token = request.cookies.get("affiliatetracker")

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )

        return {
            "user_id": payload["user_id"],
            "name": payload["name"],
            "company_name": payload["company_name"],
            "role": payload["role"]
        }

    except:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )