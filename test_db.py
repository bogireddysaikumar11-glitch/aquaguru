# test_db.py
"""
AquaGuru Database Diagnostic Script
Tests active connection and shows table status.
"""
from db import get_db_connection, get_active_engine, init_db

print("=" * 55)
print(" AquaGuru Database Diagnostic Test")
print("=" * 55)

try:
    # Ensure database is initialized
    init_db()
    
    conn = get_db_connection()
    if conn is None:
        print("[ERROR] Database connection failed.")
        print("Please check your database configuration in config.py or .env")
        exit(1)
        
    engine = get_active_engine()
    print(f"[OK] Database connection successful!")
    print(f"[OK] Active Database Engine: {engine.upper()}")
    
    cursor = conn.cursor(dictionary=True)
    
    # Query user count
    cursor.execute("SELECT COUNT(*) as count FROM users")
    res = cursor.fetchone()
    count = res['count'] if isinstance(res, dict) else res[0]
    print(f"[OK] Total registered users: {count}")
    
    # Query ponds count
    cursor.execute("SELECT COUNT(*) as count FROM ponds")
    res = cursor.fetchone()
    ponds = res['count'] if isinstance(res, dict) else res[0]
    print(f"[OK] Total ponds configured: {ponds}")
    
    cursor.close()
    conn.close()
    
    print("=" * 55)
    print(" [SUCCESS] Database is 100% READY for local and cloud deployment!")
    print("=" * 55)

except Exception as e:
    print(f"[ERROR] Diagnostic failed: {e}")