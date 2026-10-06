import os
import random
import string
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, init_db

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "bookstore-super-secret-key-2026")

# Enable secure cookie configuration for cloud platforms
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# WSGI Middleware to normalize Vercel serverless paths
class VercelPathFixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = environ.get('HTTP_X_MATCHED_PATH') or environ.get('HTTP_X_NOW_ROUTE_MATCHES')
        if matched_path:
            environ['PATH_INFO'] = matched_path
        else:
            path = environ.get('PATH_INFO', '')
            for prefix in ['/api/index.py', '/api/index', '/api']:
                if path.startswith(prefix):
                    environ['PATH_INFO'] = path[len(prefix):] or '/'
                    break

        if not environ.get('PATH_INFO', '').startswith('/'):
            environ['PATH_INFO'] = '/' + environ.get('PATH_INFO', '')

        environ['SCRIPT_NAME'] = ''
        return self.wsgi_app(environ, start_response)

# Apply middlewares (ProxyFix handles HTTPS headers, VercelPathFix handles Vercel paths)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.wsgi_app = VercelPathFixMiddleware(app.wsgi_app)

# Initialize database on start safely
try:
    with app.app_context():
        init_db()
except Exception as e:
    print("Database init warning:", e)

# ----------------- Helper Decorators ----------------- #
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in as an administrator.", "warning")
            return redirect(url_for("admin_login"))
        if session.get("user_role") != "admin":
            flash("Access denied. Admin privileges required.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# Context processor to inject cart count and categories into all templates
@app.context_processor
def inject_global_data():
    cart_count = 0
    if "user_id" in session:
        db = get_db()
        row = db.execute(
            "SELECT SUM(quantity) as total FROM cart WHERE user_id = ?",
            (session["user_id"],)
        ).fetchone()
        if row and row["total"]:
            cart_count = row["total"]
        db.close()
    
    categories = [
        "Computer Science",
        "Fiction",
        "Self-Help",
        "Finance",
        "History",
        "Science",
        "Biography"
    ]
    return dict(cart_count=cart_count, global_categories=categories)

# ----------------- User Routes ----------------- #
@app.route("/")
@app.route("/api/index")
@app.route("/api/index.py")
@app.route("/api")
def index():
    db = get_db()
    featured_books = db.execute(
        "SELECT * FROM books WHERE featured = 1 ORDER BY rating DESC LIMIT 6"
    ).fetchall()
    
    recent_books = db.execute(
        "SELECT * FROM books ORDER BY created_at DESC LIMIT 6"
    ).fetchall()

    stats = {
        "books_count": db.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "categories_count": db.execute("SELECT COUNT(DISTINCT category) FROM books").fetchone()[0],
        "reviews_count": db.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        "users_count": db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    }
    db.close()

    return render_template(
        "index.html",
        featured_books=featured_books,
        recent_books=recent_books,
        stats=stats
    )

@app.route("/books")
def books():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "default")

    sql = "SELECT * FROM books WHERE 1=1"
    params = []

    if query:
        sql += " AND (title LIKE ? OR author LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%"])

    if category:
        sql += " AND category = ?"
        params.append(category)

    if sort == "price_asc":
        sql += " ORDER BY price ASC"
    elif sort == "price_desc":
        sql += " ORDER BY price DESC"
    elif sort == "rating":
        sql += " ORDER BY rating DESC"
    elif sort == "newest":
        sql += " ORDER BY created_at DESC"
    else:
        sql += " ORDER BY id DESC"

    db = get_db()
    books_list = db.execute(sql, params).fetchall()

    # Get category counts for sidebar
    categories_with_count = db.execute(
        "SELECT category, COUNT(*) as count FROM books GROUP BY category ORDER BY count DESC"
    ).fetchall()
    db.close()

    return render_template(
        "books.html",
        books=books_list,
        current_query=query,
        current_category=category,
        current_sort=sort,
        categories=categories_with_count
    )

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        db.close()
        flash("Book not found.", "danger")
        return redirect(url_for("books"))

    reviews = db.execute(
        "SELECT * FROM reviews WHERE book_id = ? ORDER BY created_at DESC",
        (book_id,)
    ).fetchall()

    related_books = db.execute(
        "SELECT * FROM books WHERE category = ? AND id != ? LIMIT 4",
        (book["category"], book_id)
    ).fetchall()
    db.close()

    return render_template(
        "book_detail.html",
        book=book,
        reviews=reviews,
        related_books=related_books
    )

@app.route("/book/<int:book_id>/review", methods=["POST"])
@login_required
def add_review(book_id):
    rating = int(request.form.get("rating", 5))
    comment = request.form.get("comment", "").strip()

    if not comment:
        flash("Please write a review comment.", "warning")
        return redirect(url_for("book_detail", book_id=book_id))

    db = get_db()
    db.execute(
        "INSERT INTO reviews (book_id, user_id, user_name, rating, comment) VALUES (?, ?, ?, ?, ?)",
        (book_id, session["user_id"], session["user_name"], rating, comment)
    )

    # Recalculate book average rating
    avg_row = db.execute(
        "SELECT AVG(rating) as avg_rating, COUNT(*) as cnt FROM reviews WHERE book_id = ?",
        (book_id,)
    ).fetchone()
    if avg_row:
        new_rating = round(avg_row["avg_rating"], 1)
        count = avg_row["cnt"]
        db.execute(
            "UPDATE books SET rating = ?, rating_count = ? WHERE id = ?",
            (new_rating, count, book_id)
        )

    db.commit()
    db.close()

    flash("Thank you! Your review has been added.", "success")
    return redirect(url_for("book_detail", book_id=book_id))

# ----------------- Cart Routes ----------------- #
@app.route("/cart")
@login_required
def cart():
    db = get_db()
    cart_items = db.execute('''
        SELECT c.id, c.quantity, b.id as book_id, b.title, b.author, b.price, b.cover_image, b.stock
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = ?
    ''', (session["user_id"],)).fetchall()
    db.close()

    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    shipping = 0 if subtotal >= 500 or subtotal == 0 else 49.0
    total = subtotal + shipping

    return render_template(
        "cart.html",
        cart_items=cart_items,
        subtotal=subtotal,
        shipping=shipping,
        total=total
    )

@app.route("/cart/add/<int:book_id>", methods=["POST", "GET"])
@login_required
def add_to_cart(book_id):
    quantity = int(request.form.get("quantity", 1))
    db = get_db()

    # Verify book exists and has stock
    book = db.execute("SELECT stock, title FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        db.close()
        flash("Book does not exist.", "danger")
        return redirect(url_for("books"))

    if book["stock"] <= 0:
        db.close()
        flash("Sorry, this book is currently out of stock.", "warning")
        return redirect(url_for("book_detail", book_id=book_id))

    existing = db.execute(
        "SELECT quantity FROM cart WHERE user_id = ? AND book_id = ?",
        (session["user_id"], book_id)
    ).fetchone()

    if existing:
        new_qty = min(existing["quantity"] + quantity, book["stock"])
        db.execute(
            "UPDATE cart SET quantity = ? WHERE user_id = ? AND book_id = ?",
            (new_qty, session["user_id"], book_id)
        )
    else:
        new_qty = min(quantity, book["stock"])
        db.execute(
            "INSERT INTO cart (user_id, book_id, quantity) VALUES (?, ?, ?)",
            (session["user_id"], book_id, new_qty)
        )

    db.commit()
    db.close()
    flash(f"'{book['title']}' added to your cart!", "success")
    return redirect(request.referrer or url_for("cart"))

@app.route("/cart/update/<int:book_id>", methods=["POST"])
@login_required
def update_cart(book_id):
    action = request.form.get("action")
    db = get_db()

    item = db.execute(
        "SELECT quantity FROM cart WHERE user_id = ? AND book_id = ?",
        (session["user_id"], book_id)
    ).fetchone()

    if item:
        book = db.execute("SELECT stock FROM books WHERE id = ?", (book_id,)).fetchone()
        current_qty = item["quantity"]

        if action == "increase":
            if current_qty < book["stock"]:
                db.execute(
                    "UPDATE cart SET quantity = quantity + 1 WHERE user_id = ? AND book_id = ?",
                    (session["user_id"], book_id)
                )
            else:
                flash(f"Maximum available stock reached ({book['stock']}).", "warning")
        elif action == "decrease":
            if current_qty > 1:
                db.execute(
                    "UPDATE cart SET quantity = quantity - 1 WHERE user_id = ? AND book_id = ?",
                    (session["user_id"], book_id)
                )
            else:
                db.execute(
                    "DELETE FROM cart WHERE user_id = ? AND book_id = ?",
                    (session["user_id"], book_id)
                )
        db.commit()

    db.close()
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:book_id>", methods=["POST", "GET"])
@login_required
def remove_from_cart(book_id):
    db = get_db()
    db.execute(
        "DELETE FROM cart WHERE user_id = ? AND book_id = ?",
        (session["user_id"], book_id)
    )
    db.commit()
    db.close()
    flash("Item removed from your cart.", "info")
    return redirect(url_for("cart"))

# ----------------- Checkout & Orders ----------------- #
@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    db = get_db()
    cart_items = db.execute('''
        SELECT c.quantity, b.id as book_id, b.title, b.price, b.stock
        FROM cart c
        JOIN books b ON c.book_id = b.id
        WHERE c.user_id = ?
    ''', (session["user_id"],)).fetchall()

    if not cart_items:
        db.close()
        flash("Your cart is empty. Add books before proceeding to checkout.", "warning")
        return redirect(url_for("books"))

    subtotal = sum(item["price"] * item["quantity"] for item in cart_items)
    shipping = 0 if subtotal >= 500 else 49.0
    total = subtotal + shipping

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        pincode = request.form.get("pincode", "").strip()
        payment_method = request.form.get("payment_method", "Cash on Delivery")

        if not all([full_name, email, phone, address, city, pincode]):
            flash("Please fill in all shipping details.", "danger")
            db.close()
            return render_template("checkout.html", cart_items=cart_items, subtotal=subtotal, shipping=shipping, total=total)

        # Generate unique order number
        random_suffix = ''.join(random.choices(string.digits, k=5))
        order_number = f"BK-2026-{random_suffix}"

        # Insert order
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO orders (order_number, user_id, full_name, email, phone, address, city, pincode, payment_method, total_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Processing')
        ''', (order_number, session["user_id"], full_name, email, phone, address, city, pincode, payment_method, total))

        order_id = cursor.lastrowid

        # Insert order items and deduct stock
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, book_id, title, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, item["book_id"], item["title"], item["price"], item["quantity"]))

            cursor.execute('''
                UPDATE books SET stock = MAX(0, stock - ?) WHERE id = ?
            ''', (item["quantity"], item["book_id"]))

        # Clear cart
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (session["user_id"],))

        db.commit()
        db.close()

        flash("Order placed successfully!", "success")
        return redirect(url_for("order_success", order_number=order_number))

    db.close()
    return render_template(
        "checkout.html",
        cart_items=cart_items,
        subtotal=subtotal,
        shipping=shipping,
        total=total
    )

@app.route("/order-success/<order_number>")
@login_required
def order_success(order_number):
    db = get_db()
    order = db.execute(
        "SELECT * FROM orders WHERE order_number = ? AND user_id = ?",
        (order_number, session["user_id"])
    ).fetchone()

    if not order:
        db.close()
        flash("Order not found.", "danger")
        return redirect(url_for("index"))

    items = db.execute(
        "SELECT * FROM order_items WHERE order_id = ?",
        (order["id"],)
    ).fetchall()
    db.close()

    return render_template("order_success.html", order=order, items=items)

@app.route("/orders")
@login_required
def user_orders():
    db = get_db()
    orders = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],)
    ).fetchall()

    orders_with_items = []
    for order in orders:
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order["id"],)
        ).fetchall()
        orders_with_items.append({"order": order, "order_items": items})

    db.close()
    return render_template("orders.html", orders_with_items=orders_with_items)

# ----------------- Auth Routes ----------------- #
# ----------------- Auth Routes ----------------- #
@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    next_page = request.args.get("next") or request.form.get("next") or ""
    step = request.args.get("step", "phone")
    phone = session.get("login_phone", "")

    if request.method == "POST":
        action = request.form.get("action")

        # Step 1: Send OTP
        if action == "send_otp":
            raw_phone = request.form.get("phone", "").strip()
            # Keep only digits
            cleaned_phone = "".join(filter(str.isdigit, raw_phone))

            if len(cleaned_phone) != 10:
                flash("Please enter a valid 10-digit mobile number.", "warning")
                return render_template("login.html", step="phone", phone=raw_phone, next=next_page)

            # Generate random 4-digit OTP
            otp = f"{random.randint(1000, 9999)}"
            session["login_phone"] = cleaned_phone
            session["login_otp"] = otp

            # Check if this user exists
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE phone = ?", (cleaned_phone,)).fetchone()
            db.close()

            is_new = user is None
            flash(f"OTP sent successfully to +91 {cleaned_phone}! Your Verification Code is: {otp}", "info")
            return render_template("login.html", step="verify", phone=cleaned_phone, otp_code=otp, is_new_user=is_new, next=next_page)

        # Step 2: Verify OTP
        elif action == "verify_otp":
            entered_otp = request.form.get("otp", "").strip()
            submitted_phone = request.form.get("phone", "").strip()
            user_name = request.form.get("name", "").strip()

            expected_otp = session.get("login_otp")
            session_phone = session.get("login_phone")

            if not expected_otp or not session_phone or entered_otp != expected_otp or submitted_phone != session_phone:
                flash("Invalid OTP code. Please enter the correct 4-digit code.", "danger")
                return render_template("login.html", step="verify", phone=submitted_phone, otp_code=expected_otp, is_new_user=request.form.get("is_new_user") == "1", next=next_page)

            # OTP verified successfully!
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE phone = ?", (submitted_phone,)).fetchone()

            if user:
                user_id = user["id"]
                final_name = user["name"]
                final_email = user["email"]
                final_role = user["role"]
            else:
                # Create new user for this mobile number
                final_name = user_name if user_name else f"Reader-{submitted_phone[-4:]}"
                final_email = f"{submitted_phone}@bookstore.local"
                dummy_hash = generate_password_hash(os.urandom(16).hex())
                
                cursor = db.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, 'user')",
                    (final_name, final_email, submitted_phone, dummy_hash)
                )
                user_id = cursor.lastrowid
                final_role = "user"
                db.commit()

            db.close()

            # Set user session
            session.permanent = True
            session["user_id"] = user_id
            session["user_name"] = final_name
            session["user_email"] = final_email
            session["user_role"] = final_role
            session["user_phone"] = submitted_phone

            # Clear temporary OTP session
            session.pop("login_otp", None)
            session.pop("login_phone", None)

            flash(f"Welcome, {final_name}! You have signed in successfully.", "success")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("index"))

        # Fallback Email Login (if user toggles to email/password)
        elif action == "email_login":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            db = get_db()
            user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            db.close()

            if user and check_password_hash(user["password_hash"], password):
                session.permanent = True
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                session["user_role"] = user["role"]
                session["user_phone"] = user["phone"]
                flash(f"Welcome back, {user['name']}!", "success")
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)
                if user["role"] == "admin":
                    return redirect(url_for("admin_dashboard"))
                return redirect(url_for("index"))
            else:
                flash("Invalid email or password. Please try again.", "danger")
                return render_template("login.html", step="phone", next=next_page)

    return render_template("login.html", step=step, phone=phone, next=next_page)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "user_id" in session and session.get("user_role") == "admin":
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE (email = ? OR (email = 'admin@bookstore.com' AND ? = 'admin')) AND role = 'admin'",
            (email, email)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password_hash"], password):
            session.permanent = True
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["user_role"] = "admin"
            flash(f"Welcome back, {user['name']}! Admin Portal unlocked.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid administrator credentials. Access restricted.", "danger")
            return render_template("admin_login.html", email=email)

    return render_template("admin_login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("index"))

# ----------------- Admin Routes ----------------- #
@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    total_sales = db.execute(
        "SELECT SUM(total_amount) FROM orders WHERE status != 'Cancelled'"
    ).fetchone()[0] or 0.0

    total_orders = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    total_books = db.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    total_users = db.execute("SELECT COUNT(*) FROM users WHERE role = 'user'").fetchone()[0]

    recent_orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    db.close()

    return render_template(
        "admin/dashboard.html",
        total_sales=total_sales,
        total_orders=total_orders,
        total_books=total_books,
        total_users=total_users,
        recent_orders=recent_orders
    )

@app.route("/admin/books")
@admin_required
def admin_books():
    db = get_db()
    books = db.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    db.close()
    return render_template("admin/books.html", books=books)

@app.route("/admin/book/add", methods=["GET", "POST"])
@admin_required
def admin_add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        price = float(request.form.get("price", 0))
        original_price = float(request.form.get("original_price") or price)
        stock = int(request.form.get("stock", 10))
        cover_image = request.form.get("cover_image", "").strip() or "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80"
        description = request.form.get("description", "").strip()
        featured = 1 if request.form.get("featured") else 0

        db = get_db()
        db.execute('''
            INSERT INTO books (title, author, category, price, original_price, stock, description, cover_image, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, author, category, price, original_price, stock, description, cover_image, featured))
        db.commit()
        db.close()

        flash("Book added to the inventory successfully!", "success")
        return redirect(url_for("admin_books"))

    return render_template("admin/book_form.html", book=None)

@app.route("/admin/book/edit/<int:book_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_book():
    db = get_db()
    book = db.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
    if not book:
        db.close()
        flash("Book not found.", "danger")
        return redirect(url_for("admin_books"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        price = float(request.form.get("price", 0))
        original_price = float(request.form.get("original_price") or price)
        stock = int(request.form.get("stock", 0))
        cover_image = request.form.get("cover_image", "").strip()
        description = request.form.get("description", "").strip()
        featured = 1 if request.form.get("featured") else 0

        db.execute('''
            UPDATE books 
            SET title=?, author=?, category=?, price=?, original_price=?, stock=?, description=?, cover_image=?, featured=?
            WHERE id=?
        ''', (title, author, category, price, original_price, stock, description, cover_image, featured, book_id))
        db.commit()
        db.close()

        flash("Book details updated successfully!", "success")
        return redirect(url_for("admin_books"))

    db.close()
    return render_template("admin/book_form.html", book=book)

@app.route("/admin/book/delete/<int:book_id>", methods=["POST"])
@admin_required
def admin_delete_book(book_id):
    db = get_db()
    db.execute("DELETE FROM books WHERE id = ?", (book_id,))
    db.commit()
    db.close()
    flash("Book removed from inventory.", "info")
    return redirect(url_for("admin_books"))

@app.route("/admin/orders")
@admin_required
def admin_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
    
    orders_with_items = []
    for order in orders:
        items = db.execute(
            "SELECT * FROM order_items WHERE order_id = ?",
            (order["id"],)
        ).fetchall()
        orders_with_items.append({"order": order, "order_items": items})

    db.close()
    return render_template("admin/orders.html", orders_with_items=orders_with_items)

@app.route("/admin/order/status/<int:order_id>", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    status = request.form.get("status")
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    db.close()
    flash(f"Order #{order_id} status updated to '{status}'.", "success")
    return redirect(url_for("admin_orders"))

# ----------------- Error Handlers ----------------- #
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
