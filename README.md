# 📚 KitabKosh - Full-Stack Online Book Store

> **College 2nd Year Computer Science / IT Project**  
> Built with **Python (Flask)**, **SQLite3**, **Jinja2**, and **Bootstrap 5.3**.  
> Features complete **Authentication**, **Book Catalog & Search**, **Shopping Cart**, **Checkout Simulation**, **Order Tracking**, and an **Admin Dashboard**.

---

## 🌟 Key Features

### 👤 1. User & Customer Experience
- **Authentication**: Secure User Registration and Login using Werkzeug cryptographic password hashing.
- **Role-based Access**: Regular Customer accounts and Admin accounts.
- **Book Catalog**:
  - Filter by Category (Computer Science, Fiction, Finance, Self-Help, History, Science).
  - Live Search by Title or Author.
  - Sort by Price (Low to High, High to Low), Highest Rated, or Newest Arrivals.
- **Book Detail View**:
  - High-resolution cover images.
  - Dynamic stock availability indicator.
  - Verified user reviews & star ratings.
  - Direct "Write a Review" form with dynamic average rating recalculation.
  - Related books recommendations.
- **Shopping Cart**:
  - Add books with quantity selector.
  - Real-time quantity increment/decrement (`+` / `-`).
  - Item removal.
  - Free delivery threshold calculator (Free delivery on orders ₹500+).
- **Checkout & Order Flow**:
  - Complete delivery address collection.
  - Payment options (Cash on Delivery, simulated UPI / QR, simulated Card).
  - Automatic order number generation (`BK-2026-XXXXX`).
  - Automatic inventory stock decrement.
  - Printable invoice/receipt view.
- **Order History**:
  - Track order statuses (`Processing`, `Shipped`, `Delivered`, `Cancelled`).
  - Itemized history with timestamps.

### 👑 2. Administrator Panel (`/admin`)
- **Executive Dashboard**:
  - Total Revenue, Total Orders, Total Catalog Books, Total Registered Users.
  - Recent orders quick feed.
- **Inventory Management (`/admin/books`)**:
  - Add new books with cover images, prices, categories, and stock.
  - Edit existing book details.
  - Delete books from the catalog.
- **Order Management (`/admin/orders`)**:
  - View all customer orders, delivery addresses, and phone numbers.
  - Instant status updater dropdown (`Processing` &rarr; `Shipped` &rarr; `Delivered` &rarr; `Cancelled`).

---

## 🏗️ Project Architecture & Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend** | Python 3.13, Flask 3.1 | Modular route handlers, session management, decorators |
| **Database** | SQLite3 (`bookstore.db`) | Relational DB with Foreign Keys, Auto-Seeded out of the box |
| **Security** | Werkzeug Security | `generate_password_hash` & `check_password_hash` (pbkdf2:sha256) |
| **Frontend** | Jinja2, HTML5, CSS3 | Custom CSS + Bootstrap 5.3 + Font Awesome 6 Icons |
| **Production WSGI** | Gunicorn | Production-ready HTTP server for cloud deployments |

### 📂 Directory Structure
```
online book store/
│
├── app.py                  # Main Flask application and all route handlers
├── database.py             # Database creation, schema, and sample book seeders
├── bookstore.db            # SQLite database (auto-generated)
├── test_app.py             # Automated unit tests for all routes & flows
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Master layout with navbar, cart badge & footer
│   ├── index.html          # Homepage with hero, bestsellers & features
│   ├── books.html          # Catalog listing with filters & search
│   ├── book_detail.html    # Single book view with reviews & related books
│   ├── cart.html           # Interactive shopping cart
│   ├── checkout.html       # Delivery details & payment selection
│   ├── order_success.html  # Order confirmation & printable invoice
│   ├── orders.html         # User order tracking history
│   ├── login.html          # Login page (includes 1-click test credentials)
│   ├── register.html       # Registration page
│   ├── 404.html            # Custom not found page
│   ├── 500.html            # Custom server error page
│   └── admin/
│       ├── dashboard.html  # Admin overview & sales metrics
│       ├── books.html      # Manage book inventory table
│       ├── book_form.html  # Add / Edit book form
│       └── orders.html     # Manage customer orders & statuses
│
├── static/
│   ├── css/
│   │   └── style.css       # Custom design system & animations
│   └── js/
│       └── main.js         # Client-side scripts & 1-click test fillers
│
├── requirements.txt        # Python package dependencies
├── Procfile                # Cloud process configuration for Render/Railway
├── runtime.txt             # Python runtime specification
└── README.md               # Complete documentation & college viva guide
```

---

## ⚡ Quick Start (Running Locally)

### 1. Requirements
Ensure Python 3 is installed:
```bash
python --version
```

### 2. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 3. Initialize Database (Optional, app.py runs this automatically)
```bash
python database.py
```

### 4. Run the Development Server
```bash
python app.py
```
Open your browser and navigate to:  
👉 **`http://127.0.0.1:5000`**

---

## 🔑 Authentication System

### 1. Student / Customer Sign In (Mobile Number & OTP)
- Customers & students can sign in instantly using their **10-digit mobile number**.
- Click **"Get OTP"**: A 4-digit verification code is instantly sent and shown on the screen.
- Enter the code to verify & sign in.
- If it's a first-time user, an account is automatically created on the spot!

### 2. Administrator Access (`/admin/login`)
- Protected login portal for store administrators.
- Access via: `http://127.0.0.1:5000/admin/login` or via the footer link on the login page.
- Note: Admin credentials are kept confidential and are not displayed on the public UI.

---

## 🚀 Free Deployment Guide

This project is 100% deployment-ready. You can deploy it for free on **Render**, **Railway**, or **PythonAnywhere**.

### Option A: Deploy on Render.com (Recommended - 100% Free)
1. Push this project folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for KitabKosh Book Store"
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to [Render.com](https://render.com) and click **"New +" &rarr; "Web Service"**.
3. Connect your GitHub repository.
4. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Create Web Service**. Your book store will be live with a free `https://...onrender.com` URL!

### Option B: Deploy on PythonAnywhere (Free)
1. Sign up at [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Open a Bash console and upload or clone your files.
3. In the **Web** tab, configure a manual Flask app pointing to `app.py`.
4. Install requirements: `pip install -r requirements.txt`.

---

## 🎓 College Viva & Practical Exam Questions & Answers

If your professor or external examiner asks questions about this project, here are the ready answers:

**Q1: What architecture does this application follow?**  
*Answer:* It follows the **MVC (Model-View-Controller)** pattern common in web frameworks. The Models are defined via SQLite schema in `database.py`, Views are Jinja2 templates (`templates/*.html`), and Controllers are the Flask routes in `app.py`.

**Q2: Why use SQLite instead of MySQL or PostgreSQL?**  
*Answer:* SQLite is a serverless, zero-configuration relational database engine embedded directly into Python. It stores data locally in a single file (`bookstore.db`), eliminating the overhead of managing a separate database daemon while providing full ACID transactions and Foreign Key constraints.

**Q3: How is password security handled?**  
*Answer:* Passwords are never stored in plain text. We use `werkzeug.security.generate_password_hash` which generates a salted SHA-256 / PBKDF2 cryptographic hash, protecting user credentials against dictionary and rainbow-table attacks.

**Q4: How does session management work?**  
*Answer:* Flask uses cryptographically signed client-side session cookies using a secret key (`SECRET_KEY`). When a user logs in, their `user_id` and role are serialized into the signed session, allowing authentication persistence across requests.

**Q5: What happens when an order is placed?**  
*Answer:* The checkout controller performs three atomic database operations:
1. Inserts the order metadata in the `orders` table.
2. Loops through cart items and inserts records into `order_items`, while simultaneously decrementing the `stock` count in the `books` table.
3. Clears the customer's items from the `cart` table.
