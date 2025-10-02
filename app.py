from flask import Flask, request, jsonify, redirect, session, render_template
import hmac
import hashlib
import time
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urlencode

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this')

# Simple in-memory storage for shops (ใน production ควรใช้ database)
shops_storage = {}

# Shopee API Configuration
PARTNER_ID = os.getenv('SHOPEE_PARTNER_ID')
PARTNER_KEY = os.getenv('SHOPEE_PARTNER_KEY')
REDIRECT_URI = os.getenv('SHOPEE_REDIRECT_URI')
BASE_URL = os.getenv('SHOPEE_BASE_URL', 'https://partner.test-stable.shopeemobile.com')

# Validate required environment variables
if not PARTNER_ID or not PARTNER_KEY:
    print("ERROR: Missing required environment variables")
    print("Please set SHOPEE_PARTNER_ID and SHOPEE_PARTNER_KEY")
    print("For Railway deployment, set these in your project's environment variables")
    exit(1)

PARTNER_ID = int(PARTNER_ID)

# ==================== HELPER FUNCTIONS ====================

def generate_signature(api_path, timestamp, access_token='', shop_id=''):
    """Generate HMAC-SHA256 signature for Shopee API"""
    base_string = f"{PARTNER_ID}{api_path}{timestamp}"

    if access_token and shop_id:
        base_string = f"{PARTNER_ID}{api_path}{timestamp}{access_token}{shop_id}"

    signature = hmac.new(
        PARTNER_KEY.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    return signature

def make_shopee_request(api_path, method='GET', body=None, access_token=None, shop_id=None):
    """Make authenticated request to Shopee API"""
    timestamp = int(time.time())
    signature = generate_signature(api_path, timestamp, access_token or '', shop_id or '')

    url = f"{BASE_URL}{api_path}"

    common_params = {
        'partner_id': PARTNER_ID,
        'timestamp': timestamp,
        'sign': signature
    }

    if access_token:
        common_params['access_token'] = access_token
    if shop_id:
        common_params['shop_id'] = shop_id

    headers = {'Content-Type': 'application/json'}

    try:
        if method == 'GET':
            response = requests.get(url, params=common_params, headers=headers)
        else:
            response = requests.post(url, params=common_params, json=body, headers=headers)

        return response.json()
    except Exception as e:
        return {'error': str(e)}

# ==================== AUTHORIZATION ENDPOINTS ====================

@app.route('/')
def index():
    """Home page with UI"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    # Force HTTPS for Railway
    host_url = request.host_url
    if 'railway.app' in host_url and host_url.startswith('http://'):
        host_url = host_url.replace('http://', 'https://')

    return jsonify({
        'status': 'running',
        'mode': 'PRODUCTION' if os.getenv('FLASK_ENV') == 'production' else 'TEST',
        'host_url': host_url,
        'endpoints': {
            'auth': '/auth/login',
            'callback': '/auth/callback',
            'update_price': '/api/update-price',
            'update_stock': '/api/update-stock',
            'refresh_token': '/api/refresh-token'
        }
    })

@app.route('/debug')
def debug():
    """Debug page for testing"""
    timestamp = int(time.time())
    api_path = '/api/v2/shop/auth_partner'

    # Get the correct host URL - check headers for Railway
    original_host = request.host_url
    forwarded_proto = request.headers.get('X-Forwarded-Proto', 'http')

    # Use HTTPS if forwarded header says so
    if forwarded_proto == 'https' and original_host.startswith('http://'):
        host_url = original_host.replace('http://', 'https://')
    else:
        host_url = original_host

    # For Railway, always use the environment variable redirect URI
    redirect_uri = os.getenv('SHOPEE_REDIRECT_URI')

    base_string = f"{PARTNER_ID}{api_path}{timestamp}"
    signature = hmac.new(
        PARTNER_KEY.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    params = {
        'partner_id': PARTNER_ID,
        'timestamp': timestamp,
        'sign': signature,
        'redirect': redirect_uri
    }

    auth_url = f"{BASE_URL}{api_path}?{urlencode(params)}"

    return render_template('debug.html',
        partner_id=os.getenv('SHOPEE_PARTNER_ID', 'NOT SET'),
        partner_key=os.getenv('SHOPEE_PARTNER_KEY', 'NOT SET'),
        redirect_uri=redirect_uri,
        base_url=BASE_URL,
        flask_env=os.getenv('FLASK_ENV', 'NOT SET'),
        host_url=host_url,  # Use corrected host URL
        original_host_url=original_host,  # Show original host for debugging
        url=request.url,
        timestamp=timestamp,
        base_string=base_string,
        signature=signature,
        auth_url=auth_url
    )

@app.route('/auth/login')
def auth_login():
    """Step 1: Generate authorization URL and redirect"""
    timestamp = int(time.time())
    api_path = '/api/v2/shop/auth_partner'

    # Always use the redirect URI from environment variable
    redirect_uri = os.getenv('SHOPEE_REDIRECT_URI')

    # Debug logging
    print(f"\n=== AUTH LOGIN DEBUG ===")
    print(f"Partner ID: {PARTNER_ID}")
    print(f"API Path: {api_path}")
    print(f"Redirect URI: {redirect_uri}")
    print(f"Timestamp: {timestamp}")
    print(f"========================\n")

    # Generate signature for auth_partner API
    # For auth_partner, base_string = partner_id + api_path + timestamp
    base_string = f"{PARTNER_ID}{api_path}{timestamp}"
    signature = hmac.new(
        PARTNER_KEY.encode('utf-8'),
        base_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    params = {
        'partner_id': PARTNER_ID,
        'timestamp': timestamp,
        'sign': signature,
        'redirect': redirect_uri
    }

    # Debug logging (remove in production)
    print(f"Auth login debug:")
    print(f"  Base string: {base_string}")
    print(f"  Redirect URI: {redirect_uri}")
    print(f"  Partner ID: {PARTNER_ID}")
    print(f"  Timestamp: {timestamp}")

    auth_url = f"{BASE_URL}{api_path}?{urlencode(params)}"

    return redirect(auth_url)

@app.route('/auth/callback')
@app.route('/callback')
def auth_callback():
    """Step 2: Handle callback and exchange code for access token"""
    code = request.args.get('code')
    shop_id = request.args.get('shop_id')
    shop_name = request.args.get('shop_name', f'ร้านค้า #{shop_id}')

    if not code or not shop_id:
        return jsonify({'error': 'Missing code or shop_id'}), 400

    # Exchange code for access token
    timestamp = int(time.time())
    api_path = '/api/v2/auth/token/get'

    # For token/get, no signature needed in the URL
    url = f"{BASE_URL}{api_path}"
    params = {
        'partner_id': PARTNER_ID,
        'timestamp': timestamp
    }

    body = {
        'code': code,
        'shop_id': int(shop_id),
        'partner_id': PARTNER_ID
    }

    response = requests.post(url, params=params, json=body)
    result = response.json()

    if result.get('error'):
        return jsonify(result), 400

    # Store shop information
    shops_storage[shop_id] = {
        'shop_id': shop_id,
        'shop_name': shop_name,
        'access_token': result.get('access_token'),
        'refresh_token': result.get('refresh_token'),
        'expire_in': result.get('expire_in'),
        'connected_at': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }

    # Also store in session for current session
    session['access_token'] = result.get('access_token')
    session['refresh_token'] = result.get('refresh_token')
    session['shop_id'] = shop_id
    session['expire_in'] = result.get('expire_in')

    # Return success page
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>เชื่อมต่อสำเร็จ</title>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen flex items-center justify-center">
        <div class="bg-white rounded-lg shadow p-8 max-w-md">
            <div class="text-green-500 text-center mb-4">
                <i class="fas fa-check-circle text-6xl"></i>
            </div>
            <h1 class="text-2xl font-bold text-center mb-4">เชื่อมต่อร้านค้าสำเร็จ!</h1>
            <p class="text-gray-600 text-center mb-6">
                ร้าน: {shop_name}<br>
                Shop ID: {shop_id}
            </p>
            <p class="text-sm text-gray-500 text-center mb-6">
                คุณสามารถปิดหน้าต่างนี้และกลับไปที่แอปพลิเคชันได้
            </p>
            <button onclick="window.close()" class="w-full bg-orange-500 text-white py-2 rounded hover:bg-orange-600">
                ปิดหน้าต่าง
            </button>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/refresh-token', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token"""
    refresh_token_value = session.get('refresh_token')
    shop_id = session.get('shop_id')

    if not refresh_token_value or not shop_id:
        return jsonify({'error': 'No refresh token or shop_id found'}), 401

    timestamp = int(time.time())
    api_path = '/api/v2/auth/access_token/get'
    signature = generate_signature(api_path, timestamp)

    url = f"{BASE_URL}{api_path}"
    params = {
        'partner_id': PARTNER_ID,
        'timestamp': timestamp,
        'sign': signature
    }

    body = {
        'refresh_token': refresh_token_value,
        'shop_id': int(shop_id),
        'partner_id': PARTNER_ID
    }

    response = requests.post(url, params=params, json=body)
    result = response.json()

    if result.get('error'):
        return jsonify(result), 400

    # Update session with new tokens
    session['access_token'] = result.get('access_token')
    session['refresh_token'] = result.get('refresh_token')

    return jsonify({
        'message': 'Token refreshed successfully',
        'expire_in': result.get('expire_in')
    })

# ==================== PRODUCT UPDATE ENDPOINTS ====================

@app.route('/api/shops')
def get_shops():
    """Get all connected shops"""
    return jsonify({
        'shops': list(shops_storage.values())
    })

@app.route('/api/update-price', methods=['POST'])
def update_price():
    """Update product price"""
    # Check session first
    access_token = session.get('access_token')
    shop_id = session.get('shop_id')

    # If no session, check for shop_id in request
    if not access_token:
        data = request.get_json()
        shop_id = data.get('shop_id')

        if shop_id and shop_id in shops_storage:
            access_token = shops_storage[shop_id]['access_token']
        else:
            return jsonify({'error': 'Not authorized. Please connect shop first'}), 401

    data = request.get_json()
    item_id = data.get('item_id')
    price = data.get('price')

    if not item_id or price is None:
        return jsonify({'error': 'item_id and price are required'}), 400

    api_path = '/api/v2/product/update_price'
    body = {
        'item_id': int(item_id),
        'price_list': [{
            'model_id': 0,  # 0 for item without variations
            'original_price': float(price)
        }]
    }

    result = make_shopee_request(api_path, 'POST', body, access_token, shop_id)

    return jsonify(result)

@app.route('/api/update-stock', methods=['POST'])
def update_stock():
    """Update product stock"""
    # Check session first
    access_token = session.get('access_token')
    shop_id = session.get('shop_id')

    # If no session, check for shop_id in request
    if not access_token:
        data = request.get_json()
        shop_id = data.get('shop_id')

        if shop_id and shop_id in shops_storage:
            access_token = shops_storage[shop_id]['access_token']
        else:
            return jsonify({'error': 'Not authorized. Please connect shop first'}), 401

    data = request.get_json()
    item_id = data.get('item_id')
    stock = data.get('stock')

    if not item_id or stock is None:
        return jsonify({'error': 'item_id and stock are required'}), 400

    api_path = '/api/v2/product/update_stock'
    body = {
        'item_id': int(item_id),
        'stock_list': [{
            'model_id': 0,  # 0 for item without variations
            'normal_stock': int(stock)
        }]
    }

    result = make_shopee_request(api_path, 'POST', body, access_token, shop_id)

    return jsonify(result)

@app.route('/api/batch-update', methods=['POST'])
def batch_update():
    """Batch update price and stock for multiple items"""
    # Check session first
    access_token = session.get('access_token')
    shop_id = session.get('shop_id')

    # If no session, check for shop_id in request
    if not access_token:
        data = request.get_json()
        shop_id = data.get('shop_id')

        if shop_id and shop_id in shops_storage:
            access_token = shops_storage[shop_id]['access_token']
        else:
            return jsonify({'error': 'Not authorized. Please connect shop first'}), 401

    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'error': 'items array is required'}), 400

    results = []

    for item in items:
        item_id = item.get('item_id')

        # Update price if provided
        if 'price' in item:
            api_path = '/api/v2/product/update_price'
            body = {
                'item_id': int(item_id),
                'price_list': [{
                    'model_id': 0,
                    'original_price': float(item['price'])
                }]
            }
            price_result = make_shopee_request(api_path, 'POST', body, access_token, shop_id)
            results.append({'item_id': item_id, 'price_update': price_result})

        # Update stock if provided
        if 'stock' in item:
            api_path = '/api/v2/product/update_stock'
            body = {
                'item_id': int(item_id),
                'stock_list': [{
                    'model_id': 0,
                    'normal_stock': int(item['stock'])
                }]
            }
            stock_result = make_shopee_request(api_path, 'POST', body, access_token, shop_id)
            results.append({'item_id': item_id, 'stock_update': stock_result})

    return jsonify({'results': results})

# ==================== RUN APPLICATION ====================

if __name__ == '__main__':
    # Get port from environment (Railway) or use 5000 for local
    port = int(os.getenv('PORT', 5000))

    # Disable debug mode in production
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'

    app.run(debug=debug_mode, host='0.0.0.0', port=port)