from FalabellaAPIClient import Session, Products, Service, Orders
import json

# login
user = "email@example.com"
key = "_api_key_"

session = Session(user, key, "falabella")
service = Service()

# get a product

items = Products(service, session)

product_list = ["T-19150"]

item = items.get(SkuSellerList=json.dumps(product_list))

print("product:", item)

# get orders

order = Orders(service, session)

print("order:", order.get(100513))
print("orderItems:", order.items(100513))
