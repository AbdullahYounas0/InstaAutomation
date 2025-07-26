import asyncio
import pandas as pd
from playwright.async_api import async_playwright, TimeoutError
import os
import glob
import time
import random
from pathlib import Path
import logging

class InstagramDailyPostAutomation:
    def __init__(self, script_id, log_callback=None, stop_flag_callback=None, visual_mode=False):
        self.script_id = script_id
        self.log_callback = log_callback or self.default_log
        self.stop_flag_callback = stop_flag_callback or (lambda: False)
        self.visual_mode = visual_mode  # Whether to show browsers
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        self.supported_video_formats = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v']
        self.media_file = None
        self.is_video = False
        
    def default_log(self, message, level="INFO"):
        """Default logging function"""
        print(f"[{level}] {message}")
        
    def log(self, message, level="INFO"):
        """Log message using the callback"""
        self.log_callback(message, level)

    def should_stop(self):
        """Check if the script should stop"""
        return self.stop_flag_callback()

    def load_accounts_from_file(self, file_path):
        """Load Instagram credentials from Excel or CSV file."""
        try:
            # Determine file type and read accordingly
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            if df.empty:
                self.log("Error: Accounts file is empty.", "ERROR")
                return []
            
            # Check for required columns (case-insensitive)
            df.columns = df.columns.str.strip().str.title()
            required_columns = ["Username", "Password"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.log(f"Error: Missing columns in accounts file: {missing_columns}.", "ERROR")
                self.log(f"Available columns: {list(df.columns)}", "ERROR")
                return []
            
            # Load accounts
            accounts = []
            for i in range(len(df)):
                username = df.loc[i, "Username"]
                password = df.loc[i, "Password"]
                if pd.notna(username) and pd.notna(password):
                    accounts.append((str(username).strip(), str(password).strip()))
            
            self.log(f"Loaded {len(accounts)} account(s) from file.")
            return accounts
            
        except FileNotFoundError:
            self.log(f"Error: File {file_path} not found.", "ERROR")
            return []
        except Exception as e:
            self.log(f"Error loading accounts: {e}", "ERROR")
            return []

    def set_media_file(self, media_path):
        """Set the media file and determine if it's a video"""
        self.media_file = media_path
        file_ext = Path(media_path).suffix.lower()
        self.is_video = file_ext in self.supported_video_formats
        self.log(f"Media file set: {os.path.basename(media_path)} ({'Video' if self.is_video else 'Image'})")

    async def human_type(self, page, selector, text, delay_range=(50, 150)):
        """Type text with random delays"""
        if self.should_stop():
            return
        element = await page.wait_for_selector(selector, state='visible')
        await element.click()
        await page.wait_for_timeout(random.randint(300, 800))
        
        for char in text:
            if self.should_stop():
                return
            await element.type(char)
            await page.wait_for_timeout(random.randint(delay_range[0], delay_range[1]))

    async def update_visual_status(self, page, status_text, step=None):
        """Update visual status banner if in visual mode"""
        if self.visual_mode:
            try:
                step_text = f" - Step {step}" if step else ""
                # Choose color based on status
                if "✅" in status_text or "successful" in status_text.lower() or "completed" in status_text.lower():
                    color = '#28a745, #20c997'  # Green gradient
                elif "❌" in status_text or "error" in status_text.lower() or "failed" in status_text.lower():
                    color = '#dc3545, #fd7e14'  # Red gradient  
                elif "uploading" in status_text.lower() or "processing" in status_text.lower() or "sharing" in status_text.lower():
                    color = '#007bff, #6f42c1'  # Blue gradient
                else:
                    color = '#4ecdc4, #45b7aa'  # Default teal gradient
                    
                await page.evaluate(f'''
                    const banner = document.querySelector('#automation-status-banner');
                    if (banner) {{
                        banner.textContent = '{status_text}{step_text}';
                        banner.style.background = 'linear-gradient(90deg, {color})';
                    }}
                ''')
            except:
                pass  # Ignore errors in visual updates

    async def human_delay(self, min_ms=1000, max_ms=3000):
        """Add human-like random delays."""
        if self.should_stop():
            return
        await asyncio.sleep(random.randint(min_ms, max_ms) / 1000)

    async def handle_login_info_save_dialog(self, page, account_number):
        """Handle the 'Save your login info?' dialog by clicking 'Not now'"""
        try:
            self.log(f"[Account {account_number}] Looking for 'Not now' button on save login info dialog...")
            
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
                        self.log(f"[Account {account_number}] ✅ Clicked 'Not now' on save login info dialog")
                        await self.human_delay(1000, 2000)
                        return True
                except:
                    continue
            
            self.log(f"[Account {account_number}] ⚠️ Could not find 'Not now' button, continuing...")
            return False
            
        except Exception as e:
            self.log(f"[Account {account_number}] Error handling save login dialog: {e}")
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

    async def instagram_post_script(self, username, password, account_number, caption=""):
        """Main Instagram posting function for a single account."""
        self.log(f"[Account {account_number}] Starting automation for {username}")
        
        if self.should_stop():
            return
        
        try:
            async with async_playwright() as p:
                if self.should_stop():
                    return
                    
                self.log(f"[Account {account_number}] Launching browser...")
                
                # Configure browser launch args based on visual mode
                browser_args = [
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor'
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
                    
                    viewport_width = window_width - 16  # Account for browser chrome
                    viewport_height = window_height - 120
                    
                    self.log(f"[Account {account_number}] Browser window positioned at ({x_position}, {y_position}) - Grid position: Col {col+1}, Row {row+1}")
                else:
                    # Full size for headless mode
                    viewport_width = 1920
                    viewport_height = 1080
                
                browser = await p.chromium.launch(
                    headless=not self.visual_mode,  # Show browsers only in visual mode
                    args=browser_args
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': viewport_width, 'height': viewport_height}
                )
                
                page = await context.new_page()
                
                # Set page title and add visual indicators in visual mode
                if self.visual_mode:
                    await page.evaluate(f'''
                        document.title = "Account {account_number}: {username}";
                        // Add a colored banner to identify the account
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
                        banner.textContent = 'Account {account_number}: {username} - Initializing...';
                        document.body?.prepend(banner);
                    ''')

                try:
                    if self.should_stop():
                        return
                        
                    # Login to Instagram
                    self.log(f"[Account {account_number}] Navigating to Instagram login page...")
                    await self.update_visual_status(page, "Navigating to login page", 1)
                    await page.goto("https://www.instagram.com/accounts/login/", wait_until='domcontentloaded')
                    await self.human_delay(2000, 4000)
                    
                    # Wait for login form
                    await page.wait_for_selector('input[name="username"]', state='visible', timeout=30000)
                    await self.human_delay(1000, 2000)

                    # Human-like typing for credentials
                    self.log(f"[Account {account_number}] Entering credentials...")
                    await self.update_visual_status(page, "Entering credentials", 2)
                    await self.human_type(page, 'input[name="username"]', username)
                    await self.human_delay(500, 1500)
                    await self.human_type(page, 'input[name="password"]', password)
                    await self.human_delay(1000, 2000)
                    
                    if self.should_stop():
                        return
                    
                    # Click login button
                    self.log(f"[Account {account_number}] Clicking login button...")
                    await self.update_visual_status(page, "Logging in", 3)
                    await page.click('button[type="submit"]')
                    await self.human_delay(3000, 5000)
                    
                    # Wait for login to complete
                    self.log(f"[Account {account_number}] Waiting for login to complete...")
                    try:
                        await page.wait_for_url("https://www.instagram.com/", timeout=15000)
                        self.log(f"[Account {account_number}] Login successful!")
                        await self.update_visual_status(page, "Login successful!", 4)
                    except TimeoutError:
                        # Check if we're on the "Save your login info?" page first
                        current_url = page.url
                        if "accounts/onetap" in current_url:
                            self.log(f"[Account {account_number}] Handling 'Save your login info?' dialog...")
                            await self.handle_login_info_save_dialog(page, account_number)
                            # After handling the dialog, wait for home page
                            try:
                                await page.wait_for_url("https://www.instagram.com/", timeout=10000)
                                self.log(f"[Account {account_number}] Login successful after handling save dialog!")
                                await self.update_visual_status(page, "Login successful!", 4)
                            except TimeoutError:
                                await page.wait_for_selector('svg[aria-label="Home"]', state='visible', timeout=10000)
                                self.log(f"[Account {account_number}] Login successful!")
                                await self.update_visual_status(page, "Login successful!", 4)
                        else:
                            try:
                                await page.wait_for_selector('svg[aria-label="Home"]', state='visible', timeout=10000)
                                self.log(f"[Account {account_number}] Login successful!")
                                await self.update_visual_status(page, "Login successful!", 4)
                            except TimeoutError:
                                # Check if verification is required
                                if await self.is_verification_required(page):
                                    # Log message that frontend will detect for notification
                                    self.log(f"[Account {account_number}] ⚠️ Account {username} requires verification/2FA", "WARNING")
                                    self.log(f"[Account {account_number}] 🔔 Please check the account {username} and manually solve the CAPTCHA or 2FA", "WARNING")
                                    self.log(f"[Account {account_number}] ⏱️ Script will pause for 5 minutes and then retry...", "INFO")
                                    await self.update_visual_status(page, "CAPTCHA/2FA required - pausing 5 mins", 2)
                                    
                                    # Wait for 5 minutes (300 seconds) before retrying
                                    await asyncio.sleep(300)
                                    
                                    self.log(f"[Account {account_number}] 🔄 Resuming after 5-minute pause...", "INFO")
                                    
                                    # Check again if verification is still required
                                    if await self.is_verification_required(page):
                                        self.log(f"[Account {account_number}] ❌ Verification still required. Skipping account {username}.", "ERROR")
                                        return False
                                    else:
                                        self.log(f"[Account {account_number}] ✅ Verification resolved for {username}. Continuing...", "SUCCESS")
                                else:
                                    self.log(f"[Account {account_number}] Login may have failed - checking for error messages...")
                                    error_selectors = [
                                        'div:has-text("Sorry, your password was incorrect")',
                                        'div:has-text("The username you entered doesn\'t belong to an account")',
                                        'div:has-text("We couldn\'t connect to Instagram")',
                                        'div:has-text("There was a problem logging you into Instagram")'
                                    ]
                                    
                                    for selector in error_selectors:
                                        try:
                                            error_element = await page.wait_for_selector(selector, timeout=2000)
                                            if error_element:
                                                error_text = await error_element.text_content()
                                                self.log(f"[Account {account_number}] Login error: {error_text}", "ERROR")
                                                return False
                                        except TimeoutError:
                                            continue

                    if self.should_stop():
                        return

                    # Handle popups
                    await self.handle_popups(page, account_number)

                    # Navigate to create post
                    self.log(f"[Account {account_number}] Looking for 'Create' button...")
                    await self.human_delay(2000, 4000)
                    
                    create_selectors = [
                        'svg[aria-label="New post"]',
                        'a[aria-label="New post"]',
                        'div[aria-label="New post"]',
                        'svg[aria-label="Create"]',
                        'a[href*="create"]'
                    ]
                    
                    clicked_create = False
                    for selector in create_selectors:
                        if self.should_stop():
                            return
                        try:
                            await page.wait_for_selector(selector, state='visible', timeout=5000)
                            await page.click(selector)
                            self.log(f"[Account {account_number}] Clicked create button.")
                            clicked_create = True
                            break
                        except TimeoutError:
                            continue
                    
                    if not clicked_create:
                        self.log(f"[Account {account_number}] Could not find create button.", "ERROR")
                        await self.update_visual_status(page, "Create button not found!", 2)
                        return False

                    await self.update_visual_status(page, "Opening create menu...", 3)
                    await self.human_delay(1000, 2000)

                    # Try to click Post option if available
                    post_selectors = [
                        'text="Post"',
                        'div[role="button"]:has-text("Post")',
                        'span:has-text("Post")',
                        'button:has-text("Post")'
                    ]
                    
                    for selector in post_selectors:
                        if self.should_stop():
                            return
                        try:
                            await page.wait_for_selector(selector, state='visible', timeout=3000)
                            await page.click(selector)
                            self.log(f"[Account {account_number}] Clicked 'Post' option.")
                            break
                        except TimeoutError:
                            continue

                    await self.human_delay(1000, 2000)

                    # Handle file upload
                    success = await self.handle_file_upload(page, account_number)
                    if not success:
                        return False

                    # Process the post
                    success = await self.process_post(page, account_number, caption)
                    if not success:
                        return False

                    self.log(f"[Account {account_number}] Post completed successfully!", "SUCCESS")
                    await self.update_visual_status(page, "✅ COMPLETED!", 5)
                    return True

                except Exception as e:
                    self.log(f"[Account {account_number}] Error during automation: {e}", "ERROR")
                    await self.update_visual_status(page, "❌ Error occurred!", 2)
                    return False
                finally:
                    if self.visual_mode:
                        # Keep browser open briefly to show final status
                        await asyncio.sleep(3)
                    self.log(f"[Account {account_number}] Closing browser...")
                    await browser.close()
                    
        except Exception as e:
            self.log(f"[Account {account_number}] Critical error: {e}", "ERROR")
            return False

    async def handle_popups(self, page, account_number):
        """Handle pop-ups"""
        if self.should_stop():
            return
            
        self.log(f"[Account {account_number}] Handling popups...")
        
        not_now_selectors = [
            'button:has-text("Not now")',
            'div[role="button"]:has-text("Not now")',
            'button:has-text("Not Now")',
            'div[role="button"]:has-text("Not Now")',
            '//button[contains(., "Not Now")]',
            '//button[contains(., "Not now")]'
        ]
        
        for _ in range(3):
            if self.should_stop():
                return
            dismissed_any = False
            for selector in not_now_selectors:
                try:
                    await page.wait_for_selector(selector, state='visible', timeout=3000)
                    await page.click(selector)
                    self.log(f"[Account {account_number}] Dismissed a popup.")
                    await self.human_delay(1000, 2000)
                    dismissed_any = True
                    break
                except TimeoutError:
                    continue
                except Exception as e:
                    continue
            if not dismissed_any:
                break

    async def handle_file_upload(self, page, account_number):
        """Handle the media file upload process."""
        if self.should_stop():
            return False
            
        self.log(f"[Account {account_number}] Handling file upload...")
        await self.update_visual_status(page, "Uploading file...", 3)
        await self.human_delay(2000, 4000)
        
        upload_selectors = [
            'button:has-text("Select from computer")',
            'div[role="button"]:has-text("Select from computer")',
            'input[type="file"]',
            'button:has-text("Select from Computer")',
            '//button[contains(., "Select from computer")]',
            '//input[@type="file"]'
        ]
        
        upload_success = False
        
        for selector in upload_selectors:
            if self.should_stop():
                return False
            try:
                if 'input[type="file"]' in selector or '//input[@type="file"]' in selector:
                    file_input = await page.wait_for_selector(selector, state='attached', timeout=10000)
                    await file_input.set_input_files(self.media_file)
                    self.log(f"[Account {account_number}] Uploaded file directly: {os.path.basename(self.media_file)}.")
                    upload_success = True
                    break
                else:
                    await page.wait_for_selector(selector, state='visible', timeout=10000)
                    
                    async with page.expect_file_chooser(timeout=15000) as fc_info:
                        await page.click(selector)
                        file_chooser = await fc_info.value
                        await file_chooser.set_files(self.media_file)
                        self.log(f"[Account {account_number}] Uploaded file via chooser: {os.path.basename(self.media_file)}.")
                        await self.update_visual_status(page, "File uploaded!", 4)
                        upload_success = True
                        break
                        
            except Exception as e:
                continue
        
        if not upload_success:
            self.log(f"[Account {account_number}] All upload methods failed.", "ERROR")
            await self.update_visual_status(page, "Upload failed!", 2)
            return False
            
        return True

    async def process_post(self, page, account_number, caption=""):
        """Navigate through post creation steps."""
        if self.should_stop():
            return False
            
        self.log(f"[Account {account_number}] Processing post...")
        await self.update_visual_status(page, "Processing post...", 3)
        
        next_selectors = [
            'button:has-text("Next")',
            'div[role="button"]:has-text("Next")',
            '//button[contains(., "Next")]'
        ]
        
        # First 'Next' button
        self.log(f"[Account {account_number}] Waiting for first 'Next' button...")
        await self.human_delay(3000, 5000)
        clicked_first_next = False
        for selector in next_selectors:
            if self.should_stop():
                return False
            try:
                await page.wait_for_selector(selector, state='visible', timeout=15000)
                await page.click(selector)
                self.log(f"[Account {account_number}] Clicked first 'Next'.")
                clicked_first_next = True
                break
            except TimeoutError:
                continue
        
        if not clicked_first_next:
            self.log(f"[Account {account_number}] Could not find or click first 'Next' button.", "ERROR")
            return False

        # Second 'Next' button
        self.log(f"[Account {account_number}] Waiting for second 'Next' button...")
        await self.human_delay(2000, 4000)
        
        for selector in next_selectors:
            if self.should_stop():
                return False
            try:
                await page.wait_for_selector(selector, state='visible', timeout=15000)
                await page.click(selector)
                self.log(f"[Account {account_number}] Clicked second 'Next'.")
                break
            except TimeoutError:
                continue

        await self.human_delay(2000, 3000)

        # Add caption
        await self.add_caption(page, account_number, caption)

        # Click 'Share' button
        self.log(f"[Account {account_number}] Clicking 'Share' button...")
        await self.human_delay(1000, 2000)
        
        share_selectors = [
            'div.x1i10hfl[role="button"]:has-text("Share")',
            'div[class*="x1i10hfl"][role="button"]:has-text("Share")',
            'div[class*="xjqpnuy"][role="button"]:has-text("Share")',
            'button:has-text("Share")',
            'div[role="button"]:has-text("Share")',
            '[role="button"]:has-text("Share")',
            '//div[@role="button" and contains(text(), "Share")]',
            '//button[contains(text(), "Share")]',
            'text="Share"',
            ':text("Share")',
        ]
        
        clicked_share = False
        for i, selector in enumerate(share_selectors):
            if self.should_stop():
                return False
            try:
                element = await page.wait_for_selector(selector, state='visible', timeout=5000)
                if element:
                    element_text = await element.text_content()
                    if "Share" in element_text:
                        await element.click()
                        self.log(f"[Account {account_number}] Clicked 'Share' - Upload in progress...")
                        await self.update_visual_status(page, "Sharing post...", 3)
                        clicked_share = True
                        break
            except TimeoutError:
                continue
            except Exception as e:
                continue

        if not clicked_share:
            self.log(f"[Account {account_number}] Could not find or click 'Share' button.", "ERROR")
            await self.update_visual_status(page, "Share button not found!", 2)
            return False

        # Wait for post completion
        self.log(f"[Account {account_number}] Waiting for post completion...")
        await self.human_delay(5000, 8000)
        try:
            await page.wait_for_selector('text="Your post has been shared."', timeout=30000)
            self.log(f"[Account {account_number}] Post shared successfully!")
            await self.update_visual_status(page, "Post shared successfully!", 4)
        except TimeoutError:
            try:
                await page.wait_for_url("https://www.instagram.com/", timeout=15000)
                self.log(f"[Account {account_number}] Post confirmed: Redirected to home page.")
            except TimeoutError:
                self.log(f"[Account {account_number}] Post status unclear, but 'Share' was clicked.")
        
        return True

    async def add_caption(self, page, account_number, caption=""):
        """Add caption to the post."""
        if self.should_stop():
            return
            
        self.log(f"[Account {account_number}] Adding caption...")
        await self.update_visual_status(page, "Adding caption...", 3)
        try:
            caption_selectors = [
                'textarea[aria-label="Write a caption..."]',
                'div[contenteditable="true"][aria-label*="caption"]',
                'textarea[placeholder*="caption"]',
                '//textarea[@aria-label="Write a caption..."]',
                '//div[@contenteditable="true" and contains(@aria-label, "caption")]'
            ]
            
            # Use provided caption or generate default one
            if not caption:
                media_type = "video" if self.is_video else "image"
                caption = f"Automated {media_type} post! 🤖✨ #automation #instagram #bot"
            
            for selector in caption_selectors:
                if self.should_stop():
                    return
                try:
                    caption_field = await page.wait_for_selector(selector, state='visible', timeout=10000)
                    await self.human_type(page, selector, caption, delay_range=(30, 100))
                    self.log(f"[Account {account_number}] Added caption.")
                    break
                except TimeoutError:
                    continue
            
        except Exception as e:
            self.log(f"[Account {account_number}] Caption addition failed: {e}", "ERROR")

    async def run_automation(self, accounts_file, media_file, concurrent_accounts=5, caption="", auto_generate_caption=True):
        """Run Instagram posting for multiple accounts concurrently."""
        self.log("Starting Multi-Account Instagram Automation.")
        self.log("=" * 50)
        
        # Set media file
        self.set_media_file(media_file)
        
        # Load credentials
        accounts = self.load_accounts_from_file(accounts_file)
        if not accounts:
            self.log("No valid accounts found. Please check your accounts file.", "ERROR")
            return False
        
        # Limit concurrent accounts
        accounts_to_process = accounts[:concurrent_accounts]
        self.log(f"Processing {len(accounts_to_process)} account(s) concurrently.")
        self.log("=" * 50)
        
        # Create semaphore to limit concurrent browsers
        semaphore = asyncio.Semaphore(min(concurrent_accounts, 5))  # Max 5 concurrent browsers
        
        async def process_account_with_semaphore(username, password, account_num):
            async with semaphore:
                if self.should_stop():
                    return False
                return await self.instagram_post_script(username, password, account_num, caption)
        
        # Create tasks for each account
        tasks = []
        for i, (username, password) in enumerate(accounts_to_process, 1):
            if self.should_stop():
                break
            self.log(f"Creating task for Account {i}: {username}.")
            task = asyncio.create_task(process_account_with_semaphore(username, password, i))
            tasks.append(task)
        
        if not tasks:
            self.log("No tasks created", "ERROR")
            return False
        
        self.log(f"Created {len(tasks)} tasks. Starting execution...")
        
        # Run all tasks concurrently
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Summary
            self.log("\nResults Summary:")
            successful_count = 0
            for i, result in enumerate(results, 1):
                if isinstance(result, Exception):
                    self.log(f"Account {i}: Failed with error: {result}", "ERROR")
                elif result:
                    self.log(f"Account {i}: Completed successfully.", "SUCCESS")
                    successful_count += 1
                else:
                    self.log(f"Account {i}: Failed", "ERROR")
            
            self.log("=" * 50)
            if successful_count == len(results):
                self.log(f"🎉 All accounts completed successfully! {successful_count}/{len(results)} accounts processed.", "SUCCESS")
            elif successful_count > 0:
                self.log(f"⚠️ Partial success: {successful_count}/{len(results)} accounts completed successfully.", "WARNING") 
            else:
                self.log(f"❌ No accounts completed successfully. {len(results)} accounts failed.", "ERROR")
            
            self.log(f"Automation finished! {successful_count}/{len(results)} accounts processed successfully.")
            return successful_count > 0
                    
        except Exception as e:
            self.log(f"Error in concurrent execution: {e}", "ERROR")
            return False

# Async function to run the automation (to be called from Flask)
async def run_daily_post_automation(script_id, accounts_file, media_file, concurrent_accounts=5, 
                                   caption="", auto_generate_caption=True, visual_mode=False,
                                   log_callback=None, stop_callback=None):
    """Main function to run the automation"""
    automation = InstagramDailyPostAutomation(script_id, log_callback, stop_callback, visual_mode)
    
    try:
        success = await automation.run_automation(
            accounts_file=accounts_file,
            media_file=media_file,
            concurrent_accounts=concurrent_accounts,
            caption=caption,
            auto_generate_caption=auto_generate_caption
        )
        return success
    except Exception as e:
        if log_callback:
            log_callback(f"Automation failed: {e}", "ERROR")
        return False
