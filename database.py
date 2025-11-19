import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        """إنشاء الجداول اللازمة إذا لم تكن موجودة"""
        try:
            # جدول المستخدمين
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # جدول الطلبات النشطة
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS active_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stars_count INTEGER,
                ton_amount REAL,
                wallet_address TEXT,
                payment_charge_id TEXT,
                status TEXT DEFAULT 'pending',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')
            
            # جدول المعاملات المكتملة
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS completed_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tx_hash TEXT UNIQUE,
                stars_count INTEGER,
                ton_amount REAL,
                wallet_address TEXT,
                payment_charge_id TEXT,
                status TEXT DEFAULT 'completed',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )''')
            
            # جدول حالات المستخدمين
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_states (
                user_id INTEGER PRIMARY KEY,
                state TEXT,
                state_data TEXT,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            self.connection.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")

    def add_user(self, user_id, username, full_name):
        """إضافة مستخدم جديد إذا لم يكن موجودًا"""
        try:
            self.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                              (user_id, username or "", full_name or ""))
            self.connection.commit()
            logger.info(f"User {user_id} added/updated successfully")
        except Exception as e:
            logger.error(f"Error adding user {user_id}: {e}")

    def set_user_state(self, user_id, state, state_data=None):
        """حفظ حالة المستخدم"""
        try:
            import json
            data_str = json.dumps(state_data) if state_data else None
            self.cursor.execute("INSERT OR REPLACE INTO user_states (user_id, state, state_data) VALUES (?, ?, ?)", 
                              (user_id, state, data_str))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error setting user state for {user_id}: {e}")

    def get_user_state(self, user_id):
        """جلب حالة المستخدم"""
        try:
            import json
            self.cursor.execute("SELECT state, state_data FROM user_states WHERE user_id = ?", (user_id,))
            result = self.cursor.fetchone()
            if result:
                state, state_data = result
                data_obj = json.loads(state_data) if state_data else None
                return state, data_obj
            return None, None
        except Exception as e:
            logger.error(f"Error getting user state for {user_id}: {e}")
            return None, None

    def clear_user_state(self, user_id):
        """مسح حالة المستخدم"""
        try:
            self.cursor.execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Error clearing user state for {user_id}: {e}")

    def create_order(self, user_id, stars_count, ton_amount, wallet_address, payment_charge_id=None):
        """إنشاء طلب بيع جديد"""
        try:
            # حذف أي طلبات قديمة لنفس المستخدم
            self.cursor.execute("DELETE FROM active_orders WHERE user_id = ?", (user_id,))
            
            # إضافة الطلب الجديد
            self.cursor.execute('''INSERT INTO active_orders 
                                (user_id, stars_count, ton_amount, wallet_address, payment_charge_id) 
                                VALUES (?, ?, ?, ?, ?)''',
                              (user_id, stars_count, ton_amount, wallet_address, payment_charge_id))
            self.connection.commit()
            logger.info(f"Order created for user {user_id}: {stars_count} stars")
            return True
        except Exception as e:
            logger.error(f"Error creating order for user {user_id}: {e}")
            return False

    def get_order(self, user_id):
        """جلب تفاصيل الطلب النشط للمستخدم"""
        try:
            self.cursor.execute('''SELECT stars_count, ton_amount, wallet_address, payment_charge_id 
                                FROM active_orders WHERE user_id = ?''', (user_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting order for user {user_id}: {e}")
            return None

    def complete_order(self, user_id, tx_hash):
        """إكمال الطلب وإضافته لسجل المعاملات"""
        try:
            order = self.get_order(user_id)
            if order:
                stars_count, ton_amount, wallet_address, payment_charge_id = order
                
                # نقل الطلب لجدول المعاملات المكتملة
                self.cursor.execute('''INSERT INTO completed_transactions 
                                    (user_id, tx_hash, stars_count, ton_amount, wallet_address, payment_charge_id) 
                                    VALUES (?, ?, ?, ?, ?, ?)''',
                                  (user_id, tx_hash, stars_count, ton_amount, wallet_address, payment_charge_id))
                
                # حذف الطلب من الجدول النشط
                self.cursor.execute("DELETE FROM active_orders WHERE user_id = ?", (user_id,))
                self.connection.commit()
                logger.info(f"Order completed for user {user_id}, tx_hash: {tx_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error completing order for user {user_id}: {e}")
            return False

    def get_user_transactions(self, user_id, limit=10):
        """جلب معاملات المستخدم"""
        try:
            self.cursor.execute('''SELECT tx_hash, stars_count, ton_amount, wallet_address, created, status 
                                FROM completed_transactions 
                                WHERE user_id = ? 
                                ORDER BY created DESC 
                                LIMIT ?''', (user_id, limit))
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting transactions for user {user_id}: {e}")
            return []

# إنشاء كائن قاعدة البيانات
import config
db = Database(config.DATABASE_FILE)