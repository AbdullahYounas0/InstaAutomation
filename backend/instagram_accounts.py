"""
Instagram Accounts Management Module
Handles CRUD operations for Instagram accounts storage and retrieval
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configure logging for Instagram Accounts Management
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/instagram_accounts.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('InstagramAccounts')

ACCOUNTS_FILE = 'instagram_accounts.json'

class InstagramAccountsManager:
    def __init__(self):
        self.accounts_file = ACCOUNTS_FILE
        logger.info("InstagramAccountsManager initialized")
        self.ensure_file_exists()
    
    def ensure_file_exists(self):
        """Ensure instagram_accounts.json exists"""
        if not os.path.exists(self.accounts_file):
            logger.info(f"Creating new accounts file: {self.accounts_file}")
            try:
                with open(self.accounts_file, 'w') as f:
                    json.dump([], f)
                logger.info("Successfully created accounts file")
            except Exception as e:
                logger.error(f"Error creating accounts file: {str(e)}")
                raise
        else:
            logger.debug(f"Accounts file already exists: {self.accounts_file}")
    
    def load_accounts(self) -> List[Dict]:
        """Load all Instagram accounts"""
        logger.debug("Loading accounts from file")
        try:
            with open(self.accounts_file, 'r') as f:
                accounts = json.load(f)
            logger.info(f"Successfully loaded {len(accounts)} accounts")
            return accounts
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading accounts: {str(e)}")
            return []
    
    def save_accounts(self, accounts: List[Dict]) -> bool:
        """Save accounts to file"""
        logger.debug(f"Saving {len(accounts)} accounts to file")
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(accounts, f, indent=2)
            logger.info(f"Successfully saved {len(accounts)} accounts")
            return True
        except Exception as e:
            logger.error(f"Error saving accounts: {str(e)}")
            return False
    
    def get_all_accounts(self) -> List[Dict]:
        """Get all Instagram accounts"""
        logger.debug("Getting all accounts")
        accounts = self.load_accounts()
        logger.info(f"Retrieved {len(accounts)} total accounts")
        return accounts
    
    def get_active_accounts(self) -> List[Dict]:
        """Get only active Instagram accounts"""
        logger.debug("Getting active accounts")
        accounts = self.load_accounts()
        active_accounts = [acc for acc in accounts if acc.get('is_active', True)]
        logger.info(f"Retrieved {len(active_accounts)} active accounts out of {len(accounts)} total")
        return active_accounts
    
    def add_account(self, username: str, password: str, email: str = '', 
                   phone: str = '', notes: str = '') -> Dict:
        """Add a new Instagram account"""
        logger.info(f"Adding new account: {username}")
        accounts = self.load_accounts()
        
        # Check if username already exists
        existing_account = any(acc['username'].lower() == username.lower() for acc in accounts)
        if existing_account:
            logger.warning(f"Account with username '{username}' already exists")
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
            logger.info(f"Successfully added account: {username}")
            return new_account
        else:
            logger.error(f"Failed to save account: {username}")
            raise Exception("Failed to save account")
    
    def update_account(self, account_id: str, updates: Dict) -> bool:
        """Update an existing Instagram account"""
        logger.info(f"Updating account with ID: {account_id}")
        accounts = self.load_accounts()
        
        for i, account in enumerate(accounts):
            if account['id'] == account_id:
                # Update fields
                if 'username' in updates:
                    # Check if new username already exists in other accounts
                    existing_username = any(acc['username'].lower() == updates['username'].lower() 
                          and acc['id'] != account_id for acc in accounts)
                    if existing_username:
                        logger.warning(f"Username '{updates['username']}' already exists for another account")
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
                
                success = self.save_accounts(accounts)
                if success:
                    logger.info(f"Successfully updated account: {account.get('username', account_id)}")
                else:
                    logger.error(f"Failed to save updated account: {account_id}")
                return success
        
        logger.warning(f"Account not found for update: {account_id}")
        return False
    
    def delete_account(self, account_id: str) -> bool:
        """Delete an Instagram account"""
        logger.info(f"Deleting account with ID: {account_id}")
        accounts = self.load_accounts()
        original_count = len(accounts)
        accounts = [acc for acc in accounts if acc['id'] != account_id]
        
        if len(accounts) < original_count:
            success = self.save_accounts(accounts)
            if success:
                logger.info(f"Successfully deleted account: {account_id}")
            else:
                logger.error(f"Failed to save after deleting account: {account_id}")
            return success
        else:
            logger.warning(f"Account not found for deletion: {account_id}")
            return False
    
    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """Get account by ID"""
        logger.debug(f"Getting account by ID: {account_id}")
        accounts = self.load_accounts()
        account = next((acc for acc in accounts if acc['id'] == account_id), None)
        if account:
            logger.debug(f"Found account: {account.get('username')}")
        else:
            logger.debug(f"Account not found: {account_id}")
        return account
    
    def get_accounts_by_ids(self, account_ids: List[str]) -> List[Dict]:
        """Get multiple accounts by their IDs"""
        logger.debug(f"Getting {len(account_ids)} accounts by IDs")
        accounts = self.load_accounts()
        matching_accounts = [acc for acc in accounts if acc['id'] in account_ids and acc.get('is_active', True)]
        logger.info(f"Found {len(matching_accounts)} matching active accounts")
        return matching_accounts
    
    def update_last_used(self, account_id: str) -> bool:
        """Update the last_used timestamp for an account"""
        logger.debug(f"Updating last_used for account: {account_id}")
        return self.update_account(account_id, {'last_used': datetime.now().isoformat()})
    
    def import_accounts_from_file(self, file_path: str) -> Dict:
        """Import accounts from Excel/CSV file"""
        logger.info(f"Importing accounts from file: {file_path}")
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
logger.info("Instagram accounts manager instance created and ready")
