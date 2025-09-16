#!/usr/bin/env python3
"""
Initialize SQLite database with required tables
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from app.sqlite_database import SQLiteDatabase

def init_database():
    """Initialize the database with all required tables"""
    print("🗄️ Initializing SQLite database...")
    
    db = SQLiteDatabase("meeting_minutes.db")
    print("✅ Database initialized successfully!")
    
    # Test the database
    import sqlite3
    with sqlite3.connect("meeting_minutes.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
    print(f"📋 Created tables: {[table[0] for table in tables]}")
    return True

if __name__ == "__main__":
    init_database()