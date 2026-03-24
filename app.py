import os
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'orders.db'))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Change this in production via environment variable
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

db = SQLAlchemy(app)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    tracking_number = db.Column(db.String(100), unique=True, nullable=True, index=True)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    courier = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Order received')
    last_location = db.Column(db.String(200), nullable=True)
    eta = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = db.relationship(
        'OrderEvent',
        backref='order',
        lazy=True,
        cascade='all, delete-orphan',
        order_by='desc(OrderEvent.event_time)'
    )


class OrderEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    event_title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    event_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


STATUS_OPTIONS = [
    'Order received',
    'Payment confirmed',
    'Packed',
    'Awaiting courier pickup',
    'In transit',
    'Out for delivery',
    'Delivered',
    'Delayed',
    'Cancelled',
]


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Please log in as admin first.', 'error')
            return redirect(url_for('admin_login'))
        return view_func(*args, **kwargs)
    return wrapped


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/track', methods=['GET', 'POST'])
def track_order():
    query = request.form.get('query', '').strip() if request.method == 'POST' else request.args.get('query', '').strip()
    order = None

    if query:
        order = Order.query.filter(
            (Order.order_number == query) | (Order.tracking_number == query)
        ).first()

        if not order:
            flash("No order was found with that order number or tracking number.", "error")

    return render_template('track.html', order=order, query=query)


@app.route("/track/<tracking_number>")
def track_order_direct(tracking_number):
    order = Order.query.filter_by(tracking_number=tracking_number).first()

    if not order:
        flash("No order was found for that tracking number.", "error")
        return redirect(url_for("track_order"))

    return render_template("track.html", order=order, query=tracking_number)
    query = request.form.get('query', '').strip() if request.method == 'POST' else request.args.get('query', '').strip()
    order = None

    if query:
        order = Order.query.filter(
            (Order.order_number == query) | (Order.tracking_number == query)
        ).first()
        if not order:
            flash('No order was found with that order number or tracking number.', 'error')

    return render_template('track.html', order=order, query=query)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect password.', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('home'))


@app.route('/admin')
@admin_required
def admin_dashboard():
    status_filter = request.args.get('status', '').strip()

    query = Order.query

    if status_filter:
        query = query.filter(Order.status == status_filter)

    orders = query.order_by(Order.updated_at.desc()).all()

    return render_template(
        'admin_dashboard.html',
        orders=orders,
        status_filter=status_filter
    )


@app.route('/admin/orders/new', methods=['GET', 'POST'])
@admin_required
def create_order():
    if request.method == 'POST':
        order_number = request.form.get('order_number', '').strip()
        tracking_number = request.form.get('tracking_number', '').strip() or None
        customer_name = request.form.get('customer_name', '').strip()
        customer_email = request.form.get('customer_email', '').strip()
        courier = request.form.get('courier', '').strip() or None
        status = request.form.get('status', '').strip() or 'Order received'
        last_location = request.form.get('last_location', '').strip() or None
        eta = request.form.get('eta', '').strip() or None
        notes = request.form.get('notes', '').strip() or None

        if not order_number or not customer_name or not customer_email:
            flash('Order number, customer name, and customer email are required.', 'error')
            return render_template('order_form.html', order=None, statuses=STATUS_OPTIONS)

        if Order.query.filter_by(order_number=order_number).first():
            flash('That order number already exists.', 'error')
            return render_template('order_form.html', order=None, statuses=STATUS_OPTIONS)

        if tracking_number and Order.query.filter_by(tracking_number=tracking_number).first():
            flash('That tracking number already exists.', 'error')
            return render_template('order_form.html', order=None, statuses=STATUS_OPTIONS)

        order = Order(
            order_number=order_number,
            tracking_number=tracking_number,
            customer_name=customer_name,
            customer_email=customer_email,
            courier=courier,
            status=status,
            last_location=last_location,
            eta=eta,
            notes=notes,
        )
        db.session.add(order)
        db.session.flush()

        db.session.add(OrderEvent(
            order_id=order.id,
            event_title=status,
            description='Order created in admin panel.',
            location=last_location,
        ))

        db.session.commit()
        flash('Order created successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('order_form.html', order=None, statuses=STATUS_OPTIONS)


@app.route('/admin/orders/<int:order_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_order(order_id):
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        old_status = order.status
        old_location = order.last_location

        order.order_number = request.form.get('order_number', '').strip()
        order.tracking_number = request.form.get('tracking_number', '').strip() or None
        order.customer_name = request.form.get('customer_name', '').strip()
        order.customer_email = request.form.get('customer_email', '').strip()
        order.courier = request.form.get('courier', '').strip() or None
        order.status = request.form.get('status', '').strip() or 'Order received'
        order.last_location = request.form.get('last_location', '').strip() or None
        order.eta = request.form.get('eta', '').strip() or None
        order.notes = request.form.get('notes', '').strip() or None

        duplicate_order = Order.query.filter(Order.order_number == order.order_number, Order.id != order.id).first()
        if duplicate_order:
            flash('Another order already uses that order number.', 'error')
            return render_template('order_form.html', order=order, statuses=STATUS_OPTIONS)

        if order.tracking_number:
            duplicate_tracking = Order.query.filter(Order.tracking_number == order.tracking_number, Order.id != order.id).first()
            if duplicate_tracking:
                flash('Another order already uses that tracking number.', 'error')
                return render_template('order_form.html', order=order, statuses=STATUS_OPTIONS)

        event_title = request.form.get('event_title', '').strip()
        event_description = request.form.get('event_description', '').strip() or None
        add_event = bool(event_title)

        status_changed = old_status != order.status or old_location != order.last_location
        if add_event:
            db.session.add(OrderEvent(
                order_id=order.id,
                event_title=event_title,
                description=event_description,
                location=order.last_location,
            ))
        elif status_changed:
            db.session.add(OrderEvent(
                order_id=order.id,
                event_title=order.status,
                description='Status updated from admin panel.',
                location=order.last_location,
            ))

        db.session.commit()
        flash('Order updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('order_form.html', order=order, statuses=STATUS_OPTIONS)


@app.route('/admin/orders/<int:order_id>/delete', methods=['POST'])
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash('Order deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.cli.command('seed')
def seed_data():
    """Seed the database with demo data."""
    if Order.query.first():
        print('Database already has data.')
        return

    order = Order(
        order_number='AKH12345',
        tracking_number='TRK987654',
        customer_name='Akhona Maposela',
        customer_email='akhona@example.com',
        courier='FastShip',
        status='In transit',
        last_location='Cape Town Depot',
        eta='Tomorrow before 17:00',
        notes='Customer requested SMS updates.',
    )
    db.session.add(order)
    db.session.flush()

    events = [
        OrderEvent(order_id=order.id, event_title='Order received', description='We have received your order.', location='Online Store'),
        OrderEvent(order_id=order.id, event_title='Packed', description='Your order has been packed and is ready for courier pickup.', location='Johannesburg Warehouse'),
        OrderEvent(order_id=order.id, event_title='In transit', description='Your parcel is currently moving between hubs.', location='Cape Town Depot'),
    ]
    db.session.add_all(events)
    db.session.commit()
    print('Demo order added: AKH12345 / TRK987654')


with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)
