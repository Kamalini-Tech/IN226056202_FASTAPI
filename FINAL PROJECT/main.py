from fastapi import FastAPI, Query, Response
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# ------------------ DATA ------------------

menu = [
    {"id": 1, "name": "Pizza", "price": 200, "category": "Pizza", "is_available": True},
    {"id": 2, "name": "Burger", "price": 120, "category": "Burger", "is_available": True},
    {"id": 3, "name": "Coke", "price": 50, "category": "Drink", "is_available": True},
    {"id": 4, "name": "Ice Cream", "price": 80, "category": "Dessert", "is_available": False},
    {"id": 5, "name": "Fries", "price": 90, "category": "Snack", "is_available": True},
    {"id": 6, "name": "Sandwich", "price": 110, "category": "Snack", "is_available": True},
]

orders = []
order_counter = 1

cart = []

# ------------------ MODELS ------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    item_id: int = Field(gt=0)
    quantity: int = Field(gt=0, le=20)
    delivery_address: str = Field(min_length=10)
    order_type: str = "delivery"

class NewMenuItem(BaseModel):
    name: str = Field(min_length=2)
    price: int = Field(gt=0)
    category: str = Field(min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str

# ------------------ HELPERS ------------------

def find_menu_item(item_id):
    for item in menu:
        if item["id"] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type="delivery"):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

def filter_menu_logic(category, max_price, is_available):
    result = []
    for item in menu:
        if category is not None and item["category"] != category:
            continue
        if max_price is not None and item["price"] > max_price:
            continue
        if is_available is not None and item["is_available"] != is_available:
            continue
        result.append(item)
    return result

# ------------------ Q1 ------------------

@app.get("/")
def home():
    return {"message": "Welcome to QuickBite Food Delivery"}

# ------------------ Q2 ------------------

@app.get("/menu")
def get_menu():
    return {"menu": menu, "total": len(menu)}

# ------------------ Q5 (BEFORE ID ROUTE) ------------------

@app.get("/menu/summary")
def menu_summary():
    available = [i for i in menu if i["is_available"]]
    categories = list(set([i["category"] for i in menu]))
    return {
        "total": len(menu),
        "available": len(available),
        "unavailable": len(menu) - len(available),
        "categories": categories
    }

# ------------------ Q3 ------------------

@app.get("/menu/{item_id}")
def get_item(item_id: int):
    item = find_menu_item(item_id)
    if item:
        return item
    return {"error": "Item not found"}

# ------------------ Q4 ------------------

@app.get("/orders")
def get_orders():
    return {"orders": orders, "total_orders": len(orders)}

# ------------------ Q6 + Q8 ------------------

@app.post("/orders")
def create_order(order: OrderRequest):
    global order_counter

    item = find_menu_item(order.item_id)
    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item not available"}

    total = calculate_bill(item["price"], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item": item["name"],
        "quantity": order.quantity,
        "total_price": total
    }

    orders.append(new_order)
    order_counter += 1

    return new_order

# ------------------ Q10 ------------------

@app.get("/menu/filter")
def filter_menu(category: Optional[str] = None,
                max_price: Optional[int] = None,
                is_available: Optional[bool] = None):

    result = filter_menu_logic(category, max_price, is_available)
    return {"items": result, "count": len(result)}

# ------------------ Q11 ------------------

@app.post("/menu")
def add_menu(item: NewMenuItem, response: Response):
    for i in menu:
        if i["name"].lower() == item.name.lower():
            return {"error": "Duplicate item"}

    new_item = item.dict()
    new_item["id"] = len(menu) + 1
    menu.append(new_item)

    response.status_code = 201
    return new_item

# ------------------ Q12 ------------------

@app.put("/menu/{item_id}")
def update_menu(item_id: int,
                price: Optional[int] = None,
                is_available: Optional[bool] = None):

    item = find_menu_item(item_id)
    if not item:
        return {"error": "Not found"}

    if price is not None:
        item["price"] = price
    if is_available is not None:
        item["is_available"] = is_available

    return item

# ------------------ Q13 ------------------

@app.delete("/menu/{item_id}")
def delete_menu(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Not found"}

    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

# ------------------ Q14 ------------------

@app.post("/cart/add")
def add_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)

    if not item:
        return {"error": "Item not found"}

    if not item["is_available"]:
        return {"error": "Item unavailable"}

    for c in cart:
        if c["item_id"] == item_id:
            c["quantity"] += quantity
            return {"message": "Updated cart"}

    cart.append({"item_id": item_id, "name": item["name"], "quantity": quantity, "price": item["price"]})
    return {"message": "Added to cart"}

@app.get("/cart")
def get_cart():
    total = sum(i["price"] * i["quantity"] for i in cart)
    return {"cart": cart, "grand_total": total}

# ------------------ Q15 ------------------

@app.delete("/cart/{item_id}")
def remove_cart(item_id: int):
    for c in cart:
        if c["item_id"] == item_id:
            cart.remove(c)
            return {"message": "Removed"}
    return {"error": "Item not in cart"}

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest, response: Response):
    global order_counter

    if not cart:
        return {"error": "Cart empty"}

    placed_orders = []
    total = 0

    for c in cart:
        order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item": c["name"],
            "quantity": c["quantity"],
            "total_price": c["price"] * c["quantity"]
        }
        orders.append(order)
        placed_orders.append(order)
        total += order["total_price"]
        order_counter += 1

    cart.clear()
    response.status_code = 201

    return {"orders": placed_orders, "grand_total": total}

# ------------------ Q16 ------------------

@app.get("/menu/search")
def search_menu(keyword: str):
    result = [i for i in menu if keyword.lower() in i["name"].lower() or keyword.lower() in i["category"].lower()]

    if not result:
        return {"message": "No items found"}

    return {"results": result, "total_found": len(result)}

# ------------------ Q17 ------------------

@app.get("/menu/sort")
def sort_menu(sort_by: str = "price", order: str = "asc"):
    if sort_by not in ["price", "name", "category"]:
        return {"error": "Invalid sort_by"}

    if order not in ["asc", "desc"]:
        return {"error": "Invalid order"}

    reverse = True if order == "desc" else False
    sorted_list = sorted(menu, key=lambda x: x[sort_by], reverse=reverse)

    return {"sorted": sorted_list}

# ------------------ Q18 ------------------

@app.get("/menu/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    total = len(menu)

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit),
        "items": menu[start:start+limit]
    }

# ------------------ Q19 ------------------

@app.get("/orders/search")
def search_orders(customer_name: str):
    result = [o for o in orders if customer_name.lower() in o["customer_name"].lower()]
    return {"results": result}

@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    reverse = True if order == "desc" else False
    return {"orders": sorted(orders, key=lambda x: x["total_price"], reverse=reverse)}

# ------------------ Q20 ------------------

@app.get("/menu/browse")
def browse(keyword: Optional[str] = None,
           sort_by: str = "price",
           order: str = "asc",
           page: int = 1,
           limit: int = 4):

    data = menu

    if keyword:
        data = [i for i in data if keyword.lower() in i["name"].lower()]

    reverse = True if order == "desc" else False
    data = sorted(data, key=lambda x: x[sort_by], reverse=reverse)

    start = (page - 1) * limit

    return {
        "page": page,
        "total": len(data),
        "total_pages": math.ceil(len(data) / limit),
        "items": data[start:start+limit]
    }
