from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    job_role = db.Column(db.String(150))
    items = db.relationship('Item', backref='created_by_user')  # relationship back to User that added the item

    # Unique backref name for the relationship with Inventory
    added_inventory_items = db.relationship('Inventory', backref='added_by_user', lazy='dynamic')  # relationship back to user that added an item to the inventory

class Item(db.Model):  # uniquely defines an item
    id = db.Column(db.Integer, primary_key=True)
    itemName = db.Column(db.String(150))
    price = db.Column(db.Float)
    manufacturer = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_relationship = db.relationship('User', backref='items_created')  # unique backref name

    # one-to-many relationship between item and instances in inventory, one item can have many quantities in inventory
    inventory_items = db.relationship('Inventory', backref='item_inventory_items')  # unique backref name

    @property
    def created_by(self):
        return self.user_relationship.first_name if self.user_relationship else None

class Inventory(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    item = db.relationship('Item', backref='inventory_item')  

    # Foreign key reference to User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='inventory_items')  

class ForSale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    date = db.Column(db.DateTime, server_default=func.now())

    # relationships
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'))
    inventory = db.relationship('Inventory', backref='for_sale_item')
