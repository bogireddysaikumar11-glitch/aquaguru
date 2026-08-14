# db.py
"""
AquaGuru Database Manager
Supports Cloud MySQL (Render, TiDB, Aiven, Railway, AWS RDS, XAMPP)
with automatic SQLite fallback for zero-configuration deployments.
"""
import os
import sqlite3
import re
import hashlib
from datetime import datetime, date
from decimal import Decimal
from config import Config

# Try importing MySQL connectors
MYSQL_AVAILABLE = False
try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
    MYSQL_AVAILABLE = True
except ImportError:
    try:
        import pymysql
        import pymysql.cursors
        MySQLError = pymysql.Error
        MYSQL_AVAILABLE = True
    except ImportError:
        MySQLError = Exception


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def serialize_value(val):
    """Serialize values for JSON compatibility."""
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='ignore')
    return val


def serialize_row(row):
    """Converts a database row dictionary to JSON-safe dictionary."""
    if row is None:
        return None
    if isinstance(row, dict):
        return {k: serialize_value(v) for k, v in row.items()}
    return row


def serialize_rows(rows):
    """Converts a list of rows to JSON-safe dictionaries."""
    if not rows:
        return []
    return [serialize_row(r) for r in rows]


class SQLiteCursorWrapper:
    """Wraps SQLite cursor to provide MySQL-compatible interface and query translation."""
    def __init__(self, cursor, dictionary=False):
        self.cursor = cursor
        self.dictionary = dictionary
        self.lastrowid = None
        self.rowcount = -1

    def _translate_query(self, query):
        """Translates MySQL query syntax to SQLite syntax."""
        q = query
        # Translate MySQL Date functions to SQLite
        q = re.sub(r'DATE\(date\)\s*=\s*CURDATE\(\)', "date(date) = date('now', 'localtime')", q, flags=re.IGNORECASE)
        q = re.sub(r'MONTH\(date\)\s*=\s*MONTH\(CURDATE\(\)\)\s*AND\s*YEAR\(date\)\s*=\s*YEAR\(CURDATE\(\)\)', 
                   "strftime('%Y-%m', date) = strftime('%Y-%m', 'now', 'localtime')", q, flags=re.IGNORECASE)
        q = re.sub(r'\bCURDATE\(\)', "date('now', 'localtime')", q, flags=re.IGNORECASE)
        q = re.sub(r'\bNOW\(\)', "datetime('now', 'localtime')", q, flags=re.IGNORECASE)
        
        # Replace %s with ? parameter placeholders
        q = q.replace('%s', '?')
        return q

    def execute(self, query, params=None):
        translated = self._translate_query(query)
        try:
            if params is None:
                self.cursor.execute(translated)
            else:
                # Ensure params is a tuple or list
                if not isinstance(params, (list, tuple)):
                    params = (params,)
                self.cursor.execute(translated, params)
            self.lastrowid = self.cursor.lastrowid
            self.rowcount = self.cursor.rowcount
            return self
        except Exception as e:
            raise e

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.dictionary:
            return dict(row)
        return row

    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.dictionary:
            return [dict(r) for r in rows]
        return rows

    def close(self):
        try:
            self.cursor.close()
        except Exception:
            pass


class SQLiteConnectionWrapper:
    """Wraps sqlite3.Connection to provide MySQL-compatible interface."""
    def __init__(self, conn):
        self.conn = conn
        self.conn.row_factory = sqlite3.Row

    def cursor(self, dictionary=False):
        return SQLiteCursorWrapper(self.conn.cursor(), dictionary=dictionary)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def get_sqlite_connection():
    """Connects to SQLite database file with WAL mode and performance optimizations."""
    db_path = Config.SQLITE_PATH
    conn = sqlite3.connect(db_path, check_same_thread=False, timeout=20.0)
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -64000;")
        conn.execute("PRAGMA temp_store = MEMORY;")
    except Exception:
        pass
    return SQLiteConnectionWrapper(conn)


def get_mysql_connection():
    """Attempts to connect to MySQL database."""
    if not MYSQL_AVAILABLE:
        return None

    # Try mysql.connector first
    if 'mysql.connector' in globals() or 'mysql.connector' in sys_modules():
        try:
            kwargs = {
                'host': Config.MYSQL_HOST,
                'port': Config.MYSQL_PORT,
                'user': Config.MYSQL_USER,
                'password': Config.MYSQL_PASSWORD,
                'database': Config.MYSQL_DATABASE,
                'connect_timeout': 2
            }
            if Config.MYSQL_SSL_MODE:
                kwargs['ssl_mode'] = Config.MYSQL_SSL_MODE
            if Config.MYSQL_SSL_CA:
                kwargs['ssl_ca'] = Config.MYSQL_SSL_CA
            return mysql.connector.connect(**kwargs)
        except Exception:
            pass

    # Try pymysql
    try:
        import pymysql
        import pymysql.cursors
        kwargs = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DATABASE,
            'connect_timeout': 2,
            'cursorclass': pymysql.cursors.DictCursor
        }
        if Config.MYSQL_SSL_CA:
            kwargs['ssl'] = {'ca': Config.MYSQL_SSL_CA}
        return pymysql.connect(**kwargs)
    except Exception:
        return None


def sys_modules():
    import sys
    return sys.modules


_ACTIVE_ENGINE = None

def get_db_connection():
    """
    Returns an active database connection.
    Automatically connects to MySQL if configured, otherwise falls back gracefully to SQLite.
    Once the active engine is resolved, subsequent calls return instantly without connection timeouts.
    """
    global _ACTIVE_ENGINE

    # Fast path: if engine already resolved, return immediately (< 0.0005s)
    if _ACTIVE_ENGINE == 'sqlite':
        return get_sqlite_connection()
    elif _ACTIVE_ENGINE == 'mysql':
        conn = get_mysql_connection()
        if conn:
            return conn
        # If MySQL dropped, fallback to SQLite
        _ACTIVE_ENGINE = 'sqlite'
        return get_sqlite_connection()

    # Explicit SQLite mode
    if Config.DB_ENGINE == 'sqlite':
        _ACTIVE_ENGINE = 'sqlite'
        return get_sqlite_connection()

    # Explicit MySQL mode
    if Config.DB_ENGINE == 'mysql':
        conn = get_mysql_connection()
        if conn:
            _ACTIVE_ENGINE = 'mysql'
            return conn
        print("[DB WARNING] MySQL connection failed. DB_ENGINE is set to 'mysql'.")
        return None

    # Auto mode: try remote/cloud MySQL first
    if Config.DATABASE_URL or (Config.MYSQL_HOST and Config.MYSQL_HOST != 'localhost'):
        conn = get_mysql_connection()
        if conn:
            _ACTIVE_ENGINE = 'mysql'
            print("[DB INFO] Connected to Cloud MySQL engine.")
            return conn

    # Try local MySQL
    conn = get_mysql_connection()
    if conn:
        _ACTIVE_ENGINE = 'mysql'
        print("[DB INFO] Connected to Local MySQL engine.")
        return conn

    # Fallback to high-speed SQLite and lock active engine for ultra-fast queries
    if _ACTIVE_ENGINE != 'sqlite':
        print("[DB INFO] MySQL is not reachable. Using embedded high-speed SQLite database (aquaguru.db).")
        _ACTIVE_ENGINE = 'sqlite'
    return get_sqlite_connection()


def get_active_engine():
    return _ACTIVE_ENGINE or 'sqlite'


def init_db():
    """
    Initializes all database tables and seeds initial data if necessary.
    Works seamlessly across MySQL and SQLite.
    """
    conn = get_db_connection()
    if not conn:
        print("[DB ERROR] Could not establish database connection for init_db().")
        return False

    cursor = conn.cursor(dictionary=True)
    is_sqlite = (get_active_engine() == 'sqlite')

    try:
        if is_sqlite:
            # SQLite Schema
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                phone TEXT,
                address TEXT,
                farm_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ponds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_name TEXT NOT NULL,
                area REAL NOT NULL,
                seed_count INTEGER NOT NULL,
                species TEXT NOT NULL,
                stocking_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_id INTEGER,
                date TEXT NOT NULL,
                doc INTEGER NOT NULL,
                abw REAL NOT NULL,
                survival REAL NOT NULL,
                feed_percentage REAL NOT NULL,
                biomass REAL NOT NULL,
                daily_feed REAL NOT NULL,
                feed_per_session REAL NOT NULL,
                amount REAL NOT NULL,
                feed_type TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_id INTEGER,
                date TEXT NOT NULL,
                doc INTEGER NOT NULL,
                abw REAL NOT NULL,
                adg REAL NOT NULL,
                survival REAL NOT NULL,
                biomass REAL NOT NULL,
                fcr REAL NOT NULL,
                length_cm REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_quality (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_id INTEGER,
                date TEXT NOT NULL,
                ph REAL NOT NULL,
                do REAL NOT NULL,
                temperature REAL NOT NULL,
                salinity REAL,
                ammonia REAL,
                nitrite REAL,
                alkalinity REAL,
                transparency REAL,
                notes TEXT,
                image_path TEXT,
                status TEXT DEFAULT 'good',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_id INTEGER,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                receipt_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                min_quantity REAL NOT NULL,
                current_quantity REAL NOT NULL,
                price_per_unit REAL,
                supplier TEXT,
                expiry_date TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS harvest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                pond_id INTEGER,
                harvest_date TEXT NOT NULL,
                production REAL NOT NULL,
                average_weight REAL NOT NULL,
                price REAL NOT NULL,
                income REAL NOT NULL,
                total_cost REAL NOT NULL,
                profit REAL NOT NULL,
                survival_rate REAL,
                fcr REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                scheduled_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT DEFAULT 'Shrimp',
                count_size INTEGER NOT NULL,
                price_per_kg REAL NOT NULL,
                price_change REAL DEFAULT 0.0,
                location TEXT NOT NULL,
                species TEXT DEFAULT 'Vannamei',
                source TEXT DEFAULT 'AquaGuru Market Index',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date, category, species, count_size, location)
            );
            """)

        else:
            # MySQL Schema
            tables = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    full_name VARCHAR(100),
                    phone VARCHAR(20),
                    address TEXT,
                    farm_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS ponds (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_name VARCHAR(100) NOT NULL,
                    area DECIMAL(10,2) NOT NULL,
                    seed_count INT NOT NULL,
                    species VARCHAR(50) NOT NULL,
                    stocking_date DATE NOT NULL,
                    status ENUM('active', 'harvested', 'preparing') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS feed_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_id INT,
                    date DATE NOT NULL,
                    doc INT NOT NULL,
                    abw DECIMAL(10,2) NOT NULL,
                    survival DECIMAL(5,2) NOT NULL,
                    feed_percentage DECIMAL(5,2) NOT NULL,
                    biomass DECIMAL(10,2) NOT NULL,
                    daily_feed DECIMAL(10,2) NOT NULL,
                    feed_per_session DECIMAL(10,2) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    feed_type VARCHAR(50),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS growth_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_id INT,
                    date DATE NOT NULL,
                    doc INT NOT NULL,
                    abw DECIMAL(10,2) NOT NULL,
                    adg DECIMAL(10,2) NOT NULL,
                    survival DECIMAL(5,2) NOT NULL,
                    biomass DECIMAL(10,2) NOT NULL,
                    fcr DECIMAL(10,2) NOT NULL,
                    length_cm DECIMAL(10,2),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS water_quality (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_id INT,
                    date DATETIME NOT NULL,
                    ph DECIMAL(4,2) NOT NULL,
                    do DECIMAL(5,2) NOT NULL,
                    temperature DECIMAL(5,2) NOT NULL,
                    salinity DECIMAL(5,2),
                    ammonia DECIMAL(6,3),
                    nitrite DECIMAL(6,3),
                    alkalinity DECIMAL(6,2),
                    transparency DECIMAL(5,2),
                    notes TEXT,
                    image_path VARCHAR(255),
                    status ENUM('good', 'moderate', 'poor') DEFAULT 'good',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_id INT,
                    category VARCHAR(50) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    receipt_path VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    item_name VARCHAR(100) NOT NULL,
                    category ENUM('Feed', 'Medicine', 'Minerals', 'Probiotics', 'Lime', 'Chemicals', 'Other') NOT NULL,
                    quantity DECIMAL(10,2) NOT NULL,
                    unit VARCHAR(20) NOT NULL,
                    min_quantity DECIMAL(10,2) NOT NULL,
                    current_quantity DECIMAL(10,2) NOT NULL,
                    price_per_unit DECIMAL(10,2),
                    supplier VARCHAR(100),
                    expiry_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS harvest (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    pond_id INT,
                    harvest_date DATE NOT NULL,
                    production DECIMAL(10,2) NOT NULL,
                    average_weight DECIMAL(10,2) NOT NULL,
                    price DECIMAL(10,2) NOT NULL,
                    income DECIMAL(10,2) NOT NULL,
                    total_cost DECIMAL(10,2) NOT NULL,
                    profit DECIMAL(10,2) NOT NULL,
                    survival_rate DECIMAL(5,2),
                    fcr DECIMAL(10,2),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (pond_id) REFERENCES ponds(id) ON DELETE SET NULL
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type ENUM('feed_reminder', 'water_test', 'harvest_reminder', 'low_stock', 'general') NOT NULL,
                    is_read BOOLEAN DEFAULT FALSE,
                    scheduled_date DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """,
                """
                CREATE TABLE IF NOT EXISTS market_rates (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    count_size INT NOT NULL,
                    price_per_kg DECIMAL(10,2) NOT NULL,
                    price_change DECIMAL(6,2) DEFAULT 0.0,
                    location VARCHAR(100) NOT NULL,
                    species VARCHAR(50) DEFAULT 'Vannamei',
                    source VARCHAR(100) DEFAULT 'AquaGuru Market Index',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            ]
            for sql in tables:
                cursor.execute(sql)

        # Auto-migrations
        try:
            cursor.execute("ALTER TABLE water_quality ADD COLUMN image_path TEXT")
            conn.commit()
        except Exception:
            pass

        try:
            cursor.execute("ALTER TABLE market_rates ADD COLUMN category TEXT DEFAULT 'Shrimp'")
            conn.commit()
        except Exception:
            pass

        # Seed default admin user if none exists
        cursor.execute("SELECT COUNT(*) as count FROM users")
        res = cursor.fetchone()
        user_count = res['count'] if isinstance(res, dict) else res[0]

        if user_count == 0:
            admin_pwd = hash_password('admin')
            cursor.execute(
                "INSERT INTO users (username, email, password, full_name, farm_name) VALUES (%s, %s, %s, %s, %s)",
                ('admin', 'admin@aquaguru.com', admin_pwd, 'Admin User', 'AquaGuru Farm')
            )
            
            # Add sample pond
            cursor.execute(
                "INSERT INTO ponds (user_id, pond_name, area, seed_count, species, stocking_date) VALUES (%s, %s, %s, %s, %s, %s)",
                (1, 'Pond A1', 2.5, 10000, 'Vannamei', date.today().isoformat())
            )
            
            # Add sample notification
            cursor.execute(
                "INSERT INTO notifications (user_id, title, message, type) VALUES (%s, %s, %s, %s)",
                (1, 'Welcome to AquaGuru', 'Your smart shrimp farm management dashboard is ready!', 'general')
            )

        # Seed daily shrimp & fish market rates if table has few records
        cursor.execute("SELECT COUNT(*) as count FROM market_rates")
        rate_res = cursor.fetchone()
        rate_count = rate_res['count'] if isinstance(rate_res, dict) else rate_res[0]

        if rate_count < 10:
            from datetime import timedelta
            today = date.today()
            locations = ['Andhra Pradesh', 'Bhimavaram', 'Nellore', 'Kakinada', 'Surat', 'Amalapuram']
            
            # Standard shrimp market counts and reference prices (from Market Price index)
            shrimp_prices = {
                20: 650.0,
                25: 540.0,
                30: 470.0,
                40: 385.0,
                45: 355.0,
                50: 345.0,
                60: 325.0,
                70: 305.0,
                80: 295.0,
                90: 285.0,
                100: 275.0
            }
            
            fish_species_data = [
                ('Rohu', 1, 160.0),
                ('Catla', 1, 185.0),
                ('Tilapia', 1, 130.0),
                ('Pangasius', 1, 115.0),
                ('Sea Bass', 1, 420.0),
                ('Murrel', 1, 480.0)
            ]
            
            # Seed 7 days of historical and today's rates
            for day_offset in range(6, -1, -1):
                cur_date = (today - timedelta(days=day_offset)).isoformat()
                
                # Shrimp Rates
                for count_val, base_price in shrimp_prices.items():
                    for loc in locations:
                        loc_adj = 0.0 if loc == 'Andhra Pradesh' else (5.0 if loc == 'Bhimavaram' else (2.0 if loc == 'Nellore' else (-3.0 if loc == 'Kakinada' else -5.0)))
                        day_adj = (6 - day_offset) * 1.5
                        price = round(base_price + loc_adj + day_adj, 1)
                        change = round(2.5 if day_offset == 0 else 0.0, 1)
                        
                        try:
                            cursor.execute(
                                """INSERT OR REPLACE INTO market_rates (date, category, count_size, price_per_kg, price_change, location, species, source) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                (cur_date, 'Shrimp', count_val, price, change, loc, 'Vannamei', 'AquaGuru Market Feed')
                            )
                        except Exception:
                            cursor.execute(
                                """INSERT INTO market_rates (date, category, count_size, price_per_kg, price_change, location, species, source) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                                   ON DUPLICATE KEY UPDATE price_per_kg=%s, price_change=%s""",
                                (cur_date, 'Shrimp', count_val, price, change, loc, 'Vannamei', 'AquaGuru Market Feed', price, change)
                            )
                
                # Fish Rates
                for f_spec, f_count, f_base_price in fish_species_data:
                    for loc in locations:
                        loc_adj = 0.0 if loc == 'Andhra Pradesh' else (3.0 if loc == 'Bhimavaram' else (-2.0 if loc == 'Kakinada' else 0.0))
                        price = round(f_base_price + loc_adj, 1)
                        change = 0.0
                        try:
                            cursor.execute(
                                """INSERT OR REPLACE INTO market_rates (date, category, count_size, price_per_kg, price_change, location, species, source) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                (cur_date, 'Fish', f_count, price, change, loc, f_spec, 'AquaGuru Fish Market Index')
                            )
                        except Exception:
                            cursor.execute(
                                """INSERT INTO market_rates (date, category, count_size, price_per_kg, price_change, location, species, source) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                   ON DUPLICATE KEY UPDATE price_per_kg=%s, price_change=%s""",
                                (cur_date, 'Fish', f_count, price, change, loc, f_spec, 'AquaGuru Fish Market Index', price, change)
                            )

        conn.commit()
        print(f"[DB SUCCESS] Database initialized successfully using {get_active_engine().upper()} engine!")
        return True

    except Exception as e:
        print(f"[DB ERROR] Error initializing database tables: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
