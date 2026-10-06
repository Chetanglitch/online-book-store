import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_NAME = "bookstore.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Books table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            original_price REAL,
            stock INTEGER DEFAULT 10,
            rating REAL DEFAULT 4.5,
            rating_count INTEGER DEFAULT 1,
            description TEXT,
            cover_image TEXT,
            featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Cart table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            UNIQUE(user_id, book_id)
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            pincode TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'Processing',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Order items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    ''')

    # Reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()

    # Ensure users table has phone column
    cursor.execute("PRAGMA table_info(users)")
    user_columns = [col[1] for col in cursor.fetchall()]
    if "phone" not in user_columns:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")

    # Ensure admin user exists
    cursor.execute("SELECT id FROM users WHERE email = 'admin@bookstore.com'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash("admin123")
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Store Admin", "admin@bookstore.com", admin_pass, "admin")
        )

    # Ensure demo student user exists
    cursor.execute("SELECT id FROM users WHERE email = 'student@example.com'")
    student_row = cursor.fetchone()
    if not student_row:
        student_pass = generate_password_hash("student123")
        cursor.execute(
            "INSERT INTO users (name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ("Aarav Sharma", "student@example.com", "9876543210", student_pass, "user")
        )
    else:
        cursor.execute("UPDATE users SET phone = '9876543210' WHERE id = ?", (student_row[0],))

    conn.commit()

    # Seed initial data if books is empty
    cursor.execute("SELECT COUNT(*) FROM books")
    book_count = cursor.fetchone()[0]

    if book_count == 0:
        seed_data(conn)

    conn.commit()
    conn.close()

def seed_data(conn):
    cursor = conn.cursor()
    sample_books = [
        (
            "Clean Code: A Handbook of Agile Software Craftsmanship",
            "Robert C. Martin",
            "Computer Science",
            699.00,
            999.00,
            18,
            4.8,
            124,
            "Even bad code can function. But if code isn't clean, it can bring a development organization to its knees. Every year, countless hours and significant resources are lost because of poorly written code. This book is a must-read for any serious programmer.",
            "https://images.unsplash.com/photo-1532012164546-f432f2e3777a?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "Python Crash Course: Hands-on Project-based Programming",
            "Eric Matthes",
            "Computer Science",
            549.00,
            799.00,
            25,
            4.9,
            210,
            "A fast-paced, thorough introduction to programming with Python that will have you writing programs, solving problems, and making things that work in no time. Perfect for college students and beginners.",
            "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "The Psychology of Money",
            "Morgan Housel",
            "Finance",
            399.00,
            550.00,
            30,
            4.8,
            380,
            "Doing well with money isn't necessarily about what you know. It's about how you behave. And behavior is hard to teach, even to really smart people. Timeless lessons on wealth, greed, and happiness.",
            "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "Atomic Habits",
            "James Clear",
            "Self-Help",
            499.00,
            699.00,
            40,
            4.9,
            520,
            "No matter your goals, Atomic Habits offers a proven framework for improving—every day. James Clear, one of the world's leading experts on habit formation, reveals practical strategies to master tiny behaviors that lead to remarkable results.",
            "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "To Kill a Mockingbird",
            "Harper Lee",
            "Fiction",
            349.00,
            499.00,
            15,
            4.7,
            165,
            "A haunting portrait of race and class, innocence and injustice, hypocrisy and heroism, tradition and the transformation of the American South through the eyes of young Scout Finch.",
            "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=600&auto=format&fit=crop&q=80",
            0
        ),
        (
            "Data Structures & Algorithms Made Easy",
            "Narasimha Karumanchi",
            "Computer Science",
            599.00,
            850.00,
            22,
            4.6,
            140,
            "Comprehensive guide designed for college engineering students and interview preparation. Covers linked lists, trees, graphs, sorting, searching, dynamic programming with clear diagrams and code.",
            "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "Sapiens: A Brief History of Humankind",
            "Yuval Noah Harari",
            "History",
            450.00,
            650.00,
            14,
            4.7,
            290,
            "From a renowned historian comes a groundbreaking narrative of humanity's creation and evolution—exploring how biology and history have defined us and enhanced our understanding of what it means to be human.",
            "https://images.unsplash.com/photo-1461360370896-922624d12aa1?w=600&auto=format&fit=crop&q=80",
            0
        ),
        (
            "The Alchemist",
            "Paulo Coelho",
            "Fiction",
            299.00,
            399.00,
            35,
            4.8,
            430,
            "A magical story of Santiago, an Andalusian shepherd boy who yearns to travel in search of a worldly treasure as extravagant as any ever found. The story teaches us about listening to our hearts.",
            "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=80",
            1
        ),
        (
            "Introduction to Algorithms (CLRS)",
            "Thomas H. Cormen",
            "Computer Science",
            1199.00,
            1699.00,
            8,
            4.9,
            88,
            "The standard textbook algorithms book for universities worldwide. Combines rigor and comprehensiveness with in-depth analysis of algorithms and mathematical proofs.",
            "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=600&auto=format&fit=crop&q=80",
            0
        ),
        (
            "Rich Dad Poor Dad",
            "Robert T. Kiyosaki",
            "Finance",
            380.00,
            499.00,
            28,
            4.6,
            310,
            "What the rich teach their kids about money that the poor and middle class do not! Explodes the myth that you need to earn a high income to become rich and explains the difference between assets and liabilities.",
            "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=600&auto=format&fit=crop&q=80",
            0
        ),
        (
            "Deep Work: Rules for Focused Success",
            "Cal Newport",
            "Self-Help",
            420.00,
            599.00,
            19,
            4.7,
            180,
            "One of the most valuable skills in our economy is becoming increasingly rare. If you master this skill, you'll achieve extraordinary results. Essential reading for students looking to excel in academics and programming.",
            "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&auto=format&fit=crop&q=80",
            0
        ),
        (
            "1984",
            "George Orwell",
            "Fiction",
            280.00,
            350.00,
            16,
            4.8,
            245,
            "George Orwell's dystopian masterpiece depicting a totalitarian regime where Big Brother is always watching. A thought-provoking classic about surveillance, truth, and freedom.",
            "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=600&auto=format&fit=crop&q=80",
            0
        )
    ]

    cursor.executemany('''
        INSERT INTO books (title, author, category, price, original_price, stock, rating, rating_count, description, cover_image, featured)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_books)

    # Add sample reviews
    sample_reviews = [
        (1, 2, "Aarav Sharma", 5, "Every CS student should read this! It transformed how I write functions and variable names."),
        (2, 2, "Aarav Sharma", 5, "Clear examples and practical exercises. Got full marks in my college Python lab."),
        (4, 2, "Aarav Sharma", 5, "Helped me build a daily routine for coding and study. Highly recommended!")
    ]
    cursor.executemany('''
        INSERT INTO reviews (book_id, user_id, user_name, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_reviews)

if __name__ == "__main__":
    init_db()
    print("Database initialized and seeded successfully.")
