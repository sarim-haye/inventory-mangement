from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_required, current_user
from . import db
from .models import Item, User, Inventory, ForSale
from datetime import datetime, timedelta

views = Blueprint('views', __name__)

@views.route('/deletion', methods=['GET', 'POST'])
@login_required
def employee_deletion():
    if request.method == 'POST':
        employee_id_to_delete = request.form.get('delete')
        if employee_id_to_delete:
            user_to_delete = User.query.get(employee_id_to_delete)
            if user_to_delete:
                db.session.delete(user_to_delete)
                db.session.commit()
                flash(f'Employee {user_to_delete.first_name} deleted successfully!', category='success')
            else:
                flash('Invalid employee ID for deletion.', category='error')

    users = User.query.all()

    return render_template("employee_deletion.html", users=users, user=current_user)

@views.route('/items', methods=['GET', 'POST'])
@login_required
def items():
    if request.method == 'POST':
        item_name = request.form.get('itemName')
        price = request.form.get('price')
        manufacturer = request.form.get('manufacturer')

        if not item_name or not price or not manufacturer:
            flash('Please fill in all fields.', 'error')
        else:
            try:
                price = float(price)
            except ValueError:
                flash('Price must be a valid number.', 'error')
                return redirect(url_for('views.items'))

            new_item = Item(itemName=item_name, price=price, manufacturer=manufacturer, user_relationship=current_user)
            db.session.add(new_item)
            db.session.commit()

            flash('Item added successfully!', 'success')
            return redirect(url_for('views.items'))

    items = Item.query.all()

    return render_template("items.html", user=current_user, items=items)

@views.route('/delete_item', methods=['POST'])
@login_required
def delete_item():
    item_name = request.form.get('deleteItemName')
    manufacturer = request.form.get('deleteManufacturer')

    if not item_name or not manufacturer:
        flash('Please provide both item name and manufacturer for deletion.', 'error')
        return redirect(url_for('views.items'))

    item_to_delete = Item.query.filter_by(itemName=item_name, manufacturer=manufacturer).first()

    if item_to_delete:
        db.session.delete(item_to_delete)
        db.session.commit()
        flash(f'Successfully deleted item: {item_name} - {manufacturer}', 'success')
    else:
        flash(f'Item not found: {item_name} - {manufacturer}', 'error')

    return redirect(url_for('views.items'))

@views.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    items = Item.query.all()
    inventory_items = Inventory.query.all()

    if request.method == 'POST':
        if 'itemSelect' in request.form:
            add_to_inventory()
            flash('Item added to inventory successfully!', 'success')
            return redirect(url_for('views.inventory'))

        elif 'deleteInventoryItemID' in request.form:
            inventory_item_id = request.form.get('deleteInventoryItemID')
            delete_item_from_inventory(inventory_item_id)
            flash('Item deleted from inventory successfully!', 'success')

        elif 'reduceQuantityItemID' in request.form:
            item_id = request.form.get('reduceQuantityItemID')
            quantity_to_reduce = request.form.get('reduceQuantity')
            reduce_quantity(item_id, quantity_to_reduce)
            flash('Quantity reduced successfully!', 'success')

    return render_template("inventory.html", items=items, inventory_items=inventory_items, user=current_user)

@views.route('/delete_item_from_inventory', methods=['POST'])
@login_required
def delete_item_from_inventory():
    inventory_item_id = request.form.get('deleteInventoryItemID')
    if inventory_item_id:
        delete_item_from_inventory_logic(inventory_item_id)
        flash('Item deleted from inventory successfully!', 'success')
    else:
        flash('Invalid inventory item ID for deletion.', 'error')

    return redirect(url_for('views.inventory'))

def delete_item_from_inventory_logic(inventory_item_id):
    inventory_item = Inventory.query.get(inventory_item_id)
    if inventory_item:
        db.session.delete(inventory_item)
        db.session.commit()

@views.route('/reduce_quantity', methods=['POST'])
@login_required
def reduce_quantity():
    item_id = request.form.get('itemID')
    quantity_to_reduce = request.form.get('quantity')
    if item_id and quantity_to_reduce:
        reduce_quantity_logic(item_id, quantity_to_reduce)
        flash('Quantity reduced successfully!', 'success')
    else:
        flash('Invalid item ID or quantity for reduction.', 'error')

    return redirect(url_for('views.inventory'))

def reduce_quantity_logic(item_id, quantity_to_reduce):
    item = Item.query.get(item_id)
    if item:
        inventory_item = Inventory.query.filter_by(item_id=item_id).first()
        if inventory_item and inventory_item.quantity >= int(quantity_to_reduce):
            inventory_item.quantity -= int(quantity_to_reduce)
            db.session.commit()
        else:
            flash('Invalid quantity for reduction.', 'error')
    else:
        flash('Invalid item ID for reduction.', 'error')

@views.route('/add_to_inventory', methods=['POST'])
@login_required
def add_to_inventory():
    item_id = request.form.get('itemSelect')
    quantity = request.form.get('quantity')

    if item_id and quantity:
        item = Item.query.get(item_id)

        if item:
            if int(quantity) > 0:
                inventory_item = Inventory.query.filter_by(item_id=item_id).first()

                if inventory_item:
                    # If the item is already in inventory, update the quantity
                    inventory_item.quantity += int(quantity)
                else:
                    # If the item is not in inventory, create a new entry
                    new_inventory_item = Inventory(item_id=item_id, quantity=int(quantity))
                    db.session.add(new_inventory_item)

                db.session.commit()
                flash('Item added to inventory successfully!', 'success')
            else:
                flash('Invalid quantity.', 'error')
        else:
            flash('Invalid item ID.', 'error')
    else:
        flash('Invalid form data.', 'error')

    return redirect(url_for('views.inventory'))

@views.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer():
    inventory_items = Inventory.query.all()

    if request.method == 'POST':
        selected_items_ids = [int(id) for id in request.form.getlist('selectedItems')]

        selected_items = []
        for item_id in selected_items_ids:
            quantity_key = f'quantity_{item_id}'
            quantity = int(request.form.get(quantity_key, 1))

            inventory_item = Inventory.query.get(item_id)

            if inventory_item:
                if inventory_item.quantity >= quantity:
                    selected_items.append({'inventory_item': inventory_item, 'quantity': quantity})
                else:
                    flash(f"Selected quantity for '{inventory_item.item.itemName}' exceeds available quantity in inventory.", 'error')

        if selected_items:
            flash('Selected items for transfer successfully!', 'success')

        return render_template("transfer.html", inventory_items=inventory_items, user=current_user, selected_items=selected_items)

    return render_template("transfer.html", inventory_items=inventory_items, user=current_user)


@views.route('/transfer_to_for_sale', methods=['POST'])
@login_required
def transfer_to_for_sale():
    selected_items_ids = request.form.getlist('selectedItems')

    for item_id in selected_items_ids:
        quantity_key = f'quantity_{item_id}'
        quantity = int(request.form.get(quantity_key, 1))

        inventory_item = Inventory.query.get(item_id)

        if inventory_item and inventory_item.quantity >= quantity:
            for_sale_item = ForSale.query.filter_by(inventory_id=inventory_item.id).first()
            
            if for_sale_item:
                #if item already exists, add quantity entered by user to it
                for_sale_item.quantity += quantity
            else:
                # If the item doesn't exist in the ForSale table, create a new entry
                for_sale_item = ForSale(quantity=quantity, inventory=inventory_item)
                db.session.add(for_sale_item)

            #reduce quantity in inventory by the amount the user entered
            inventory_item.quantity -= quantity  # Reduce quantity in inventory

            db.session.commit()
            flash('Items transferred to For Sale successfully!', 'success')
        else:
            flash('Invalid quantity for transfer.', 'error')

    return redirect(url_for('views.transfer'))


def commit_transfer_to_for_sale(selected_items_ids):
    for item_id in selected_items_ids:
        inventory_item = Inventory.query.get(item_id)

        if inventory_item and inventory_item.quantity > 0:
            # Get the transfer quantity from the form
            transfer_quantity_key = f'transferQuantity_{item_id}'
            transfer_quantity = int(request.form.get(transfer_quantity_key, 1))

            # Reduce quantity in inventory based on the transfer quantity
            inventory_item.quantity -= transfer_quantity

    db.session.commit()

@views.route('/for_sale', methods=['GET'])
@login_required
def for_sale():
    for_sale_items = ForSale.query.all()

    # Sorting the for sale items alphabetically using Merge Sort
    sorted_for_sale_items = merge_sort(for_sale_items)

    grouped_items = {}
    for sale_item in sorted_for_sale_items:
        inventory_item = sale_item.inventory
        item_name = inventory_item.item.itemName

        if item_name not in grouped_items:
            grouped_items[item_name] = {'total_quantity': sale_item.quantity, 'item_id': sale_item.id}
        else:
            grouped_items[item_name]['total_quantity'] += sale_item.quantity

    grouped_items_list = [{'item_name': key, **value} for key, value in grouped_items.items()]

    return render_template("for_sale.html", grouped_items=grouped_items_list, user=current_user)


def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left_half = arr[:mid]
    right_half = arr[mid:]

    left_half = merge_sort(left_half)
    right_half = merge_sort(right_half)

    if left_half is None or right_half is None:
        return []

    return merge(left_half, right_half)

def merge(left, right):
    result = []
    left_index, right_index = 0, 0

    while left_index < len(left) and right_index < len(right):
        if left[left_index].inventory.item.itemName < right[right_index].inventory.item.itemName:
                result.append(left[left_index])
                left_index += 1
        else:
            result.append(right[right_index])
            right_index += 1

    result.extend(left[left_index:])
    result.extend(right[right_index:])

    return result



@views.route('/sale_made/<int:item_id>', methods=['POST'])
@login_required
def sale_made(item_id):
    for_sale_item = ForSale.query.filter_by(id=item_id).first()
    if for_sale_item and for_sale_item.quantity > 0:
        # Assuming each button click sells 1 item, reduce the quantity
        for_sale_item.quantity -= 1
        db.session.commit()
        flash('Sale made for 1 item!', 'success')
    else:
        flash('Invalid sale request.', 'error')

    return redirect(url_for('views.for_sale'))

@views.route('/demand', methods=['GET', 'POST'])
def demand_page():
    if request.method == 'POST':
        try:
            # Retrieve demand data for each day and current stock quantity from the form
            monday_demand = int(request.form.get('monday'))
            tuesday_demand = int(request.form.get('tuesday'))
            wednesday_demand = int(request.form.get('wednesday'))
            thursday_demand = int(request.form.get('thursday'))
            friday_demand = int(request.form.get('friday'))
            saturday_demand = int(request.form.get('saturday'))
            sunday_demand = int(request.form.get('sunday'))
            current_stock_quantity = int(request.form.get('current_stock'))
        except ValueError:
            # If a valid number isn't entered, flash a message and render the form again
            flash("Please enter valid numbers for demand and current stock quantity.", category='error')
            return render_template('demand.html', user=current_user)

        # Calculate total demand for the week
        total_demand = monday_demand + tuesday_demand + wednesday_demand + thursday_demand + friday_demand + saturday_demand + sunday_demand

        # Calculate average demand per day
        average_demand_per_day = round(total_demand / 7)

        # Recommendation for restocking based on average demand and current stock
        if current_stock_quantity <= 0:
            restock_recommendation = "Restock immediately"
        elif current_stock_quantity < average_demand_per_day:
            restock_recommendation = "Consider restocking soon"
        else:
            restock_recommendation = "Stock level is sufficient"

        # Render the template with the average demand per day and restocking recommendation
        return render_template('demand.html', average_demand_per_day=average_demand_per_day, restock_recommendation=restock_recommendation, user=current_user)

    # Render the form for GET requests
    return render_template('demand.html', user=current_user)

@views.route('/lead_time', methods=['GET', 'POST'])
def lead_time_page():
    if request.method == 'POST':
        valid = False
        while not valid:
            try:
                # Retrieve form data
                order_date = datetime.strptime(request.form['order_date'], '%Y-%m-%d')
                estimated_arrival_date = datetime.strptime(request.form['estimated_arrival_date'], '%Y-%m-%d')
                if order_date < estimated_arrival_date:
                    valid = True
                else:
                    flash('Order date must be before the estimated arrival date.', category='error')
                    return render_template('lead_time.html', user=current_user)
            except ValueError:
                flash('Please enter valid dates in the format YYYY-MM-DD.', category='error')
                return render_template('lead_time.html', user=current_user)

            if valid:
                # Continue with the rest of your calculation logic here...
                try:
                    average_demand_per_day = int(request.form.get('average_demand_per_day'))
                    buffer_stock = int(request.form.get('buffer_stock'))
                    current_stock_quantity = int(request.form.get('current_stock', 0))  # Provide a default value of 0
                except ValueError:
                    flash('Demand and stock must be integer values.', category='error')
                    return render_template('lead_time.html', user=current_user)

                # Calculate difference in days between order and estimated arrival date
                difference_in_days = (estimated_arrival_date - order_date).days

                # Calculate the number of days until the buffer stock runs out
                days_until_run_out = max(0, current_stock_quantity - buffer_stock) // average_demand_per_day

                # Calculate the current stock runout date
                current_stock_run_out = estimated_arrival_date - timedelta(days=days_until_run_out)

                # Calculate the number of days to order before stock runs out
                order_recommendation = max(0, difference_in_days - days_until_run_out)

                # Recommendation based on buffer stock runout date
                if days_until_run_out <= 0:
                    recommendation = "Order stock immediately to avoid stockout."
                elif days_until_run_out <= 7:
                    recommendation = "Stock level is sufficient for the next week."
                else:
                    recommendation = "Stock level is sufficient for the buffer period."

                # Render template with calculated values
                return render_template('lead_time.html',
                                        difference_in_days=difference_in_days,
                                        current_stock_run_out=current_stock_run_out.strftime('%Y-%m-%d'),
                                        recommendation=recommendation,
                                        order_recommendation=order_recommendation, 
                                        user=current_user)

    # Render form for GET requests
    return render_template('lead_time.html', user=current_user)

@views.route('/calculations', methods=['GET'])
def calculations_page():
    return render_template('calculations.html', user=current_user)

@views.route('/promotion', methods=['GET'])
@login_required
def display_promotion_page():
    general_staff_users = User.query.filter_by(job_role='general_staff').all()
    return render_template('promotion.html', general_staff_users=general_staff_users, user=current_user)

@views.route('/promote', methods=['POST'])
@login_required
def promote_user():
    if request.method == 'POST':
        user_email = request.form['email']
        user = User.query.filter_by(email=user_email, job_role='general_staff').first()
        if user:
            user.job_role = 'senior_staff'
            db.session.commit()
            flash('User promoted successfully', 'success')
        else:
            flash('User not found or already promoted', 'error')
    return redirect(url_for('views.display_promotion_page'))