# firebase_db.py
"""
AquaGuru Firebase Firestore Database Client
Provides real-time cloud data synchronization and REST CRUD operations
for Google Cloud Firestore project: aquaguru-f35c0.
"""

import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import date, datetime
from decimal import Decimal
import threading

from config import Config

PROJECT_ID = Config.FIREBASE_PROJECT_ID
API_KEY = Config.FIREBASE_API_KEY
BASE_URL = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents"


def _convert_value_to_firestore(val):
    """Converts a standard Python value into Firestore REST API value format."""
    if val is None:
        return {"nullValue": None}
    elif isinstance(val, bool):
        return {"booleanValue": val}
    elif isinstance(val, int):
        return {"integerValue": str(val)}
    elif isinstance(val, (float, Decimal)):
        return {"doubleValue": float(val)}
    elif isinstance(val, (datetime, date)):
        if isinstance(val, datetime):
            iso_str = val.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            iso_str = f"{val.strftime('%Y-%m-%d')}T00:00:00Z"
        return {"timestampValue": iso_str}
    elif isinstance(val, dict):
        fields = {k: _convert_value_to_firestore(v) for k, v in val.items()}
        return {"mapValue": {"fields": fields}}
    elif isinstance(val, (list, tuple)):
        values = [_convert_value_to_firestore(v) for v in val]
        return {"arrayValue": {"values": values}}
    else:
        return {"stringValue": str(val)}


def _convert_firestore_to_value(field_dict):
    """Converts a Firestore REST API field dictionary back to a Python value."""
    if not isinstance(field_dict, dict):
        return field_dict
    
    if "nullValue" in field_dict:
        return None
    elif "booleanValue" in field_dict:
        return field_dict["booleanValue"]
    elif "integerValue" in field_dict:
        try:
            return int(field_dict["integerValue"])
        except Exception:
            return field_dict["integerValue"]
    elif "doubleValue" in field_dict:
        return float(field_dict["doubleValue"])
    elif "stringValue" in field_dict:
        return field_dict["stringValue"]
    elif "timestampValue" in field_dict:
        return field_dict["timestampValue"]
    elif "mapValue" in field_dict:
        fields = field_dict.get("mapValue", {}).get("fields", {})
        return {k: _convert_firestore_to_value(v) for k, v in fields.items()}
    elif "arrayValue" in field_dict:
        values = field_dict.get("arrayValue", {}).get("values", [])
        return [_convert_firestore_to_value(v) for v in values]
    return field_dict


def dict_to_firestore_fields(data):
    """Converts a flat Python dictionary into Firestore fields representation."""
    fields = {}
    for k, v in data.items():
        fields[k] = _convert_value_to_firestore(v)
    return {"fields": fields}


def firestore_doc_to_dict(doc):
    """Parses a Firestore REST document into a clean Python dictionary."""
    if not doc or not isinstance(doc, dict):
        return {}
    
    doc_name = doc.get("name", "")
    doc_id = doc_name.split("/")[-1] if doc_name else ""
    fields = doc.get("fields", {})
    
    result = {"_firestore_id": doc_id}
    for k, v in fields.items():
        result[k] = _convert_firestore_to_value(v)
    return result


class FirestoreClient:
    """Synchronous REST client for Google Cloud Firestore with zero external heavy dependencies."""

    @staticmethod
    def _send_request(url, method="GET", payload=None):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AquaGuru-Cloud/1.0"
        }
        
        data_bytes = None
        if payload is not None:
            data_bytes = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_text = resp.read().decode("utf-8")
                return json.loads(resp_text) if resp_text else {}
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            return {"error": True, "code": e.code, "message": str(e), "details": err_body}
        except Exception as ex:
            return {"error": True, "message": str(ex)}

    @classmethod
    def test_connection(cls):
        """Tests live connectivity to Google Firestore aquaguru-f35c0."""
        # Query the ponds collection endpoint
        url = f"{BASE_URL}/ponds?key={API_KEY}&pageSize=1"
        res = cls._send_request(url, method="GET")
        if isinstance(res, dict) and res.get("error"):
            # If 404 on collection listing, it means collection is empty, which is valid connected state!
            if res.get("code") in (404, 403):
                # Test write a ping document
                ping_res = cls.save_document("_ping", {"status": "connected", "timestamp": datetime.now()}, doc_id="ping_test")
                if not (isinstance(ping_res, dict) and ping_res.get("error")):
                    return True, "Connected to Google Cloud Firestore (aquaguru-f35c0)"
            return False, res.get("message", "Unknown error")
        return True, "Connected to Google Cloud Firestore (aquaguru-f35c0)"

    @classmethod
    def save_document(cls, collection, data, doc_id=None):
        """Creates or overwrites a document in the specified Firestore collection."""
        payload = dict_to_firestore_fields(data)
        
        if doc_id:
            # Patch / write specific document ID
            url = f"{BASE_URL}/{collection}/{doc_id}?key={API_KEY}"
            return cls._send_request(url, method="PATCH", payload=payload)
        else:
            # Create document with auto ID
            url = f"{BASE_URL}/{collection}?key={API_KEY}"
            return cls._send_request(url, method="POST", payload=payload)

    @classmethod
    def get_documents(cls, collection, page_size=100):
        """Retrieves documents from a collection."""
        url = f"{BASE_URL}/{collection}?key={API_KEY}&pageSize={page_size}"
        res = cls._send_request(url, method="GET")
        if not res or res.get("error"):
            return []
        
        docs = res.get("documents", [])
        return [firestore_doc_to_dict(d) for d in docs]

    @classmethod
    def get_document(cls, collection, doc_id):
        """Retrieves a single document by ID."""
        url = f"{BASE_URL}/{collection}/{doc_id}?key={API_KEY}"
        res = cls._send_request(url, method="GET")
        if not res or res.get("error"):
            return None
        return firestore_doc_to_dict(res)

    @classmethod
    def delete_document(cls, collection, doc_id):
        """Deletes a document from Firestore."""
        url = f"{BASE_URL}/{collection}/{doc_id}?key={API_KEY}"
        return cls._send_request(url, method="DELETE")

    @classmethod
    def async_save_document(cls, collection, data, doc_id=None):
        """Non-blocking background save to Firestore."""
        def _task():
            try:
                cls.save_document(collection, data, doc_id=doc_id)
            except Exception as e:
                print(f"[FIREBASE ASYNC ERROR] {collection}/{doc_id}: {e}")
        
        t = threading.Thread(target=_task, daemon=True)
        t.start()


def sync_database_to_firestore():
    """Reads all existing records from local DB and syncs them into Firestore collections."""
    from db import get_db_connection, serialize_rows
    
    conn = get_db_connection()
    if not conn:
        return {"success": False, "error": "Database connection failed"}
    
    collections_to_sync = [
        ("ponds", "SELECT * FROM ponds"),
        ("feed_records", "SELECT * FROM feed_records"),
        ("water_quality", "SELECT * FROM water_quality"),
        ("growth_records", "SELECT * FROM growth_records"),
        ("expenses", "SELECT * FROM expenses"),
        ("inventory", "SELECT * FROM inventory"),
        ("harvest", "SELECT * FROM harvest"),
        ("notifications", "SELECT * FROM notifications")
    ]
    
    synced_counts = {}
    
    try:
        cur = conn.cursor(dictionary=True) if hasattr(conn, 'cursor') else conn.cursor()
        for col_name, sql in collections_to_sync:
            try:
                cur.execute(sql)
                rows = serialize_rows(cur.fetchall())
                for r in rows:
                    doc_id = str(r.get("id")) if "id" in r else None
                    FirestoreClient.save_document(col_name, r, doc_id=doc_id)
                synced_counts[col_name] = len(rows)
            except Exception as ex:
                synced_counts[col_name] = f"Notice: {ex}"
        
        cur.close()
        conn.close()
        return {"success": True, "synced_counts": synced_counts}
    except Exception as e:
        if conn:
            conn.close()
        return {"success": False, "error": str(e)}
