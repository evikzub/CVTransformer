"""
User model and database operations for CV Converter Web Application
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class User:
    """User data model representing a user in the system"""
    id: Optional[int] = None
    redmine_user_id: Optional[int] = None
    username: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    role: str = "user"  # "admin" or "user"
    last_login: Optional[datetime] = None
    conversion_count: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'redmine_user_id': self.redmine_user_id,
            'username': self.username,
            'custom_fields': self.custom_fields,
            'role': self.role,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'conversion_count': self.conversion_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserManager:
    """Database manager for user operations"""
    
    def __init__(self, db_path: str):
        """Initialize user manager with database path"""
        self.db_path = db_path
        self.ensure_database_exists()
        self.create_tables()

    def ensure_database_exists(self):
        """Ensure the database directory and file exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_tables(self):
        """Create the users table according to the requirements schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    redmine_user_id INTEGER UNIQUE,
                    username TEXT,
                    custom_fields TEXT, -- JSON string of Redmine custom fields
                    role TEXT CHECK(role IN ('admin', 'user')) DEFAULT 'user',
                    last_login TIMESTAMP,
                    conversion_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def create_user(self, redmine_user_id: int, username: str, 
                   custom_fields: Optional[Dict[str, Any]] = None) -> User:
        """Create a new user in the database"""
        # Check if this is the first user (auto-admin logic)
        is_first_user = self.get_user_count() == 0
        role = "admin" if is_first_user else "user"
        
        with self.get_connection() as conn:
            cursor = conn.execute('''
                INSERT INTO users (redmine_user_id, username, custom_fields, role, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                redmine_user_id,
                username,
                json.dumps(custom_fields) if custom_fields else None,
                role,
                datetime.now()
            ))
            
            user_id = cursor.lastrowid
            conn.commit()
            
        return self.get_user_by_id(user_id)

    def get_user_by_redmine_id(self, redmine_user_id: int) -> Optional[User]:
        """Get user by Redmine user ID"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM users WHERE redmine_user_id = ?
            ''', (redmine_user_id,)).fetchone()
            
            if row:
                return self._row_to_user(row)
            return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal ID"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM users WHERE id = ?
            ''', (user_id,)).fetchone()
            
            if row:
                return self._row_to_user(row)
            return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        with self.get_connection() as conn:
            row = conn.execute('''
                SELECT * FROM users WHERE username = ?
            ''', (username,)).fetchone()
            
            if row:
                return self._row_to_user(row)
            return None

    def update_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now(), user_id))
            conn.commit()
            return cursor.rowcount > 0

    def increment_conversion_count(self, user_id: int) -> bool:
        """Increment user's conversion count"""
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE users SET conversion_count = conversion_count + 1 WHERE id = ?
            ''', (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update user's role (admin only operation)"""
        if new_role not in ['admin', 'user']:
            return False
            
        with self.get_connection() as conn:
            cursor = conn.execute('''
                UPDATE users SET role = ? WHERE id = ?
            ''', (new_role, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        with self.get_connection() as conn:
            rows = conn.execute('''
                SELECT * FROM users ORDER BY created_at DESC
            ''').fetchall()
            
            return [self._row_to_user(row) for row in rows]

    def get_user_count(self) -> int:
        """Get total number of users"""
        with self.get_connection() as conn:
            result = conn.execute('SELECT COUNT(*) FROM users').fetchone()
            return result[0]

    def _row_to_user(self, row: sqlite3.Row) -> User:
        """Convert database row to User object"""
        return User(
            id=row['id'],
            redmine_user_id=row['redmine_user_id'],
            username=row['username'],
            custom_fields=json.loads(row['custom_fields']) if row['custom_fields'] else None,
            role=row['role'],
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            conversion_count=row['conversion_count'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    def delete_user(self, user_id: int) -> bool:
        """Delete a user (admin only operation)"""
        with self.get_connection() as conn:
            cursor = conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            return cursor.rowcount > 0 