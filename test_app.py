import unittest
from app import app
from database import get_db, init_db

class BookStoreTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_homepage(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Kitab', response.data)
        self.assertIn(b'Featured', response.data)

    def test_catalog_and_search(self):
        response = self.client.get('/books')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clean Code', response.data)

        # Search test
        search_res = self.client.get('/books?q=Python')
        self.assertEqual(search_res.status_code, 200)
        self.assertIn(b'Python Crash Course', search_res.data)

        # Category test
        cat_res = self.client.get('/books?category=Fiction')
        self.assertEqual(cat_res.status_code, 200)
        self.assertIn(b'The Alchemist', cat_res.data)

    def test_book_detail(self):
        response = self.client.get('/book/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Clean Code', response.data)

    def test_phone_otp_authentication_flow(self):
        # 1. Request OTP for existing student
        otp_res = self.client.post('/login', data={
            'action': 'send_otp',
            'phone': '9876543210'
        }, follow_redirects=True)
        self.assertEqual(otp_res.status_code, 200)
        self.assertIn(b'OTP sent successfully', otp_res.data)

        # Get generated OTP from session
        with self.client.session_transaction() as sess:
            otp_code = sess.get('login_otp')

        self.assertIsNotNone(otp_code)
        self.assertEqual(len(otp_code), 4)

        # 2. Verify OTP with correct code
        verify_res = self.client.post('/login', data={
            'action': 'verify_otp',
            'phone': '9876543210',
            'otp': otp_code
        }, follow_redirects=True)
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn(b'Aarav Sharma', verify_res.data)

        # 3. Logout
        self.client.get('/logout', follow_redirects=True)

        # 4. New user registration via OTP
        new_otp_res = self.client.post('/login', data={
            'action': 'send_otp',
            'phone': '9123456789'
        }, follow_redirects=True)
        self.assertEqual(new_otp_res.status_code, 200)

        with self.client.session_transaction() as sess:
            new_code = sess.get('login_otp')

        new_verify_res = self.client.post('/login', data={
            'action': 'verify_otp',
            'phone': '9123456789',
            'otp': new_code,
            'name': 'Pooja Patel'
        }, follow_redirects=True)
        self.assertEqual(new_verify_res.status_code, 200)
        self.assertIn(b'Pooja Patel', new_verify_res.data)

    def test_cart_and_checkout_flow(self):
        # Login demo student via OTP
        self.client.post('/login', data={'action': 'send_otp', 'phone': '9876543210'})
        with self.client.session_transaction() as sess:
            otp_code = sess.get('login_otp')
        self.client.post('/login', data={'action': 'verify_otp', 'phone': '9876543210', 'otp': otp_code})

        # Add book 1 to cart
        add_res = self.client.post('/cart/add/1', data={'quantity': 2}, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)

        # View cart
        cart_res = self.client.get('/cart')
        self.assertEqual(cart_res.status_code, 200)
        self.assertIn(b'Clean Code', cart_res.data)

        # Checkout
        checkout_res = self.client.post('/checkout', data={
            'full_name': 'Aarav Sharma',
            'email': 'student@example.com',
            'phone': '9876543210',
            'address': 'Boys Hostel Block 3, Room 204',
            'city': 'Bengaluru',
            'pincode': '560001',
            'payment_method': 'Cash on Delivery'
        }, follow_redirects=True)
        self.assertEqual(checkout_res.status_code, 200)
        self.assertIn(b'Order Confirmed', checkout_res.data)

        # View orders
        orders_res = self.client.get('/orders')
        self.assertEqual(orders_res.status_code, 200)
        self.assertIn(b'Clean Code', orders_res.data)

    def test_admin_flow(self):
        # Login admin via dedicated admin_login route
        login_res = self.client.post('/admin/login', data={
            'email': 'admin@bookstore.com',
            'password': 'admin123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Total Revenue', login_res.data)

        # Add a new book
        add_book_res = self.client.post('/admin/book/add', data={
            'title': 'Computer Networks by Tanenbaum',
            'author': 'Andrew S. Tanenbaum',
            'category': 'Computer Science',
            'price': 750.00,
            'original_price': 999.00,
            'stock': 20,
            'cover_image': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop&q=80',
            'description': 'Essential guide to networking principles for CS engineering students.',
            'featured': 1
        }, follow_redirects=True)
        self.assertEqual(add_book_res.status_code, 200)
        self.assertIn(b'Computer Networks', add_book_res.data)

        # Update order status
        update_status_res = self.client.post('/admin/order/status/1', data={
            'status': 'Delivered'
        }, follow_redirects=True)
        self.assertEqual(update_status_res.status_code, 200)

    def test_security_access_control(self):
        # Non-admin trying to access admin dashboard
        self.client.get('/logout', follow_redirects=True)
        unauth_res = self.client.get('/admin', follow_redirects=True)
        self.assertEqual(unauth_res.status_code, 200)
        self.assertIn(b'Please log in as an administrator', unauth_res.data)

    def test_add_review(self):
        # Login student via OTP
        self.client.post('/login', data={'action': 'send_otp', 'phone': '9876543210'})
        with self.client.session_transaction() as sess:
            otp_code = sess.get('login_otp')
        self.client.post('/login', data={'action': 'verify_otp', 'phone': '9876543210', 'otp': otp_code})

        rev_res = self.client.post('/book/1/review', data={
            'rating': 5,
            'comment': 'Awesome explanation of clean code standards!'
        }, follow_redirects=True)
        self.assertEqual(rev_res.status_code, 200)
        self.assertIn(b'Awesome explanation of clean code standards', rev_res.data)

if __name__ == '__main__':
    unittest.main()
