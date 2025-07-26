"""
Instagram Accounts Management Module
Handles CRUD operations for Instagram accounts storage and retrieval
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccountsManager:
    def __init__(self):
        self.accounts_file = ACCOUNTS_FILE
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Ensure instagram_accounts.json exists"""
        if not os.path.exists(self.accounts_file):
            with open(self.accounts_file, 'w') as f:
                json.dump([], f)
    
    def load_accounts(self) -> List[Dict]:
        """Load all Instagram accounts"""
        try:
            with open(self.accounts_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_accounts(self, accounts: List[Dict]) -> bool:
        """Save accounts to file"""
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(accounts, f, indent=2)
            return True
        except Exception:
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all Instagram accounts"""
        return self.load_accounts()
    
    def get_active_accounts(self) -> List[Dict]:
        """Get only active Instagram accounts"""
        accounts = self.load_accounts()
        return [acc for acc in accounts if acc.get('is_active', True)]
    
    def add_account(self, username: str, password: str, email: str = '', 
                   phone: str = '', notes: str = '') -> Dict:
        """Add a new Instagram account"""
        accounts = self.load_accounts()
        
        # Check if username already exists
        if any(acc['username'].lower() == username.lower() for acc in accounts):
            raise ValueError(f"Account with username '{username}' already exists")
        
        new_account = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': password,
            'email': email,
            'phone': phone,
            'notes': notes,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        accounts.append(new_account)
        
        if self.save_accounts(accounts):
            return new_account
        else:
            raise Exception("Failed to save account")
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """Update an existing Instagram account"""
        accounts = self.load_accounts()
        
        for i, account in enumerate(accounts):
            if account['id'] == account_id:
                # Update fields
                if 'username' in updates:
                    # Check if new username already exists in other accounts
                    if any(acc['username'].lower() == updates['username'].lower() 
                          and acc['id'] != account_id for acc in accounts):
                        raise ValueError(f"Account with username '{updates['username']}' already exists")
                    account['username'] = updates['username']
                
                if 'password' in updates:
                    account['password'] = updates['password']
                if 'email' in updates:
                    account['email'] = updates['email']
                if 'phone' in updates:
                    account['phone'] = updates['phone']
                if 'notes' in updates:
                    account['notes'] = updates['notes']
                if 'is_active' in updates:
                    account['is_active'] = updates['is_active']
                
                account['updated_at'] = datetime.now().isoformat()
                accounts[i] = account
                
                return self.save_accounts(accounts)
        
        return False
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an Instagram account"""
        accounts = self.load_accounts()
        accounts = [acc for acc in accounts if acc['id'] != account_id]
        return self.save_accounts(accounts)
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID"""
        accounts = self.load_accounts()
        return next((acc for acc in accounts if acc['id'] == account_id), None)
    
    def get_accounts_by_ids(self, account_ids: List[str]) -> List[Dict]:
        """Get multiple accounts by their IDs"""
        accounts = self.load_accounts()
        return [acc for acc in accounts if acc['id'] in account_ids and acc.get('is_active', True)]
    
    def update_last_used(self, account_id: str) -> bool:
        """Update the last_used timestamp for an account"""
        return self.update_account(account_id, {'last_used': datetime.now().isoformat()})
    
    def import_accounts_from_file(self, file_path: str) -> Dict:
        """Import accounts from Excel/CSV file"""
        try:
            import pandas as pd
            
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Expected columns: username, password, email (optional), phone (optional), notes (optional)
            required_columns = ['username', 'password']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Clean and validate data
            df = df.dropna(subset=required_columns)
            
            accounts = self.load_accounts()
            existing_usernames = {acc['username'].lower() for acc in accounts}
            
            added_accounts = []
            skipped_accounts = []
            
            for _, row in df.iterrows():
                username = str(row['username']).strip()
                password = str(row['password']).strip()
                
                if not username or not password:
                    skipped_accounts.append({'username': username, 'reason': 'Empty username or password'})
                    continue
                
                if username.lower() in existing_usernames:
                    skipped_accounts.append({'username': username, 'reason': 'Username already exists'})
                    continue
                
                try:
                    new_account = {
                        'id': str(uuid.uuid4()),
                        'username': username,
                        'password': password,
                        'email': str(row.get('email', '')).strip(),
                        'phone': str(row.get('phone', '')).strip(),
                        'notes': str(row.get('notes', '')).strip(),
                        'is_active': True,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat(),
                        'last_used': None
                    }
                    
                    accounts.append(new_account)
                    added_accounts.append(new_account)
                    existing_usernames.add(username.lower())
                    
                except Exception as e:
                    skipped_accounts.append({'username': username, 'reason': str(e)})
            
            if self.save_accounts(accounts):
                return {
                    'success': True,
                    'added_count': len(added_accounts),
                    'skipped_count': len(skipped_accounts),
                    'added_accounts': added_accounts,
                    'skipped_accounts': skipped_accounts
                }
            else:
                raise Exception("Failed to save accounts")
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global instance
instagram_accounts_manager = InstagramAccountsManager()
