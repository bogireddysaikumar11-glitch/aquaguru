from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response, send_from_directory
import os
import uuid
import base64
from datetime import datetime, date
from decimal import Decimal
from config import Config

import json

# Unified Database Manager
from db import (
    get_db_connection, 
    init_db, 
    hash_password, 
    serialize_row, 
    serialize_rows, 
    get_active_engine
)

# Firebase Firestore Cloud Client
from firebase_db import FirestoreClient, sync_database_to_firestore

# Translation import
from translations import t, lang_data

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Water Quality Uploads Directory
WATER_QUALITY_UPLOAD_DIR = os.path.join(app.static_folder, 'uploads', 'water_quality')
os.makedirs(WATER_QUALITY_UPLOAD_DIR, exist_ok=True)

# Initialize database tables on startup (works on Render Gunicorn & local)
with app.app_context():
    try:
        init_db()
    except Exception as e:
        print(f"[STARTUP] Warning during init_db: {e}")

# ==================== GLOBAL VARIABLES ====================
@app.context_processor
def inject_globals():
    return {
        'now': datetime.now(),
        'db_engine': get_active_engine(),
        'firebase_config': Config.FIREBASE_CONFIG,
        'current_lang': session.get('lang', 'en'),
        'lang_data_json': json.dumps(lang_data)
    }

# Prevent browser from serving stale cached HTML so language switches instantly
@app.after_request
def add_no_cache_headers(response):
    if 'text/html' in response.headers.get('Content-Type', ''):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# ==================== LANGUAGE SETUP ====================
@app.before_request
def check_language():
    req_lang = request.args.get('lang')
    cookie_lang = request.cookies.get('lang')
    
    if req_lang in ['en', 'te']:
        session['lang'] = req_lang
    elif cookie_lang in ['en', 'te']:
        session['lang'] = cookie_lang
    elif 'lang' not in session or not session.get('lang'):
        session['lang'] = 'en'

@app.route('/set-language/<lang_code>')
def set_language(lang_code):
    if lang_code not in ['en', 'te']:
        lang_code = 'en'
    
    session['lang'] = lang_code
    session.permanent = True
    session.modified = True
    
    # Priority: next query parameter > referrer > dashboard
    next_page = request.args.get('next')
    redirect_target = url_for('dashboard')
    if next_page and next_page.startswith('/') and not next_page.startswith('/set-language'):
        redirect_target = next_page
    elif request.referrer and '/set-language' not in request.referrer:
        redirect_target = request.referrer
    
    resp = make_response(redirect(redirect_target))
    resp.set_cookie('lang', lang_code, max_age=365*86400, path='/')
    resp.set_cookie('googtrans', '', expires=0, path='/')
    return resp

# ==================== PWA ROUTES ====================
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/manifest+json')

@app.route('/sw.js')
def serve_sw():
    response = make_response(send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript'))
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.template_filter('translate')
def translate_filter(text):
    lang = session.get('lang', 'en')
    return t(text, lang)

@app.template_filter('days_since')
def days_since_filter(date_val):
    if not date_val:
        return 0
    if isinstance(date_val, str):
        try:
            date_val = datetime.strptime(date_val.split('T')[0].split(' ')[0], '%Y-%m-%d').date()
        except Exception:
            return 0
    elif isinstance(date_val, datetime):
        date_val = date_val.date()
    elif isinstance(date_val, date):
        pass
    else:
        return 0
    
    diff = (datetime.now().date() - date_val).days
    return max(0, diff)

# ==================== AUTHENTICATION FUNCTIONS ====================
def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('username') == 'admin'

def login_required(f):
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash('Please login to access this page.', 'danger')
            return redirect(url_for('login'))
        if not is_admin():
            flash('Only administrators can update market rates!', 'danger')
            return redirect(url_for('market_rates'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.context_processor
def inject_admin_status():
    return {'is_admin_user': is_admin()}

# ==================== MAIN ROUTES ====================
@app.route('/')
def index():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/test')
def test():
    engine = get_active_engine()
    return f"Hello! AquaGuru server is running smoothly with {engine.upper()} database engine."

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "AquaGuru", "engine": get_active_engine()}), 200

@app.route('/ping')
def ping():
    return "pong", 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_logged_in():
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        raw_username = request.form.get('username', '')
        raw_password = request.form.get('password', '')
        
        username = raw_username.strip()
        password = raw_password.strip()
        hashed_password = hash_password(raw_password)
        hashed_password_clean = hash_password(password)
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                # Case-insensitive username/email matching for mobile keyboards
                cursor.execute(
                    """SELECT * FROM users 
                       WHERE (LOWER(username) = LOWER(%s) OR LOWER(email) = LOWER(%s)) 
                         AND (password = %s OR password = %s)""",
                    (username, username, hashed_password, hashed_password_clean)
                )
                user = cursor.fetchone()
                if user:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Invalid username or password!', 'danger')
            except Exception as e:
                flash(f'Login error: {e}', 'danger')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed! Please check your settings.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters!', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = hash_password(password)
        
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s OR email = %s",
                    (username, email)
                )
                existing = cursor.fetchone()
                if existing:
                    flash('Username or email already exists!', 'danger')
                    return redirect(url_for('register'))
                
                cursor.execute(
                    "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                    (username, email, hashed_password)
                )
                connection.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                flash(f'Registration failed: {e}', 'danger')
            finally:
                cursor.close()
                connection.close()
        else:
            flash('Database connection failed!', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# ==================== DASHBOARD ====================
@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('dashboard.html', stats={}, growth_data=[], water_quality_data=[], expense_data=[])
    
    cursor = connection.cursor(dictionary=True)
    stats = {}
    growth_data = []
    water_quality_data = []
    expense_data = []
    
    try:
        user_id = session['user_id']
        cursor.execute("SELECT COUNT(*) as count FROM ponds WHERE user_id = %s", (user_id,))
        res = cursor.fetchone()
        stats['total_ponds'] = res['count'] if res else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM ponds WHERE user_id = %s AND status = 'active'", (user_id,))
        res = cursor.fetchone()
        stats['active_ponds'] = res['count'] if res else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM feed_records WHERE user_id = %s AND DATE(date) = CURDATE()", (user_id,))
        result = cursor.fetchone()
        stats['today_feed'] = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM feed_records WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        stats['total_feed'] = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT doc FROM growth_records WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        stats['current_doc'] = result['doc'] if result else 0
        
        cursor.execute("SELECT abw FROM growth_records WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        stats['avg_abw'] = result['abw'] if result else 0
        
        cursor.execute("SELECT survival FROM growth_records WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user_id,))
        result = cursor.fetchone()
        stats['survival'] = result['survival'] if result else 0
        
        cursor.execute("SELECT ph, do, temperature, ammonia, nitrite FROM water_quality WHERE user_id = %s ORDER BY date DESC LIMIT 1", (user_id,))
        water_data = cursor.fetchone()
        if water_data:
            issues = []
            ph = float(water_data.get('ph', 7.5) or 7.5)
            do_val = float(water_data.get('do', 5.0) or 5.0)
            temp = float(water_data.get('temperature', 28.0) or 28.0)
            ammonia = float(water_data.get('ammonia', 0.0) or 0.0)
            nitrite = float(water_data.get('nitrite', 0.0) or 0.0)

            if ph < 7.0 or ph > 8.5: issues.append('pH')
            if do_val < 4.0: issues.append('DO')
            if temp < 25 or temp > 32: issues.append('Temperature')
            if ammonia > 0.1: issues.append('Ammonia')
            if nitrite > 0.1: issues.append('Nitrite')
            
            if len(issues) == 0: stats['water_status'] = 'Good'
            elif len(issues) <= 2: stats['water_status'] = 'Moderate'
            else: stats['water_status'] = 'Poor'
        else:
            stats['water_status'] = 'No Data'
        
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s AND category = 'Feed'", (user_id,))
        result = cursor.fetchone()
        stats['feed_cost'] = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        stats['total_expenses'] = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0", (user_id,))
        res = cursor.fetchone()
        stats['notifications'] = res['count'] if res else 0
        
        cursor.execute("SELECT date, abw, doc, survival FROM growth_records WHERE user_id = %s ORDER BY date ASC LIMIT 30", (user_id,))
        growth_data = serialize_rows(cursor.fetchall())
        
        cursor.execute("SELECT date, ph, do, temperature FROM water_quality WHERE user_id = %s ORDER BY date ASC LIMIT 30", (user_id,))
        water_quality_data = serialize_rows(cursor.fetchall())
        
        cursor.execute("SELECT date, amount, category FROM expenses WHERE user_id = %s ORDER BY date DESC LIMIT 10", (user_id,))
        expense_data = serialize_rows(cursor.fetchall())
        
        # Latest daily shrimp market rates for dashboard (unique counts)
        cursor.execute("""
            SELECT count_size, price_per_kg, price_change, location, date, species 
            FROM market_rates 
            WHERE date = (SELECT MAX(date) FROM market_rates) AND (category = 'Shrimp' OR category IS NULL)
            GROUP BY count_size
            ORDER BY count_size ASC LIMIT 8
        """)
        today_rates = serialize_rows(cursor.fetchall())
        
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'danger')
        today_rates = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('dashboard.html', stats=stats, growth_data=growth_data, water_quality_data=water_quality_data, expense_data=expense_data, today_rates=today_rates)

# ==================== PONDS ====================
@app.route('/ponds')
@login_required
def ponds():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('ponds.html', ponds=[])
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s ORDER BY created_at DESC", (session['user_id'],))
        ponds_list = serialize_rows(cursor.fetchall())
    except Exception as e:
        flash(f'Error loading ponds: {e}', 'danger')
        ponds_list = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('ponds.html', ponds=ponds_list)

@app.route('/add-pond', methods=['POST'])
@login_required
def add_pond():
    pond_name = request.form.get('pond_name')
    area = request.form.get('area')
    seed_count = request.form.get('seed_count')
    species = request.form.get('species')
    stocking_date = request.form.get('stocking_date')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('ponds'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO ponds (user_id, pond_name, area, seed_count, species, stocking_date) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], pond_name, area, seed_count, species, stocking_date)
        )
        connection.commit()
        flash('Pond added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding pond: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('ponds'))

@app.route('/edit-pond', methods=['POST'])
@login_required
def edit_pond():
    pond_id = request.form.get('pond_id')
    pond_name = request.form.get('pond_name')
    area = request.form.get('area')
    seed_count = request.form.get('seed_count')
    species = request.form.get('species')
    stocking_date = request.form.get('stocking_date')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('ponds'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE ponds SET pond_name = %s, area = %s, seed_count = %s, species = %s, stocking_date = %s WHERE id = %s AND user_id = %s",
            (pond_name, area, seed_count, species, stocking_date, pond_id, session['user_id'])
        )
        connection.commit()
        flash('Pond updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating pond: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('ponds'))

@app.route('/delete-pond/<int:pond_id>', methods=['POST'])
@login_required
def delete_pond(pond_id):
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('ponds'))
    
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM ponds WHERE id = %s AND user_id = %s", (pond_id, session['user_id']))
        connection.commit()
        flash('Pond deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting pond: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('ponds'))

# ==================== FEED ====================
@app.route('/feed')
@login_required
def feed():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('feed.html', ponds=[])
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s AND status = 'active'", (session['user_id'],))
        ponds_list = serialize_rows(cursor.fetchall())
    except Exception as e:
        flash(f'Error loading ponds: {e}', 'danger')
        ponds_list = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('feed.html', ponds=ponds_list)

@app.route('/save-feed-record', methods=['POST'])
@login_required
def save_feed_record():
    pond_id = request.form.get('pond_id')
    date_val = request.form.get('date')
    doc = request.form.get('doc')
    abw = request.form.get('abw')
    survival = request.form.get('survival')
    feed_percentage = request.form.get('feed_percentage')
    biomass = request.form.get('biomass')
    daily_feed = request.form.get('daily_feed')
    feed_per_session = request.form.get('feed_per_session')
    amount = request.form.get('amount')
    feed_type = request.form.get('feed_type', 'Pellets')
    notes = request.form.get('notes', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('feed'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO feed_records (user_id, pond_id, date, doc, abw, survival, feed_percentage, biomass, daily_feed, feed_per_session, amount, feed_type, notes) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session['user_id'], pond_id, date_val, doc, abw, survival, feed_percentage, biomass, daily_feed, feed_per_session, amount, feed_type, notes)
        )
        connection.commit()
        flash('Feed record saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving feed record: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('feed'))

# ==================== WATER QUALITY ====================
@app.route('/water-quality')
@login_required
def water_quality():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('water_quality.html', ponds=[])
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s AND status = 'active'", (session['user_id'],))
        ponds_list = serialize_rows(cursor.fetchall())
    except Exception as e:
        flash(f'Error loading ponds: {e}', 'danger')
        ponds_list = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('water_quality.html', ponds=ponds_list)

@app.route('/save-water-quality', methods=['POST'])
@login_required
def save_water_quality():
    pond_id = request.form.get('pond_id')
    date_val = request.form.get('date')
    ph = float(request.form.get('ph', 7.5))
    do_val = float(request.form.get('do', 5.0))
    temperature = float(request.form.get('temperature', 28.0))
    salinity = request.form.get('salinity', 15.0)
    ammonia = float(request.form.get('ammonia', 0.0) or 0.0)
    nitrite = request.form.get('nitrite', 0.0)
    alkalinity = request.form.get('alkalinity', 120.0)
    transparency = request.form.get('transparency', 30.0)
    notes = request.form.get('notes', '')
    
    # Process Water Quality Photo (Files / Mobile Camera / Live Webcam Snapshot)
    image_path = None
    uploaded_file = request.files.get('photo_file') or request.files.get('photo_camera')
    if uploaded_file and uploaded_file.filename != '':
        ext = os.path.splitext(uploaded_file.filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.jfif']:
            filename = f"wq_{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}{ext}"
            file_full_path = os.path.join(WATER_QUALITY_UPLOAD_DIR, filename)
            uploaded_file.save(file_full_path)
            image_path = f"uploads/water_quality/{filename}"
            
    # Check for WebRTC Base64 camera snapshot
    photo_base64 = request.form.get('photo_base64', '').strip()
    if not image_path and photo_base64 and 'base64,' in photo_base64:
        try:
            header, encoded = photo_base64.split('base64,', 1)
            img_data = base64.b64decode(encoded)
            filename = f"wq_{session['user_id']}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}.jpg"
            file_full_path = os.path.join(WATER_QUALITY_UPLOAD_DIR, filename)
            with open(file_full_path, 'wb') as f:
                f.write(img_data)
            image_path = f"uploads/water_quality/{filename}"
        except Exception as e:
            print(f"[IMAGE SAVE ERROR] {e}")
    
    status = 'good'
    if ph < 7.0 or ph > 8.5 or do_val < 4.0:
        status = 'moderate'
    if ammonia > 0.1:
        status = 'poor'
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('water_quality'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO water_quality (user_id, pond_id, date, ph, do, temperature, salinity, ammonia, nitrite, alkalinity, transparency, notes, image_path, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session['user_id'], pond_id, date_val, ph, do_val, temperature, salinity, ammonia, nitrite, alkalinity, transparency, notes, image_path, status)
        )
        connection.commit()
        flash('Water quality record saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving water quality record: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('water_quality'))

# ==================== GROWTH ====================
@app.route('/growth')
@login_required
def growth():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('growth.html', ponds=[])
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s AND status = 'active'", (session['user_id'],))
        ponds_list = serialize_rows(cursor.fetchall())
    except Exception as e:
        flash(f'Error loading ponds: {e}', 'danger')
        ponds_list = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('growth.html', ponds=ponds_list)

@app.route('/save-growth-record', methods=['POST'])
@login_required
def save_growth_record():
    pond_id = request.form.get('pond_id')
    date_val = request.form.get('date')
    doc = request.form.get('doc')
    abw = request.form.get('abw')
    adg = request.form.get('adg', 0.15)
    survival = request.form.get('survival')
    biomass = request.form.get('biomass')
    fcr = request.form.get('fcr', 1.2)
    notes = request.form.get('notes', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('growth'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO growth_records (user_id, pond_id, date, doc, abw, adg, survival, biomass, fcr, notes) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session['user_id'], pond_id, date_val, doc, abw, adg, survival, biomass, fcr, notes)
        )
        connection.commit()
        flash('Growth record saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving growth record: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('growth'))

# ==================== EXPENSES ====================
@app.route('/expenses')
@login_required
def expenses():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('expenses.html', ponds=[], daily_expense=0, monthly_expense=0, total_expense=0)
    
    cursor = connection.cursor(dictionary=True)
    try:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s", (user_id,))
        ponds_list = serialize_rows(cursor.fetchall())
        
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s AND DATE(date) = CURDATE()", (user_id,))
        result = cursor.fetchone()
        daily_expense = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s AND MONTH(date) = MONTH(CURDATE()) AND YEAR(date) = YEAR(CURDATE())", (user_id,))
        result = cursor.fetchone()
        monthly_expense = result['total'] if result and result['total'] else 0
        
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        total_expense = result['total'] if result and result['total'] else 0
        
    except Exception as e:
        flash(f'Error loading expenses: {e}', 'danger')
        ponds_list = []
        daily_expense = 0
        monthly_expense = 0
        total_expense = 0
    finally:
        cursor.close()
        connection.close()
    
    return render_template('expenses.html', ponds=ponds_list, daily_expense=daily_expense, monthly_expense=monthly_expense, total_expense=total_expense)

@app.route('/save-expense', methods=['POST'])
@login_required
def save_expense():
    pond_id = request.form.get('pond_id') or None
    category = request.form.get('category')
    amount = request.form.get('amount')
    date_val = request.form.get('date')
    description = request.form.get('description', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('expenses'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "INSERT INTO expenses (user_id, pond_id, category, amount, date, description) VALUES (%s, %s, %s, %s, %s, %s)",
            (session['user_id'], pond_id, category, amount, date_val, description)
        )
        connection.commit()
        flash('Expense record saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving expense record: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('expenses'))

# ==================== INVENTORY ====================
@app.route('/inventory')
@login_required
def inventory():
    return render_template('inventory.html')

@app.route('/save-inventory', methods=['POST'])
@login_required
def save_inventory():
    item_name = request.form.get('item_name')
    category = request.form.get('category')
    quantity = request.form.get('quantity')
    unit = request.form.get('unit')
    min_quantity = request.form.get('min_quantity')
    current_quantity = request.form.get('current_quantity')
    price_per_unit = request.form.get('price_per_unit') or 0
    supplier = request.form.get('supplier', '')
    expiry_date = request.form.get('expiry_date') or None
    notes = request.form.get('notes', '')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('inventory'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO inventory (user_id, item_name, category, quantity, unit, min_quantity, current_quantity, price_per_unit, supplier, expiry_date, notes) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session['user_id'], item_name, category, quantity, unit, min_quantity, current_quantity, price_per_unit, supplier, expiry_date, notes)
        )
        connection.commit()
        flash('Inventory item added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding inventory item: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('inventory'))

# ==================== HARVEST ====================
@app.route('/harvest')
@login_required
def harvest():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('harvest.html', ponds=[], total_income=0, total_profit=0)
    
    cursor = connection.cursor(dictionary=True)
    try:
        user_id = session['user_id']
        cursor.execute("SELECT * FROM ponds WHERE user_id = %s", (user_id,))
        ponds_list = serialize_rows(cursor.fetchall())
        
        cursor.execute("SELECT SUM(income) as total_income, SUM(profit) as total_profit FROM harvest WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        total_income = result['total_income'] if result and result['total_income'] else 0
        total_profit = result['total_profit'] if result and result['total_profit'] else 0
        
    except Exception as e:
        flash(f'Error loading harvest data: {e}', 'danger')
        ponds_list = []
        total_income = 0
        total_profit = 0
    finally:
        cursor.close()
        connection.close()
    
    return render_template('harvest.html', ponds=ponds_list, total_income=total_income, total_profit=total_profit)

@app.route('/save-harvest', methods=['POST'])
@login_required
def save_harvest():
    pond_id = request.form.get('pond_id')
    harvest_date = request.form.get('harvest_date')
    production = float(request.form.get('production', 0))
    average_weight = float(request.form.get('average_weight', 0))
    price = float(request.form.get('price', 0))
    total_cost = float(request.form.get('total_cost', 0))
    survival_rate = request.form.get('survival_rate') or 85.0
    fcr = request.form.get('fcr') or 1.2
    notes = request.form.get('notes', '')
    
    income = production * price
    profit = income - total_cost
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('harvest'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            """INSERT INTO harvest (user_id, pond_id, harvest_date, production, average_weight, price, income, total_cost, profit, survival_rate, fcr, notes) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (session['user_id'], pond_id, harvest_date, production, average_weight, price, income, total_cost, profit, survival_rate, fcr, notes)
        )
        cursor.execute("UPDATE ponds SET status = 'harvested' WHERE id = %s AND user_id = %s", (pond_id, session['user_id']))
        connection.commit()
        flash('Harvest record saved successfully!', 'success')
    except Exception as e:
        flash(f'Error saving harvest record: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('harvest'))

# ==================== MARKET RATES (SHRIMP & FISH) ====================
@app.route('/market-rates')
@login_required
def market_rates():
    category = request.args.get('category', 'Shrimp')
    if category not in ['Shrimp', 'Fish']:
        category = 'Shrimp'
        
    species_filter = request.args.get('species', 'Vannamei' if category == 'Shrimp' else 'Rohu')
    location_filter = request.args.get('location', 'Andhra Pradesh')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template(
            'market_rates.html', 
            rates=[], 
            locations=[], 
            species_list=[], 
            latest_date=None, 
            current_location=location_filter, 
            current_species=species_filter, 
            current_category=category
        )
    
    cursor = connection.cursor(dictionary=True)
    try:
        # 1. Distinct Locations
        cursor.execute("SELECT DISTINCT location FROM market_rates ORDER BY location ASC")
        loc_rows = cursor.fetchall()
        locations = [r['location'] for r in loc_rows] if loc_rows else ['Andhra Pradesh', 'Bhimavaram', 'Nellore', 'Kakinada', 'Surat', 'Amalapuram']
        if 'Andhra Pradesh' not in locations:
            locations.insert(0, 'Andhra Pradesh')
        
        # 2. Distinct Species for Category
        cursor.execute("SELECT DISTINCT species FROM market_rates WHERE category = %s ORDER BY species ASC", (category,))
        spec_rows = cursor.fetchall()
        species_list = [r['species'] for r in spec_rows] if spec_rows else (['Vannamei', 'Black Tiger'] if category == 'Shrimp' else ['Rohu', 'Catla', 'Tilapia', 'Pangasius', 'Sea Bass', 'Murrel'])
        
        if species_filter not in species_list and species_list:
            species_filter = species_list[0]
            
        cursor.execute("SELECT MAX(date) as max_date FROM market_rates WHERE category = %s", (category,))
        max_res = cursor.fetchone()
        latest_date = max_res['max_date'] if max_res and max_res['max_date'] else date.today().isoformat()
        
        # 3. Query Rates with strict Deduplication
        if category == 'Shrimp':
            if location_filter and location_filter != 'All':
                cursor.execute(
                    """SELECT * FROM market_rates 
                       WHERE category = %s AND species = %s AND date = %s AND location = %s 
                       GROUP BY count_size 
                       ORDER BY count_size ASC""",
                    (category, species_filter, latest_date, location_filter)
                )
            else:
                cursor.execute(
                    """SELECT * FROM market_rates 
                       WHERE category = %s AND species = %s AND date = %s 
                       GROUP BY count_size 
                       ORDER BY count_size ASC""",
                    (category, species_filter, latest_date)
                )
        else:
            # Fish Category - group by species for location
            if location_filter and location_filter != 'All':
                cursor.execute(
                    """SELECT * FROM market_rates 
                       WHERE category = 'Fish' AND date = %s AND location = %s 
                       GROUP BY species 
                       ORDER BY price_per_kg DESC""",
                    (latest_date, location_filter)
                )
            else:
                cursor.execute(
                    """SELECT * FROM market_rates 
                       WHERE category = 'Fish' AND date = %s 
                       GROUP BY species 
                       ORDER BY price_per_kg DESC""",
                    (latest_date,)
                )
        rates = serialize_rows(cursor.fetchall())
        
    except Exception as e:
        flash(f'Error loading market rates: {e}', 'danger')
        rates = []
        locations = ['Andhra Pradesh', 'Bhimavaram', 'Nellore', 'Kakinada', 'Surat', 'Amalapuram']
        species_list = ['Vannamei', 'Black Tiger']
        latest_date = date.today().isoformat()
    finally:
        cursor.close()
        connection.close()
        
    return render_template(
        'market_rates.html', 
        rates=rates, 
        locations=locations, 
        species_list=species_list, 
        latest_date=latest_date, 
        current_location=location_filter, 
        current_species=species_filter, 
        current_category=category
    )

@app.route('/save-market-rate', methods=['POST'])
@admin_required
def save_market_rate():
    date_val = request.form.get('date', date.today().isoformat())
    category = request.form.get('category', 'Shrimp')
    count_size = int(request.form.get('count_size', 30))
    price_per_kg = float(request.form.get('price_per_kg', 0))
    price_change = float(request.form.get('price_change', 0.0))
    location = request.form.get('location', 'Andhra Pradesh')
    species = request.form.get('species', 'Vannamei')
    source = request.form.get('source', 'AquaGuru Market Index')
    
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('market_rates'))
    
    cur = conn.cursor(dictionary=True)
    try:
        # Check existing row for UPSERT (prevents duplicates)
        cur.execute(
            """SELECT id FROM market_rates 
               WHERE date = %s AND category = %s AND species = %s AND count_size = %s AND location = %s""",
            (date_val, category, species, count_size, location)
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """UPDATE market_rates 
                   SET price_per_kg = %s, price_change = %s, source = %s 
                   WHERE id = %s""",
                (price_per_kg, price_change, source, existing['id'])
            )
            flash('Market rate updated successfully!', 'success')
        else:
            cur.execute(
                """INSERT INTO market_rates (date, category, count_size, price_per_kg, price_change, location, species, source) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (date_val, category, count_size, price_per_kg, price_change, location, species, source)
            )
            flash('Market rate saved successfully!', 'success')
        conn.commit()
    except Exception as e:
        flash(f'Error saving market rate: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('market_rates', location=location, species=species, category=category))

@app.route('/delete-market-rate/<int:rate_id>', methods=['POST'])
@admin_required
def delete_market_rate(rate_id):
    conn = get_db_connection()
    if not conn:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('market_rates'))
    
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM market_rates WHERE id = %s", (rate_id,))
        conn.commit()
        flash('Market rate deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting market rate: {e}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('market_rates'))

# ==================== NOTIFICATIONS ====================
@app.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

# ==================== AI ASSISTANT ====================
@app.route('/ai-assistant')
@login_required
def ai_assistant():
    return render_template('ai_assistant.html')

@app.route('/api/ai-assistant', methods=['POST'])
@login_required
def ai_assistant_query():
    data = request.get_json() or {}
    question = data.get('question', '').lower()
    
    if 'low do' in question or 'dissolved oxygen' in question or 'oxygen' in question:
        response = """🔬 LOW DISSOLVED OXYGEN (DO) SOLUTION:
1. Increase aeration immediately (turn on all aerators/paddle wheels)
2. Reduce feeding by 30-50% to decrease organic load
3. Check for algal blooms or sudden die-offs
4. Conduct fresh water exchange if possible
5. Monitor oxygen levels every 2 hours
6. Keep sodium percarbonate or oxygen tablets ready for emergency use"""
    elif 'ammonia' in question or 'nh3' in question:
        response = """⚠️ HIGH AMMONIA SOLUTION:
1. Stop or drastically reduce feeding immediately
2. Increase water exchange by 20-30%
3. Apply commercial probiotics and bio-filters (Bacillus strains)
4. Check and adjust pH levels (higher pH increases toxic unionized ammonia)
5. Test ammonia twice daily
6. Consider applying zeolite or yucca extract for rapid binding"""
    elif 'white gut' in question or 'white feces' in question:
        response = """🦐 WHITE GUT / WHITE FECES SYNDROME:
1. Reduce feeding by 50%
2. Top-dress feed with gut probiotics and garlic extract
3. Check water quality parameters and bottom sludge
4. Test for EHP (Enterocytozoon hepatopenaei) and Vibrio bacteria
5. Disinfect pond bottom and eliminate carrier organisms
6. Add Vitamin C and beta-glucan immune stimulants to diet"""
    elif 'fcr' in question or 'feed conversion' in question:
        response = """📈 FCR (Feed Conversion Ratio) TIPS:
1. Target FCR: 1.2-1.5 for Vannamei, 1.4-1.8 for Monodon
2. Use feeding trays (check trays after 2-2.5 hours)
3. Adjust feed amount according to DOC, ABW, and weather
4. Maintain optimal water quality (stable DO & Temperature)
5. Avoid overfeeding during molt cycles
6. Use high-protein, nutrient-dense feed formulations"""
    elif 'water quality' in question or 'parameter' in question:
        response = """🌊 OPTIMAL WATER QUALITY PARAMETERS:
- pH: 7.5 - 8.5 (Daily fluctuation < 0.5)
- DO: > 4.0 mg/L (Preferably > 5.0 mg/L)
- Temperature: 28 - 32°C
- Salinity: 10 - 25 ppt
- Total Ammonia Nitrogen (TAN): < 0.1 mg/L
- Nitrite (NO2-): < 0.1 mg/L
- Alkalinity: > 120 mg/L CaCO3
- Transparency / Secchi: 30 - 40 cm"""
    elif 'ph' in question:
        response = """🧪 pH MANAGEMENT:
- Low pH (<7.5): Apply agricultural lime (CaCO3) or dolomite @ 20-30 kg/ha.
- High pH (>8.5): Apply fermented molasses/rice bran probiotics or dilute acetic acid."""
    else:
        response = """🤖 AQUAGURU AI ASSISTANT:
I can help you manage and diagnose:
- Dissolved Oxygen (DO) crises & Aeration
- High Ammonia & Nitrite treatment
- Feed calculation & FCR optimization
- White Gut / White Feces / EHP prevention
- Water parameter balancing (pH, Salinity, Alkalinity)

Feel free to ask any specific aquaculture question!"""
    
    return jsonify({'response': response})

# ==================== JSON API ENDPOINTS ====================

@app.route('/api/calculate-feed', methods=['POST'])
@login_required
def api_calculate_feed():
    data = request.get_json() or {}
    try:
        doc = float(data.get('doc', 30))
        abw = float(data.get('abw', 5.0))
        survival = float(data.get('survival', 85.0))
        feed_percentage = float(data.get('feed_percentage', 4.0))
        
        # Calculate biomass: assume 10000 seeds standard or fetch pond
        seed_count = 10000
        pond_id = data.get('pond_id')
        if pond_id:
            conn = get_db_connection()
            if conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT seed_count FROM ponds WHERE id = %s AND user_id = %s", (pond_id, session['user_id']))
                pond = cur.fetchone()
                if pond and pond.get('seed_count'):
                    seed_count = float(pond['seed_count'])
                cur.close()
                conn.close()
        
        biomass = (seed_count * (survival / 100.0) * abw) / 1000.0
        daily_feed = biomass * (feed_percentage / 100.0)
        feed_per_session = daily_feed / 4.0
        
        return jsonify({
            'biomass': f"{biomass:.2f}",
            'daily_feed': f"{daily_feed:.2f}",
            'feed_per_session': f"{feed_per_session:.2f}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/feed-records', methods=['GET'])
@login_required
def api_feed_records():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT f.*, p.pond_name 
               FROM feed_records f 
               LEFT JOIN ponds p ON f.pond_id = p.id 
               WHERE f.user_id = %s 
               ORDER BY f.date DESC LIMIT 50""",
            (session['user_id'],)
        )
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/water-quality', methods=['GET'])
@login_required
def api_water_quality():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT w.*, p.pond_name 
               FROM water_quality w 
               LEFT JOIN ponds p ON w.pond_id = p.id 
               WHERE w.user_id = %s 
               ORDER BY w.date DESC LIMIT 50""",
            (session['user_id'],)
        )
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/market-rates', methods=['GET'])
@login_required
def api_market_rates():
    category = request.args.get('category', 'Shrimp')
    species = request.args.get('species', 'Vannamei')
    location = request.args.get('location', 'Andhra Pradesh')
    
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT MAX(date) as max_date FROM market_rates WHERE category = %s", (category,))
        max_d = cur.fetchone()
        latest_date = max_d['max_date'] if max_d and max_d['max_date'] else date.today().isoformat()
        
        if location and location != 'All':
            cur.execute(
                """SELECT * FROM market_rates 
                   WHERE category = %s AND species = %s AND date = %s AND location = %s 
                   GROUP BY count_size 
                   ORDER BY count_size ASC""",
                (category, species, latest_date, location)
            )
        else:
            cur.execute(
                """SELECT * FROM market_rates 
                   WHERE category = %s AND species = %s AND date = %s 
                   GROUP BY count_size 
                   ORDER BY count_size ASC""",
                (category, species, latest_date)
            )
        rates = serialize_rows(cur.fetchall())
        return jsonify(rates)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/market-rates/history', methods=['GET'])
@login_required
def api_market_rates_history():
    category = request.args.get('category', 'Shrimp')
    species = request.args.get('species', 'Vannamei')
    count_size = request.args.get('count', 30, type=int)
    location = request.args.get('location', 'Andhra Pradesh')
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'dates': [], 'prices': []})
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT date, price_per_kg FROM market_rates 
               WHERE category = %s AND species = %s AND count_size = %s AND location = %s 
               GROUP BY date 
               ORDER BY date ASC LIMIT 30""",
            (category, species, count_size, location)
        )
        rows = serialize_rows(cur.fetchall())
        dates = [r['date'] for r in rows]
        prices = [float(r['price_per_kg']) for r in rows]
        return jsonify({'dates': dates, 'prices': prices, 'count': count_size, 'location': location, 'category': category, 'species': species})
    except Exception as e:
        return jsonify({'dates': [], 'prices': []})
    finally:
        cur.close()
        conn.close()

@app.route('/api/growth-records', methods=['GET'])
@login_required
def api_growth_records():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT g.*, p.pond_name 
               FROM growth_records g 
               LEFT JOIN ponds p ON g.pond_id = p.id 
               WHERE g.user_id = %s 
               ORDER BY g.date DESC LIMIT 50""",
            (session['user_id'],)
        )
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/expenses', methods=['GET'])
@login_required
def api_expenses():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT e.*, p.pond_name 
               FROM expenses e 
               LEFT JOIN ponds p ON e.pond_id = p.id 
               WHERE e.user_id = %s 
               ORDER BY e.date DESC LIMIT 50""",
            (session['user_id'],)
        )
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/inventory', methods=['GET'])
@login_required
def api_inventory():
    conn = get_db_connection()
    if not conn:
        return jsonify({'items': []})
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM inventory WHERE user_id = %s ORDER BY item_name ASC", (session['user_id'],))
        items = serialize_rows(cur.fetchall())
        return jsonify({'items': items})
    except Exception as e:
        return jsonify({'items': []})
    finally:
        cur.close()
        conn.close()

@app.route('/api/harvest-records', methods=['GET'])
@login_required
def api_harvest_records():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            """SELECT h.*, p.pond_name 
               FROM harvest h 
               LEFT JOIN ponds p ON h.pond_id = p.id 
               WHERE h.user_id = %s 
               ORDER BY h.harvest_date DESC LIMIT 50""",
            (session['user_id'],)
        )
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/api/notifications', methods=['GET'])
@login_required
def api_notifications():
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT * FROM notifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 50", (session['user_id'],))
        records = serialize_rows(cur.fetchall())
        return jsonify(records)
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

@app.route('/mark-notification-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False})
    cur = conn.cursor()
    try:
        cur.execute("UPDATE notifications SET is_read = 1 WHERE id = %s AND user_id = %s", (notification_id, session['user_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cur.close()
        conn.close()

@app.route('/api/reports/<report_type>', methods=['GET'])
@login_required
def api_reports(report_type):
    conn = get_db_connection()
    if not conn:
        return jsonify([])
    cur = conn.cursor(dictionary=True)
    user_id = session['user_id']
    try:
        if report_type == 'feed':
            cur.execute(
                """SELECT f.*, p.pond_name FROM feed_records f 
                   LEFT JOIN ponds p ON f.pond_id = p.id 
                   WHERE f.user_id = %s ORDER BY f.date DESC""",
                (user_id,)
            )
            return jsonify(serialize_rows(cur.fetchall()))
        elif report_type == 'growth':
            cur.execute(
                """SELECT g.*, p.pond_name FROM growth_records g 
                   LEFT JOIN ponds p ON g.pond_id = p.id 
                   WHERE g.user_id = %s ORDER BY g.date DESC""",
                (user_id,)
            )
            return jsonify(serialize_rows(cur.fetchall()))
        elif report_type == 'expense':
            cur.execute(
                """SELECT e.*, p.pond_name FROM expenses e 
                   LEFT JOIN ponds p ON e.pond_id = p.id 
                   WHERE e.user_id = %s ORDER BY e.date DESC""",
                (user_id,)
            )
            return jsonify(serialize_rows(cur.fetchall()))
        elif report_type == 'water':
            cur.execute(
                """SELECT w.*, p.pond_name FROM water_quality w 
                   LEFT JOIN ponds p ON w.pond_id = p.id 
                   WHERE w.user_id = %s ORDER BY w.date DESC""",
                (user_id,)
            )
            return jsonify(serialize_rows(cur.fetchall()))
        elif report_type == 'harvest':
            cur.execute(
                """SELECT h.*, p.pond_name FROM harvest h 
                   LEFT JOIN ponds p ON h.pond_id = p.id 
                   WHERE h.user_id = %s ORDER BY h.harvest_date DESC""",
                (user_id,)
            )
            return jsonify(serialize_rows(cur.fetchall()))
        elif report_type == 'full':
            cur.execute("SELECT COUNT(*) as total FROM ponds WHERE user_id = %s", (user_id,))
            tp = cur.fetchone()['total']
            cur.execute("SELECT COUNT(*) as active FROM ponds WHERE user_id = %s AND status = 'active'", (user_id,))
            ap = cur.fetchone()['active']
            cur.execute("SELECT SUM(amount) as total FROM expenses WHERE user_id = %s", (user_id,))
            te = cur.fetchone()['total'] or 0
            cur.execute("SELECT SUM(amount) as total FROM feed_records WHERE user_id = %s", (user_id,))
            tf = cur.fetchone()['total'] or 0
            return jsonify({
                'total_ponds': tp,
                'active_ponds': ap,
                'total_expenses': float(te),
                'total_feed': float(tf)
            })
        else:
            return jsonify([])
    except Exception as e:
        return jsonify([])
    finally:
        cur.close()
        conn.close()

# ==================== PROFILE ====================
@app.route('/profile')
@login_required
def profile():
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return render_template('profile.html', user=None, total_ponds=0)
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = serialize_row(cursor.fetchone())
        cursor.execute("SELECT COUNT(*) as count FROM ponds WHERE user_id = %s", (session['user_id'],))
        result = cursor.fetchone()
        total_ponds = result['count'] if result else 0
    except Exception as e:
        flash(f'Error loading profile: {e}', 'danger')
        user = None
        total_ponds = 0
    finally:
        cursor.close()
        connection.close()
    
    return render_template('profile.html', user=user, total_ponds=total_ponds)

@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    address = request.form.get('address')
    farm_name = request.form.get('farm_name')
    
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('profile'))
    
    cursor = connection.cursor()
    try:
        cursor.execute(
            "UPDATE users SET full_name = %s, phone = %s, address = %s, farm_name = %s WHERE id = %s",
            (full_name, phone, address, farm_name, session['user_id'])
        )
        connection.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating profile: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('profile'))

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if new_password != confirm_password:
        flash('New passwords do not match!', 'danger')
        return redirect(url_for('profile'))
    if len(new_password) < 6:
        flash('Password must be at least 6 characters!', 'danger')
        return redirect(url_for('profile'))
    
    hashed_current = hash_password(current_password)
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed!', 'danger')
        return redirect(url_for('profile'))
    
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute("SELECT password FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        if user and user['password'] != hashed_current:
            flash('Current password is incorrect!', 'danger')
            return redirect(url_for('profile'))
        
        hashed_new = hash_password(new_password)
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_new, session['user_id']))
        connection.commit()
        flash('Password changed successfully!', 'success')
    except Exception as e:
        flash(f'Error changing password: {e}', 'danger')
    finally:
        cursor.close()
        connection.close()
    
    return redirect(url_for('profile'))

# ==================== REPORTS ====================
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# ==================== LEGAL & LANDING ====================
@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ==================== FIREBASE FIRESTORE API ====================
@app.route('/api/firebase/status')
def firebase_status():
    ok, msg = FirestoreClient.test_connection()
    return jsonify({
        'connected': ok,
        'message': msg,
        'project_id': Config.FIREBASE_PROJECT_ID
    })

@app.route('/api/firebase/sync', methods=['POST'])
@login_required
def firebase_sync():
    res = sync_database_to_firestore()
    return jsonify(res)

# ==================== MAIN ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("=" * 60)
    print("AquaGuru - Smart Shrimp & Aquaculture Farm Management")
    print(f"Active Database Engine: {get_active_engine().upper()}")
    print(f"Server starting on http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port, debug=Config.DEBUG)