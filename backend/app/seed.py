from sqlalchemy import select
from .models import Customer, Merchant, Driver, Order

def seed(db):
    if db.scalar(select(Customer.id).limit(1)):
        return
    db.add(Customer(id=1,name="Alex Morgan"))
    db.add_all([Merchant(id=1,name="Little Italy Kitchen",lat=40.724,lng=-73.997),Merchant(id=2,name="Green Bowl",lat=40.735,lng=-73.99)])
    db.flush()
    names = ["Maya Chen", "Jordan Rivera", "Sam Patel", "Taylor Brooks", "Chris Park", "Avery Lewis"]
    for i,name in enumerate(names):
        db.add(Driver(name=name,lat=40.716+i*.004,lng=-74.005+i*.003))
    for i in range(4):
        db.add(Order(customer_id=1,merchant_id=1+i%2,lat=40.738+i*.003,lng=-73.98-i*.002,status=["CREATED","ACCEPTED","PREPARING","READY_FOR_PICKUP"][i],prep_minutes=4+i*2))
    db.commit()
