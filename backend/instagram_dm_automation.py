import os
import sys
import csv
import json
import random
import threading
import asyncio
import logging
import pandas as pd
import chardet
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from openai import OpenAI
import time

# Configuration constants
INSTAGRAM_URL = "https://www.instagram.com/"
MAX_PARALLEL_ACCOUNTS = 10

# Proxy list
PROXIES = [
    "156.237.58.177:8075:silwfmmt:9mnui1h717nw",
    "72.1.138.220:6111:silwfmmt:9mnui1h717nw",
    "136.143.251.205:7404:silwfmmt:9mnui1h717nw",
    "163.123.200.142:6427:silwfmmt:9mnui1h717nw",
    "208.66.73.58:5069:silwfmmt:9mnui1h717nw",
    "46.203.3.115:8114:silwfmmt:9mnui1h717nw",
    "66.43.6.242:8113:silwfmmt:9mnui1h717nw",
    "69.30.75.24:6081:silwfmmt:9mnui1h717nw",
    "72.1.156.235:8125:silwfmmt:9mnui1h717nw",
    "156.237.54.82:7977:silwfmmt:9mnui1h717nw",
    "45.56.157.181:6404:silwfmmt:9mnui1h717nw",
    "192.53.68.50:5108:silwfmmt:9mnui1h717nw",
    "208.72.211.251:7036:silwfmmt:9mnui1h717nw",
    "207.228.28.217:7866:silwfmmt:9mnui1h717nw",
    "156.237.42.124:8023:silwfmmt:9mnui1h717nw",
    "46.203.104.5:7502:silwfmmt:9mnui1h717nw",
    "154.194.25.13:5031:silwfmmt:9mnui1h717nw",
    "207.228.32.142:6759:silwfmmt:9mnui1h717nw",
    "46.203.54.224:8222:silwfmmt:9mnui1h717nw",
    "207.228.14.23:5315:silwfmmt:9mnui1h717nw"
]

# Global locks and variables
csv_lock = threading.Lock()
proxy_lock = threading.Lock()
used_proxies = set()

class DMAutomationEngine:
    def __init__(self, log_callback=None, stop_callback=None, visual_mode=False):
        self.log_callback = log_callback or print
        self.stop_callback = stop_callback or (lambda: False)
        self.visual_mode = visual_mode  # Whether to show browsers
        self.client = None
        self.sent_dms = []
        self.positive_responses = []
        
    def log(self, message, level="INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}"
        self.log_callback(formatted_message, level)

    async def update_visual_status(self, page, status_text, account_number, step=None):
        """Update visual status banner if in visual mode"""
        if self.visual_mode:
            try:
                step_text = f" - Step {step}" if step else ""
                # Choose color based on status
                if "✅" in status_text or "successful" in status_text.lower() or "completed" in status_text.lower():
                    color = '#28a745, #20c997'  # Green gradient
                elif "❌" in status_text or "error" in status_text.lower() or "failed" in status_text.lower():
                    color = '#dc3545, #fd7e14'  # Red gradient  
                elif "sending" in status_text.lower() or "processing" in status_text.lower():
                    color = '#007bff, #6f42c1'  # Blue gradient
                else:
                    color = '#4ecdc4, #45b7aa'  # Default teal gradient
                    
                await page.evaluate(f'''
                    const banner = document.querySelector('#automation-status-banner');
                    if (banner) {{
                        banner.textContent = 'Account {account_number}: {status_text}{step_text}';
                        banner.style.background = 'linear-gradient(90deg, {color})';
                    }}
                ''')
            except:
                pass  # Ignore errors in visual updates
        
    def setup_openai_client(self):
        """Setup OpenAI client for DeepSeek API"""
        try:
            # Always use the default API key
            deepseek_key = 'sk-0307c2f76e434a19aaef94e76c017fca'
            self.log("Using default DeepSeek API key for AI-powered message generation")
            
            self.client = OpenAI(
                api_key=deepseek_key,
                base_url="https://api.deepseek.com"
            )
            self.log("DeepSeek AI client initialized successfully")
            return True
        except Exception as e:
            self.log(f"Failed to initialize AI client: {e}", "ERROR")
            return False
    
    def get_available_proxy(self):
        """Get an available proxy that hasn't been used yet"""
        with proxy_lock:
            available_proxies = [p for p in PROXIES if p not in used_proxies]
            if available_proxies:
                proxy = random.choice(available_proxies)
                used_proxies.add(proxy)
                return proxy
            return None
    
    def release_proxy(self, proxy):
        """Release a proxy back to the pool"""
        with proxy_lock:
            used_proxies.discard(proxy)
    
    def parse_proxy(self, proxy_string):
        """Parse proxy string into components"""
        parts = proxy_string.split(':')
        if len(parts) == 4:
            return {
                'server': f'http://{parts[0]}:{parts[1]}',
                'username': parts[2],
                'password': parts[3]
            }
        return None
    
    async def setup_browser(self, proxy_string=None, account_number=1):
        """Set up browser with optimized settings and proxy support"""
        try:
            playwright = await async_playwright().start()
            
            # Parse proxy if provided
            proxy_config = None
            if proxy_string:
                proxy_parts = self.parse_proxy(proxy_string)
                if proxy_parts:
                    proxy_config = {
                        'server': proxy_parts['server'],
                        'username': proxy_parts['username'],
                        'password': proxy_parts['password']
                    }
                    self.log(f"Using proxy: {proxy_parts['server']}")
            
            # Randomize viewport and user agent
            viewports = [
                {"width": 1366, "height": 768},
                {"width": 1920, "height": 1080},
                {"width": 1536, "height": 864},
                {"width": 1440, "height": 900},
                {"width": 1280, "height": 720}
            ]
            viewport = random.choice(viewports)
            
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
            ]
            user_agent = random.choice(user_agents)
            
            # Configure browser launch args based on visual mode
            browser_args = [
                "--no-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
            
            # Configure window positioning and size for visual mode
            if self.visual_mode:
                # Calculate browser window position in grid
                # Grid layout: 3 columns, rows as needed
                cols = 3
                window_width = 500
                window_height = 650
                col = (account_number - 1) % cols
                row = (account_number - 1) // cols
                x_position = col * (window_width + 15)  # 15px gap
                y_position = row * (window_height + 60) + 50  # 60px gap + 50px from top
                
                browser_args.extend([
                    f'--window-position={x_position},{y_position}',
                    f'--window-size={window_width},{window_height}',
                    '--disable-infobars',
                    '--disable-extensions',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-popup-blocking'
                ])
                
                viewport = {"width": window_width - 16, "height": window_height - 120}
                
                self.log(f"[Account {account_number}] Browser window positioned at ({x_position}, {y_position}) - Grid position: Col {col+1}, Row {row+1}")
            
            # Launch browser with stealth mode
            browser = await playwright.chromium.launch(
                headless=not self.visual_mode,  # Show browsers only in visual mode
                proxy=proxy_config,
                args=browser_args
            )
            
            context = await browser.new_context(
                user_agent=user_agent,
                viewport=viewport,
                java_script_enabled=True,
                locale='en-US',
                timezone_id='America/New_York'
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                window.chrome = {
                    runtime: {}
                };
            """)
            
            # Add visual status banner in visual mode
            if self.visual_mode:
                await context.add_init_script(f"""
                    // Wait for DOM to be ready
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', function() {{
                            addStatusBanner({account_number});
                        }});
                    }} else {{
                        addStatusBanner({account_number});
                    }}
                    
                    function addStatusBanner(accountNum) {{
                        setTimeout(() => {{
                            if (document.body && !document.querySelector('#automation-status-banner')) {{
                                const banner = document.createElement('div');
                                banner.id = 'automation-status-banner';
                                banner.style.cssText = `
                                    position: fixed;
                                    top: 0;
                                    left: 0;
                                    width: 100%;
                                    height: 30px;
                                    background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
                                    color: white;
                                    text-align: center;
                                    line-height: 30px;
                                    font-weight: bold;
                                    z-index: 10000;
                                    font-size: 12px;
                                `;
                                banner.textContent = `Account ${{accountNum}}: Initializing DM automation...`;
                                document.body.prepend(banner);
                            }}
                        }}, 1000);
                    }}
                """)
            
            context.set_default_timeout(120000)  # 2 minutes
            context.set_default_navigation_timeout(120000)
            
            return playwright, browser, context
        
        except Exception as e:
            self.log(f"Browser setup failed: {e}", "ERROR")
            raise
    
    def load_accounts(self, accounts_file):
        """Load bot accounts from file"""
        try:
            if accounts_file.endswith('.csv'):
                accounts_df = pd.read_csv(accounts_file)
            else:
                accounts_df = pd.read_excel(accounts_file)
            
            # Standardize column names
            accounts_df.columns = accounts_df.columns.str.strip().str.title()
            
            if 'Username' not in accounts_df.columns or 'Password' not in accounts_df.columns:
                raise ValueError("Accounts file must contain 'Username' and 'Password' columns")
            
            accounts = []
            for _, row in accounts_df.iterrows():
                if pd.notna(row['Username']) and pd.notna(row['Password']):
                    accounts.append({
                        'username': str(row['Username']).strip(),
                        'password': str(row['Password']).strip()
                    })
            
            self.log(f"Loaded {len(accounts)} bot accounts")
            return accounts
            
        except Exception as e:
            self.log(f"Error loading accounts: {e}", "ERROR")
            raise
    
    def load_target_users(self, target_file=None):
        """Load target users from file or return default list"""
        if not target_file:
            # Return default target users if no file provided
            default_targets = [
                {'username': 'test_user1', 'first_name': 'John', 'city': 'New York', 'bio': 'entrepreneur'},
                {'username': 'test_user2', 'first_name': 'Sarah', 'city': 'Los Angeles', 'bio': 'marketing'},
                {'username': 'test_user3', 'first_name': 'Mike', 'city': 'Chicago', 'bio': 'business owner'},
            ]
            self.log("Using default target users (no target file provided)")
            return default_targets
        
        try:
            # Detect encoding
            with open(target_file, 'rb') as f:
                encoding = chardet.detect(f.read())['encoding']
            
            if target_file.endswith('.csv'):
                target_df = pd.read_csv(target_file, encoding=encoding)
            else:
                target_df = pd.read_excel(target_file)
            
            target_users = target_df.to_dict('records')
            self.log(f"Loaded {len(target_users)} target users")
            return target_users
            
        except Exception as e:
            self.log(f"Error loading target users: {e}", "WARNING")
            return []
    
    def load_dm_prompt(self, prompt_file=None, custom_prompt=None):
        """Load DM prompt from file or use custom prompt"""
        if custom_prompt and custom_prompt.strip():
            self.log("Using custom DM prompt")
            return custom_prompt.strip()
        
        if prompt_file and os.path.exists(prompt_file):
            try:
                with open(prompt_file, 'r', encoding='utf-8') as file:
                    prompt = file.read().strip()
                self.log("DM prompt loaded from file")
                return prompt
            except Exception as e:
                self.log(f"Error loading prompt file: {e}", "WARNING")
        
        # Default prompt
        default_prompt = """Create a personalized Instagram DM for {first_name} in {city} who works in {bio}. 
The message should be about offering virtual assistant services to help with business tasks. 
Keep it friendly, professional, and under 500 characters. 
Mention how VA services could specifically help their type of work.
Make it feel personal and not like spam."""
        
        self.log("Using default DM prompt")
        return default_prompt
    
    def generate_message(self, user_data, prompt_template):
        """Generate personalized message using AI"""
        try:
            city = user_data.get('city', '') or "your area"
            bio = user_data.get('bio', '') or "your work"
            first_name = user_data.get('first_name', user_data.get('username', 'there'))
            
            prompt = f"{prompt_template}\nUser data: city: {city}, bio: {bio}, first_name: {first_name}"
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "Write personalized Instagram DMs. Keep under 500 characters."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            self.log(f"Message generation failed: {e}", "WARNING")
            return f"Hey {first_name}, interested in VA services to help with your business tasks? Worth a chat?"
    
    async def handle_login_info_save_dialog(self, page, username):
        """Handle the 'Save your login info?' dialog by clicking 'Not now'"""
        try:
            self.log(f"[{username}] Looking for 'Not now' button on save login info dialog...")
            
            # Multiple selectors to find the "Not now" button
            not_now_selectors = [
                'button:has-text("Not now")',
                'div[role="button"]:has-text("Not now")',
                'button:has-text("Not Now")',
                'div[role="button"]:has-text("Not Now")',
                '//button[contains(text(), "Not now")]',
                '//button[contains(text(), "Not Now")]',
                '[role="button"]:has-text("Not now")',
                '[role="button"]:has-text("Not Now")'
            ]
            
            for selector in not_now_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        self.log(f"[{username}] ✅ Clicked 'Not now' on save login info dialog")
                        await asyncio.sleep(random.uniform(1, 2))
                        return True
                except:
                    continue
            
            self.log(f"[{username}] ⚠️ Could not find 'Not now' button, continuing...")
            return False
            
        except Exception as e:
            self.log(f"[{username}] Error handling save login dialog: {e}")
            return False

    async def is_verification_required(self, page):
        """Check if the current page requires verification"""
        current_url = page.url
        verification_indicators = [
            "challenge",
            "checkpoint", 
            # "accounts/onetap" removed - this is just "Save your login info?" dialog, can be handled automatically
            "auth_platform/codeentry",
            "two_factor",
            "2fa",
            "verify",
            "security",
            "suspicious"
        ]
        
        # Check URL
        if any(indicator in current_url.lower() for indicator in verification_indicators):
            return True
            
        # Check page content for verification elements
        verification_selectors = [
            "input[name='verificationCode']",
            "input[name='security_code']", 
            "[data-testid='2fa-input']",
            "text=Enter the code",
            "text=verification code",
            "text=Two-factor authentication"
        ]
        
        for selector in verification_selectors:
            if await page.query_selector(selector):
                return True
                
        return False

    async def safe_goto(self, page, url, retries=3):
        """Safely navigate to URL with retries"""
        for attempt in range(retries):
            try:
                self.log(f"Navigating to {url} (attempt {attempt + 1})")
                
                if attempt == 0:
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                elif attempt == 1:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                else:
                    await page.goto(url, wait_until="load", timeout=60000)
                
                await asyncio.sleep(random.uniform(2, 4))
                
                if "instagram.com" in page.url:
                    return True
                else:
                    self.log(f"Unexpected URL: {page.url}", "WARNING")
                    
            except Exception as e:
                self.log(f"Navigation attempt {attempt + 1} failed: {e}", "WARNING")
                if attempt < retries - 1:
                    await asyncio.sleep(random.uniform(3, 5))
                    continue
        
        return False
    
    async def login_instagram(self, page, username, password, account_number=1):
        """Login to Instagram with improved error handling"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.log(f"[{username}] Login attempt {attempt + 1}/{max_retries}")
                
                # Add visual status update
                if self.visual_mode:
                    await self.update_visual_status(page, f"Login attempt {attempt + 1}", account_number, 2)
                
                # Navigate to Instagram
                if not await self.safe_goto(page, INSTAGRAM_URL):
                    self.log(f"[{username}] Failed to load Instagram", "ERROR")
                    if attempt < max_retries - 1:
                        continue
                    return False
                
                # Wait for page to fully load
                await asyncio.sleep(2)
                
                # Check if already logged in
                home_indicators = [
                    "nav[aria-label='Primary navigation']",
                    "[aria-label='Home']",
                    "svg[aria-label='Home']",
                    "a[href='/']"
                ]
                
                for indicator in home_indicators:
                    if await page.query_selector(indicator):
                        self.log(f"[{username}] Already logged in")
                        return True
                
                # Check for suspended account or immediate redirects
                current_url = page.url
                if any(indicator in current_url.lower() for indicator in ["suspended", "challenge", "checkpoint", "auth_platform", "verify"]):
                    self.log(f"[{username}] Account issue detected immediately: {current_url[:100]}...", "ERROR")
                    return False
                
                # Find login form with better detection
                login_form_found = False
                
                # Wait for login form to appear
                try:
                    await page.wait_for_selector("input[name='username']", timeout=10000)
                    login_form_found = True
                except:
                    # Try to navigate to login page
                    login_selectors = [
                        "a[href='/accounts/login/']",
                        "a:has-text('Log In')",
                        "a:has-text('Log in')",
                        "button:has-text('Log In')",
                        "button:has-text('Log in')"
                    ]
                    
                    for selector in login_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                await element.click()
                                await asyncio.sleep(3)
                                try:
                                    await page.wait_for_selector("input[name='username']", timeout=5000)
                                    login_form_found = True
                                    break
                                except:
                                    continue
                        except:
                            continue
                
                if not login_form_found:
                    self.log(f"[{username}] Login form not found after attempts", "ERROR")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(5)
                        continue
                    return False
                
                # Fill login form
                try:
                    # Wait for form elements to be ready
                    await asyncio.sleep(1)
                    
                    username_input = await page.query_selector("input[name='username']")
                    if username_input:
                        await username_input.click()
                        await asyncio.sleep(0.3)
                        # Clear field using keyboard shortcuts
                        await username_input.press("Control+A")
                        await username_input.press("Delete")
                        await asyncio.sleep(0.2)
                        await username_input.type(username, delay=50)
                        await asyncio.sleep(0.5)
                    else:
                        raise Exception("Username input field not found")
                    
                    password_input = await page.query_selector("input[name='password']")
                    if password_input:
                        await password_input.click()
                        await asyncio.sleep(0.3)
                        # Clear field using keyboard shortcuts
                        await password_input.press("Control+A")
                        await password_input.press("Delete")
                        await asyncio.sleep(0.2)
                        await password_input.type(password, delay=50)
                        await asyncio.sleep(0.5)
                    else:
                        raise Exception("Password input field not found")
                    
                    # Submit form with better button detection
                    submit_button_clicked = False
                    submit_selectors = [
                        "button[type='submit']",
                        "button:has-text('Log In')",
                        "button:has-text('Log in')",
                        "div[role='button']:has-text('Log In')",
                        "div[role='button']:has-text('Log in')"
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            button = await page.query_selector(selector)
                            if button:
                                await button.click()
                                submit_button_clicked = True
                                break
                        except:
                            continue
                    
                    if not submit_button_clicked:
                        # Fallback to pressing Enter
                        await password_input.press("Enter")
                    
                    # Wait for login to complete with loading indicators
                    self.log(f"[{username}] Submitting login form...")
                    await asyncio.sleep(3)
                    
                    # Wait for navigation or error messages
                    try:
                        await asyncio.sleep(5)  # Give time for login processing
                    except:
                        pass
                    
                    # Check login result with better detection
                    current_url = page.url
                    
                    # Check if we're on the "Save your login info?" page first
                    if "accounts/onetap" in current_url:
                        self.log(f"[{username}] Handling 'Save your login info?' dialog...")
                        if await self.handle_login_info_save_dialog(page, username):
                            # After handling the dialog, wait and check for success indicators
                            await asyncio.sleep(3)
                            current_url = page.url
                    
                    # First check if verification is required
                    if await self.is_verification_required(page):
                        # Log message that frontend will detect for notification
                        self.log(f"[{username}] ⚠️ Account requires verification/2FA", "WARNING")
                        self.log(f"[{username}] 🔔 Please check the account {username} and manually solve the CAPTCHA or 2FA", "WARNING")
                        self.log(f"[{username}] ⏱️ Script will pause for 5 minutes and then retry...", "INFO")
                        
                        # Wait for 5 minutes (300 seconds) before retrying
                        await asyncio.sleep(300)
                        
                        self.log(f"[{username}] 🔄 Resuming after 5-minute pause...", "INFO")
                        
                        # Check again if verification is still required
                        if await self.is_verification_required(page):
                            self.log(f"[{username}] ❌ Verification still required. Skipping this account.", "ERROR")
                            return False
                        else:
                            self.log(f"[{username}] ✅ Verification resolved. Continuing...", "SUCCESS")
                    
                    # Check for success indicators
                    success_indicators = [
                        "nav[aria-label='Primary navigation']",
                        "[aria-label='Home']",
                        "svg[aria-label='Home']",
                        "[data-testid='mobile-nav-home']"
                    ]
                    
                    for indicator in success_indicators:
                        if await page.query_selector(indicator):
                            self.log(f"[{username}] ✅ Login successful!")
                            return True
                    
                    # Check for error messages
                    error_selectors = [
                        "#slfErrorAlert",
                        "[role='alert']",
                        "p:has-text('incorrect')",
                        "div:has-text('incorrect')",
                        "div:has-text('password you entered is incorrect')",
                        "div:has-text('user not found')"
                    ]
                    
                    error_found = False
                    for selector in error_selectors:
                        if await page.query_selector(selector):
                            error_found = True
                            self.log(f"[{username}] ❌ Login credentials incorrect", "WARNING")
                            break
                    
                    if not error_found:
                        self.log(f"[{username}] ⚠️  Login status unclear, URL: {current_url[:100]}...", "WARNING")
                        # If we're still on instagram.com, might be rate limited
                        if "instagram.com" in current_url and "login" not in current_url:
                            self.log(f"[{username}] Possible rate limiting detected", "WARNING")
                        
                except Exception as e:
                    self.log(f"[{username}] Login form error: {e}", "WARNING")
                
            except Exception as e:
                self.log(f"[{username}] Login attempt {attempt + 1} failed: {e}", "ERROR")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(3, 5))
                    continue
                return False
        
        return False
    
    async def send_dm(self, page, username, message):
        """Send DM to user"""
        try:
            # Navigate to profile
            if not await self.safe_goto(page, f"{INSTAGRAM_URL}{username}/"):
                return "NAVIGATION_FAILED"
            
            # Check if profile exists
            if await page.query_selector("text=Sorry, this page isn't available."):
                return "USER_NOT_FOUND"
            
            # Wait for profile to load
            try:
                await page.wait_for_selector("header, main, article", timeout=20000)
            except:
                return "PROFILE_LOAD_TIMEOUT"
            
            # Find and click message button
            message_clicked = False
            
            selectors = [
                "button:has-text('Message')",
                "div[role='button']:has-text('Message')",
                "[aria-label='Message']",
                "a:has-text('Message')"
            ]
            
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        message_clicked = True
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            if not message_clicked:
                return "MESSAGE_BUTTON_NOT_FOUND"
            
            # Find message input
            input_selectors = [
                "div[role='textbox']",
                "div[contenteditable='true']",
                "textarea[placeholder*='Message']"
            ]
            
            message_input = None
            for selector in input_selectors:
                try:
                    message_input = await page.query_selector(selector)
                    if message_input:
                        break
                except:
                    continue
            
            if not message_input:
                return "INPUT_FIELD_ERROR"
            
            # Type and send message
            await message_input.click()
            await asyncio.sleep(0.5)
            await message_input.fill(message)
            await asyncio.sleep(random.uniform(0.5, 1))
            await message_input.press("Enter")
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            self.log(f"DM send error for {username}: {e}", "ERROR")
            return False
    
    async def check_dm_responses(self, page, account_username):
        """Check for unread messages in DM inbox (simple and fast)"""
        try:
            self.log(f"[{account_username}] Checking for unread messages...")
            
            # Navigate to direct messages
            if not await self.safe_goto(page, f"{INSTAGRAM_URL}direct/inbox/"):
                self.log(f"[{account_username}] Failed to navigate to DM inbox", "WARNING")
                return []
            
            await asyncio.sleep(3)
            
            # Wait for inbox to load
            try:
                await page.wait_for_selector("div[role='main'], div[role='grid']", timeout=15000)
            except:
                self.log(f"[{account_username}] Inbox load timeout", "WARNING")
                return []
            
            responses = []
            
            # Look for unread message indicators (Instagram shows unread conversations differently)
            unread_selectors = [
                "div[role='listitem']:has(div[class*='unread'])",  # Conversations with unread indicators
                "div[role='listitem']:has(span[class*='badge'])",   # Conversations with notification badges  
                "div[role='listitem']:has(div[style*='font-weight: bold'])", # Bold text indicates unread
                "a[href*='/direct/t/']:has(div[class*='unread'])", # Direct links with unread markers
            ]
            
            unread_conversations = []
            for selector in unread_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        unread_conversations.extend(elements)
                except:
                    continue
            
            # If no specific unread indicators found, check first few conversations
            if not unread_conversations:
                try:
                    all_conversations = await page.query_selector_all("div[role='listitem']")
                    unread_conversations = all_conversations[:5]  # Check first 5 conversations
                except:
                    pass
            
            if not unread_conversations:
                self.log(f"[{account_username}] No conversations found in inbox", "INFO")
                return []
            
            self.log(f"[{account_username}] Found {len(unread_conversations)} potential unread conversations")
            
            # Check each unread conversation
            for i, conversation in enumerate(unread_conversations[:10]):  # Limit to 10 for speed
                try:
                    # Click on conversation
                    await conversation.click()
                    await asyncio.sleep(1)  # Reduced wait time
                    
                    # Get username from conversation header
                    username_selectors = [
                        "header h1", "header span", 
                        "div[role='button'] span", 
                        "a[role='link'] span"
                    ]
                    
                    conversation_username = "Unknown"
                    for selector in username_selectors:
                        try:
                            username_element = await page.query_selector(selector)
                            if username_element:
                                username_text = await username_element.inner_text()
                                if username_text and len(username_text.strip()) > 0:
                                    conversation_username = username_text.strip()
                                    break
                        except:
                            continue
                    
                    # Get the latest message (assume it's unread)
                    message_selectors = [
                        "div[data-testid='message-text']",
                        "div[class*='message'] span",
                        "div[role='row'] div span"
                    ]
                    
                    latest_message = ""
                    for selector in message_selectors:
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                # Get the last message
                                last_element = elements[-1]
                                latest_message = await last_element.inner_text()
                                if latest_message and len(latest_message.strip()) > 0:
                                    break
                        except:
                            continue
                    
                    # Store any message found (we're not filtering, just collecting)
                    if latest_message and len(latest_message.strip()) > 0:
                        response_data = {
                            'account': account_username,
                            'responder': conversation_username,
                            'message': latest_message.strip(),
                            'timestamp': datetime.now().isoformat()
                        }
                        responses.append(response_data)
                        self.log(f"[{account_username}] 📩 Response from {conversation_username}: {latest_message[:50]}...", "INFO")
                    
                    # Go back to inbox quickly
                    await page.go_back()
                    await asyncio.sleep(0.5)  # Reduced wait time
                    
                except Exception as e:
                    self.log(f"[{account_username}] Error checking conversation {i+1}: {e}", "WARNING")
                    # Try to go back to inbox if we're stuck
                    try:
                        await page.go_back()
                        await asyncio.sleep(0.5)
                    except:
                        break
                    continue
            
            self.log(f"[{account_username}] Collected {len(responses)} responses")
            return responses
            
        except Exception as e:
            self.log(f"[{account_username}] Error checking responses: {e}", "ERROR")
            return []
    
    def distribute_users(self, users, num_accounts):
        """Distribute users across accounts"""
        distributed = [[] for _ in range(num_accounts)]
        for i, user in enumerate(users):
            distributed[i % num_accounts].append(user)
        return distributed
    
    async def process_account(self, account_data, assigned_users, prompt_template, dm_limit, account_number=1):
        """Process DMs for single account with enhanced error handling"""
        username = account_data.get('username')
        password = account_data.get('password')
        
        playwright = None
        browser = None
        context = None
        proxy_string = None
        
        try:
            # Get a unique proxy for this account
            proxy_string = self.get_available_proxy()
            if not proxy_string:
                self.log(f"[{username}] No available proxies", "WARNING")
            
            self.log(f"[{username}] Starting with {len(assigned_users)} users (limit: {dm_limit})")
            
            # Setup browser with proxy
            playwright, browser, context = await self.setup_browser(proxy_string, account_number)
            page = await context.new_page()
            
            # Add visual status update
            if self.visual_mode:
                await self.update_visual_status(page, "Setting up browser", account_number, 1)
            
            # Login
            if not await self.login_instagram(page, username, password, account_number):
                self.log(f"[{username}] Login failed", "ERROR")
                if self.visual_mode:
                    await self.update_visual_status(page, "❌ Login failed", account_number)
                return {"account": username, "sent": 0, "processed": 0, "error": "Login failed"}
            
            if self.visual_mode:
                await self.update_visual_status(page, "✅ Login successful", account_number, 3)
            
            sent_count = 0
            processed_count = 0
            
            # Add visual status update for DM processing start
            if self.visual_mode:
                await self.update_visual_status(page, f"Processing {len(assigned_users)} users", account_number, 4)
            
            # Process users up to limit
            users_to_process = assigned_users[:dm_limit]
            
            for user in users_to_process:
                # Check if browser is still connected (closed detection)
                try:
                    if not browser.is_connected():
                        self.log(f"[{username}] Browser was closed manually - stopping automation", "WARNING")
                        return {"account": username, "sent": sent_count, "processed": processed_count, "error": "Browser closed manually"}
                except:
                    # If we can't check browser status, assume it's closed
                    self.log(f"[{username}] Browser connection lost - stopping automation", "WARNING") 
                    return {"account": username, "sent": sent_count, "processed": processed_count, "error": "Browser connection lost"}
                
                if self.stop_callback():
                    self.log(f"[{username}] Stopped by user request", "WARNING")
                    break
                
                processed_count += 1
                target_username = user.get('username', f'user_{processed_count}')
                
                # Generate personalized message
                message = self.generate_message(user, prompt_template)
                
                # Add visual status update
                if self.visual_mode:
                    await self.update_visual_status(page, f"Sending DM {sent_count + 1}/{dm_limit}", account_number)
                
                # Send DM
                result = await self.send_dm(page, target_username, message)
                
                if result is True:
                    sent_count += 1
                    self.log(f"[{username}] DM sent to {target_username} ({sent_count}/{dm_limit})")
                    
                    # Update visual progress
                    if self.visual_mode:
                        await self.update_visual_status(page, f"✅ Sent {sent_count}/{dm_limit} DMs", account_number)
                    
                    # Save to sent DMs log
                    with csv_lock:
                        self.sent_dms.append({
                            'timestamp': datetime.now().isoformat(),
                            'bot_account': username,
                            'target_username': target_username,
                            'message': message,
                            'status': 'sent'
                        })
                else:
                    self.log(f"[{username}] Failed to send DM to {target_username}: {result}", "WARNING")
                
                # Rate limiting
                await asyncio.sleep(random.uniform(10, 20))
                
                if sent_count >= dm_limit:
                    break
            
            self.log(f"[{username}] Completed: {sent_count} sent out of {processed_count} processed")
            
            # Check for responses after sending all DMs
            self.log(f"[{username}] Waiting 10 seconds before checking for responses...")
            await asyncio.sleep(10)  # Reduced wait time
            
            responses = await self.check_dm_responses(page, username)
            
            # Store responses globally
            if responses:
                self.positive_responses.extend(responses)
                self.log(f"[{username}] Collected {len(responses)} positive responses!")
            
            # Add visual completion status
            if self.visual_mode:
                response_text = f" | {len(responses)} responses" if responses else ""
                await self.update_visual_status(page, f"✅ COMPLETED! {sent_count} DMs sent{response_text}", account_number)
                # Keep browser open briefly to show final status
                await asyncio.sleep(3)
            
            return {
                "account": username,
                "sent": sent_count,
                "processed": processed_count,
                "responses": len(responses),
                "proxy_used": proxy_string.split(':')[0] if proxy_string else "none"
            }
            
        except Exception as e:
            self.log(f"[{username}] Processing error: {e}", "ERROR")
            if self.visual_mode:
                await self.update_visual_status(page, f"❌ Error: {str(e)}", account_number)
            return {"account": username, "sent": 0, "processed": 0, "error": str(e)}
            
        finally:
            # Release proxy back to pool
            if proxy_string:
                self.release_proxy(proxy_string)
            
            # Cleanup browser
            try:
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()
            except:
                pass

async def run_dm_automation(
    script_id,
    accounts_file,
    target_file=None,
    prompt_file=None,
    custom_prompt=None,
    dms_per_account=30,
    visual_mode=False,
    log_callback=None,
    stop_callback=None
):
    """Main function to run DM automation"""
    
    engine = DMAutomationEngine(log_callback, stop_callback, visual_mode)
    
    try:
        engine.log("=== Instagram DM Automation Started ===")
        engine.log(f"Script ID: {script_id}")
        engine.log("") 
        engine.log("📋 ACCOUNT REQUIREMENTS:")
        engine.log("✅ Account should NOT have 2FA (Two Factor Authentication) enabled")
        engine.log("✅ Account should be verified/trusted (not flagged for suspicious activity)")  
        engine.log("✅ Account should have been logged in recently from this IP/device")
        engine.log("")
        
        # Setup AI client
        if not engine.setup_openai_client():
            engine.log("Failed to setup AI client", "ERROR")
            return False
        
        # Load data
        engine.log("Loading bot accounts...")
        bot_accounts = engine.load_accounts(accounts_file)
        
        if not bot_accounts:
            engine.log("No valid bot accounts found", "ERROR")
            return False
        
        # Use all accounts from the file dynamically
        engine.log(f"Using {len(bot_accounts)} bot accounts (all accounts from file)")

        engine.log("Loading target users...")
        target_users = engine.load_target_users(target_file)
        
        if not target_users:
            engine.log("No target users found", "ERROR")
            return False
        
        # Load DM prompt
        prompt_template = engine.load_dm_prompt(prompt_file, custom_prompt)
        
        engine.log(f"Configuration:")
        engine.log(f"- Bot accounts: {len(bot_accounts)}")
        engine.log(f"- Target users: {len(target_users)}")
        engine.log(f"- DMs per account: {dms_per_account}")
        engine.log(f"- Total target DMs: {len(bot_accounts) * dms_per_account}")
        
        # Distribute users across accounts
        user_distribution = engine.distribute_users(target_users, len(bot_accounts))
        
        engine.log("Starting parallel DM campaigns...")
        
        # Create tasks for parallel processing
        tasks = []
        for i, (account, assigned_users) in enumerate(zip(bot_accounts, user_distribution), 1):
            if assigned_users:
                task = engine.process_account(account, assigned_users, prompt_template, dms_per_account, i)
                tasks.append(task)
        
        # Run parallel processing
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check if any browser was closed manually (early termination)
        browser_closed_manually = False
        for result in results:
            if isinstance(result, dict) and result.get('error') in ['Browser closed manually', 'Browser connection lost']:
                browser_closed_manually = True
                engine.log("⚠️ Browser was closed manually - stopping automation", "WARNING")
                break
        
        if browser_closed_manually:
            engine.log("❌ Automation stopped due to browser closure", "ERROR")
            return False  # This will trigger automatic script stopping
        
        # Calculate final results
        total_sent = 0
        total_processed = 0
        total_responses = 0
        successful_accounts = 0
        
        engine.log("\n=== FINAL RESULTS ===")
        
        for i, result in enumerate(results):
            if isinstance(result, dict):
                account = result.get('account', f'Account_{i+1}')
                sent = result.get('sent', 0)
                processed = result.get('processed', 0)
                responses = result.get('responses', 0)
                error = result.get('error')
                
                if error:
                    engine.log(f"❌ {account}: Error - {error}", "ERROR")
                else:
                    response_text = f" | {responses} responses" if responses > 0 else ""
                    engine.log(f"✅ {account}: {sent}/{processed} DMs sent{response_text}")
                    successful_accounts += 1
                
                total_sent += sent
                total_processed += processed
                total_responses += responses
            else:
                engine.log(f"❌ Task failed: {result}", "ERROR")
        
        engine.log(f"\n📊 SUMMARY:")
        engine.log(f"- Total DMs sent: {total_sent}")
        engine.log(f"- Total targets processed: {total_processed}")
        engine.log(f"- Total positive responses: {total_responses}")
        engine.log(f"- Response rate: {(total_responses/total_sent)*100:.1f}%" if total_sent > 0 else "0%")
        engine.log(f"- Success rate: {(total_sent/total_processed)*100:.1f}%" if total_processed > 0 else "0%")
        engine.log(f"- Successful accounts: {successful_accounts}/{len(bot_accounts)}")
        
        # Save results
        if engine.sent_dms:
            try:
                import os
                results_file = os.path.join('logs', f'dm_results_{script_id}.csv')
                os.makedirs('logs', exist_ok=True)
                
                with open(results_file, 'w', newline='', encoding='utf-8') as f:
                    if engine.sent_dms:
                        fieldnames = engine.sent_dms[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(engine.sent_dms)
                
                engine.log(f"Results saved to: {results_file}")
            except Exception as e:
                engine.log(f"Failed to save results: {e}", "WARNING")
        
        # Save positive responses
        if engine.positive_responses:
            try:
                import os
                responses_file = os.path.join('logs', f'dm_responses_{script_id}.csv')
                
                with open(responses_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = engine.positive_responses[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(engine.positive_responses)
                
                engine.log(f"Positive responses saved to: {responses_file}")
                
                # Also save as JSON for API access
                responses_json_file = os.path.join('logs', f'dm_responses_{script_id}.json')
                with open(responses_json_file, 'w', encoding='utf-8') as f:
                    json.dump(engine.positive_responses, f, indent=2, ensure_ascii=False)
                
            except Exception as e:
                engine.log(f"Failed to save positive responses: {e}", "WARNING")
        
        engine.log("=== DM Automation Completed ===")
        return total_sent > 0
        
    except Exception as e:
        engine.log(f"DM Automation failed: {e}", "ERROR")
        import traceback
        engine.log(f"Traceback: {traceback.format_exc()}", "ERROR")
        return False
