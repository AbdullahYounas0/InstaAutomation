import asyncio
import pandas as pd
from playwright.async_api import async_playwright, Playwright, BrowserContext
import random
import time
import logging
import os
from datetime import datetime

# Configure logging for Instagram Warmup Automation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/instagram_warmup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('InstagramWarmup')

# Default Configuration
DEFAULT_WARMUP_DURATION_MINUTES = 300
DEFAULT_SCROLL_PAUSE_SECONDS = 2
DEFAULT_ACTIVITY_DELAY_SECONDS = (3, 7)
DEFAULT_SCROLL_ATTEMPTS = (5, 10)
DEFAULT_MAX_CONCURRENT_BROWSERS = 10

async def human_like_delay(delay_range=DEFAULT_ACTIVITY_DELAY_SECONDS, stop_callback=None):
    """Introduces a human-like delay between actions with stop signal checking."""
    delay_seconds = random.uniform(*delay_range)
    logger.debug(f"Human-like delay: {delay_seconds:.2f} seconds")
    
    # If delay is short, just sleep normally
    if delay_seconds <= 1:
        await asyncio.sleep(delay_seconds)
        return
    
    # For longer delays, check stop signal periodically
    elapsed = 0
    check_interval = 0.5  # Check every 500ms
    
    while elapsed < delay_seconds:
        if stop_callback and stop_callback():
            logger.debug("Stop signal received during delay")
            return  # Exit immediately if stop requested
        
        sleep_time = min(check_interval, delay_seconds - elapsed)
        await asyncio.sleep(sleep_time)
        elapsed += sleep_time

async def human_like_typing(page, selector, text):
    """Types text into a field with a human-like delay between characters."""
    logger.debug(f"Human-like typing: '{text[:20]}...'")
    try:
        await page.type(selector, text, delay=random.uniform(50, 150))
        logger.debug("Human-like typing completed successfully")
    except Exception as e:
        logger.error(f"Error during human-like typing: {str(e)}")
        raise

async def human_like_scroll(page):
    """Performs a human-like scroll action on the page."""
    scroll_amount = random.randint(300, 800)
    scroll_duration = random.uniform(0.5, 1.5)
    steps = random.randint(5, 15)
    step_amount = scroll_amount / steps
    step_delay = scroll_duration / steps

    logger.debug(f"Human-like scroll: {scroll_amount}px in {steps} steps over {scroll_duration:.2f}s")
    
    try:
        for _ in range(steps):
            await page.evaluate(f"window.scrollBy(0, {step_amount})")
            await asyncio.sleep(step_delay)
        logger.debug("Human-like scroll completed successfully")
    except Exception as e:
        logger.error(f"Error during human-like scroll: {str(e)}")
        raise
    await asyncio.sleep(random.uniform(0.5, 1.5))

async def is_verification_required(page):
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

async def handle_login_info_save_dialog(page, username, log_callback=None):
    """Handle the 'Save your login info?' dialog by clicking 'Not now'"""
    try:
        if log_callback:
            log_callback(f"{username}: Looking for 'Not now' button on save login info dialog...")
        
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
                    if log_callback:
                        log_callback(f"{username}: ✅ Clicked 'Not now' on save login info dialog")
                    await human_like_delay()
                    return True
            except:
                continue
        
        if log_callback:
            log_callback(f"{username}: ⚠️ Could not find 'Not now' button, continuing...")
        return False
        
    except Exception as e:
        if log_callback:
            log_callback(f"{username}: Error handling save login dialog: {e}")
        return False

async def login(context: BrowserContext, username, password, log_callback=None):
    """
    Attempts to log in to Instagram with the given credentials.
    Handles cookie consent and common post-login prompts.
    """
    page = await context.new_page()
    try:
        await page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        if log_callback:
            log_callback(f"{username}: Navigated to login page.")
        await human_like_delay()

        # Attempt to accept cookies if the dialog appears
        try:
            accept_cookies_button = await page.wait_for_selector('button:has-text("Allow all cookies")', timeout=5000)
            await accept_cookies_button.click()
            if log_callback:
                log_callback(f"{username}: Accepted cookies.")
            await human_like_delay()
        except Exception:
            if log_callback:
                log_callback(f"{username}: No cookie consent dialog found or already accepted.")

        await human_like_typing(page, 'input[name="username"]', username)
        await human_like_delay()
        await human_like_typing(page, 'input[name="password"]', password)
        if log_callback:
            log_callback(f"{username}: Entered credentials with human-like typing.")
        await human_like_delay()

        login_button = await page.wait_for_selector('button[type="submit"]', timeout=10000)
        await login_button.click()
        if log_callback:
            log_callback(f"{username}: Clicked login button.")
        await human_like_delay()

        try:
            await page.wait_for_url("https://www.instagram.com/", timeout=10000)
            if log_callback:
                log_callback(f"Successfully logged in with {username} and landed on home page directly.")
            return page
        except Exception:
            # Check if we're on the "Save your login info?" page first
            current_url = page.url
            if "accounts/onetap" in current_url:
                if log_callback:
                    log_callback(f"{username}: Handling 'Save your login info?' dialog...")
                if await handle_login_info_save_dialog(page, username, log_callback):
                    # After handling the dialog, wait for home page
                    try:
                        await page.wait_for_url("https://www.instagram.com/", timeout=10000)
                        if log_callback:
                            log_callback(f"Successfully logged in with {username} after handling save dialog!")
                        return page
                    except:
                        await page.wait_for_selector('a[href="/"]', timeout=10000)
                        if log_callback:
                            log_callback(f"Successfully logged in with {username}!")
                        return page
            
            # Check if verification is required
            if await is_verification_required(page):
                if log_callback:
                    # Log message that frontend will detect for notification
                    log_callback(f"[{username}] ⚠️ Account {username} requires verification/2FA", "WARNING")
                    log_callback(f"[{username}] 🔔 Please check the account {username} and manually solve the CAPTCHA or 2FA", "WARNING")
                    log_callback(f"[{username}] ⏱️ Script will pause for 5 minutes and then retry...", "INFO")
                
                # Wait for 5 minutes (300 seconds) before retrying
                await asyncio.sleep(300)
                
                if log_callback:
                    log_callback(f"[{username}] 🔄 Resuming after 5-minute pause...", "INFO")
                
                # Check again if verification is still required
                if await is_verification_required(page):
                    if log_callback:
                        log_callback(f"[{username}] ❌ Verification still required. Skipping account {username}.", "ERROR")
                    return None
                else:
                    if log_callback:
                        log_callback(f"[{username}] ✅ Verification resolved for {username}. Continuing...", "SUCCESS")
                    return page
            else:
                if log_callback:
                    log_callback(f"Login for {username} did not directly land on home page. Checking for intermediate prompts.")
                
                # Try multiple approaches to handle post-login dialogs
                handled_dialog = False
                
                # Approach 1: Look for "Not now" button with extended timeout and multiple selectors
                not_now_selectors = [
                    'div[role="button"]:has-text("Not now")',
                    'button:has-text("Not now")',
                    'div[role="button"]:has-text("Not Now")',
                    'button:has-text("Not Now")',
                    '[role="button"]:has-text("Not now")',
                    '[role="button"]:has-text("Not Now")',
                    '//button[contains(text(), "Not now")]',
                    '//div[@role="button" and contains(text(), "Not now")]'
                ]
                
                for selector in not_now_selectors:
                    try:
                        await page.wait_for_timeout(2000)  # Wait 2 seconds between attempts
                        not_now_button = await page.wait_for_selector(selector, timeout=5000)
                        if not_now_button:
                            await not_now_button.click()
                            if log_callback:
                                log_callback(f"{username}: ✅ Clicked 'Not now' using selector: {selector}")
                            handled_dialog = True
                            break
                    except Exception:
                        continue
                
                # Approach 2: Look for home elements if dialog handling failed
                if not handled_dialog:
                    if log_callback:
                        log_callback(f"{username}: No 'Not now' button found, checking if already on home page...")
                
                # Wait for home page elements with extended timeout
                try:
                    await human_like_delay()
                    home_selectors = [
                        'a[href="/"]',
                        '[data-testid="home-link"]',
                        'svg[aria-label="Home"]',
                        'div[role="main"]'
                    ]
                    
                    home_found = False
                    for selector in home_selectors:
                        try:
                            await page.wait_for_selector(selector, timeout=8000)
                            home_found = True
                            break
                        except Exception:
                            continue
                    
                    if home_found or 'instagram.com' in page.url:
                        if log_callback:
                            log_callback(f"{username}: ✅ Successfully logged in and reached home page.")
                        return page
                    else:
                        if log_callback:
                            log_callback(f"{username}: ⚠️ Login may have succeeded but couldn't verify home page. Current URL: {page.url}")
                        return page  # Return page anyway, activities will handle further navigation
                        
                except Exception as e:
                    if log_callback:
                        log_callback(f"Login verification failed for {username}: Could not confirm successful login. Current URL: {page.url} Error: {e}", "ERROR")
                    return None
    except Exception as e:
        if log_callback:
            log_callback(f"Error during login for {username}: {e}", "ERROR")
        await page.close()
        return None

async def perform_activities(page, username, duration_minutes, activities, timing, log_callback=None, stop_callback=None):
    """
    Performs a series of human-like activities on Instagram for a given duration.
    Activities include scrolling feed, watching/liking reels, liking feed posts,
    and visiting random pages.
    """
    if log_callback:
        log_callback(f"Starting activities for {username}...")
    start_time = time.time()
    end_time = start_time + duration_minutes * 60

    activity_delay = timing.get('activity_delay', DEFAULT_ACTIVITY_DELAY_SECONDS)
    scroll_attempts = timing.get('scroll_attempts', DEFAULT_SCROLL_ATTEMPTS)

    while time.time() < end_time:
        # Check if stop was requested
        if stop_callback and stop_callback():
            if log_callback:
                log_callback(f"{username}: Stopping activities due to user request.")
            break
            
        # Build activity choices based on enabled activities
        activity_choices = []
        if activities.get('feed_scroll', True):
            activity_choices.append("feed_scroll")
        if activities.get('watch_reels', True):
            activity_choices.append("watch_reel")
        if activities.get('like_reels', True):
            activity_choices.append("like_reel")
        if activities.get('like_posts', True):
            activity_choices.append("like_feed_post")
        if activities.get('explore_page', True):
            activity_choices.append("explore_scroll")
        if activities.get('random_visits', True):
            activity_choices.append("random_page_scroll")
        
        if not activity_choices:
            activity_choices = ["feed_scroll"]  # Default fallback
            
        activity_type = random.choice(activity_choices)
        if log_callback:
            log_callback(f"{username}: Performing activity: {activity_type}")

        try:
            if activity_type == "feed_scroll":
                if log_callback:
                    log_callback(f"{username}: Scrolling through feed...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay, stop_callback)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"{username}: Stopping feed scroll due to user request.")
                        return
                    await human_like_scroll(page)

            elif activity_type == "watch_reel":
                if log_callback:
                    log_callback(f"{username}: Watching reels...")
                await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"{username}: Stopping reel watching due to user request.")
                            return
                        await human_like_scroll(page)

                    reels = await page.query_selector_all('div:has(video[playsinline])')
                    if reels:
                        chosen_reel = random.choice(reels)
                        await chosen_reel.scroll_into_view_if_needed()
                        if log_callback:
                            log_callback(f"{username}: Watched a reel.")
                        
                        # Check for stop signal during reel watching
                        watch_duration = random.uniform(5, 15)
                        for _ in range(int(watch_duration)):
                            if stop_callback and stop_callback():
                                if log_callback:
                                    log_callback(f"{username}: Stopping reel watching due to user request.")
                                return
                            await asyncio.sleep(1)
                    else:
                        if log_callback:
                            log_callback(f"{username}: No reels found to watch.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"{username}: Error while trying to watch reel: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "like_reel":
                if log_callback:
                    log_callback(f"{username}: Attempting to like a reel...")
                await page.goto("https://www.instagram.com/reels/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"{username}: Stopping reel liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_button = await page.wait_for_selector(selector, timeout=3000)
                            if like_button:
                                is_visible = await like_button.is_visible()
                                if is_visible:
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"{username}: Liked a reel.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role=\\"button\\"]") || element.closest("span[role=\\"button\\"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"{username}: Liked a reel.")
                                else:
                                    if log_callback:
                                        log_callback(f"{username}: Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"{username}: Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"{username}: No like buttons found for reels.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"{username}: Error while trying to like reel: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "like_feed_post":
                if log_callback:
                    log_callback(f"{username}: Attempting to like a feed post...")
                await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                try:
                    scroll_count = random.randint(*scroll_attempts)
                    for i in range(scroll_count):
                        # Check for stop signal before each scroll
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback(f"{username}: Stopping feed post liking due to user request.")
                            return
                        await human_like_scroll(page)

                    like_selectors = [
                        'svg[aria-label="Like"]',
                        'button[aria-label="Like"]',
                        'div[role="button"] svg[aria-label="Like"]',
                        'span[role="button"] svg[aria-label="Like"]'
                    ]
                    
                    like_button = None
                    for selector in like_selectors:
                        try:
                            like_buttons = await page.query_selector_all(selector)
                            if like_buttons:
                                visible_buttons = [btn for btn in like_buttons if await btn.is_visible()]
                                if visible_buttons:
                                    like_button = random.choice(visible_buttons)
                                    break
                        except:
                            continue
                    
                    if like_button:
                        try:
                            await like_button.click()
                            if log_callback:
                                log_callback(f"{username}: Liked a feed post.")
                        except:
                            try:
                                parent_button = await like_button.evaluate_handle('element => element.closest("button") || element.closest("div[role=\\"button\\"]") || element.closest("span[role=\\"button\\"]")')
                                if parent_button:
                                    await parent_button.click()
                                    if log_callback:
                                        log_callback(f"{username}: Liked a feed post.")
                                else:
                                    if log_callback:
                                        log_callback(f"{username}: Found like button but couldn't click it.", "WARNING")
                            except Exception as e:
                                if log_callback:
                                    log_callback(f"{username}: Error clicking like button: {e}", "WARNING")
                    else:
                        if log_callback:
                            log_callback(f"{username}: No like buttons found for feed posts.", "WARNING")
                except Exception as e:
                    if log_callback:
                        log_callback(f"{username}: Error while trying to like a feed post: {e}", "ERROR")
                await human_like_delay(activity_delay)

            elif activity_type == "explore_scroll":
                if log_callback:
                    log_callback(f"{username}: Navigating to Explore page and scrolling...")
                await page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"{username}: Stopping explore scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"{username}: Finished scrolling on Explore page.")
                await human_like_delay(activity_delay)

            elif activity_type == "random_page_scroll":
                pages_to_visit = {
                    "Search": "https://www.instagram.com/explore/search/",
                    "Messages": "https://www.instagram.com/direct/inbox/",
                    "Notifications": "https://www.instagram.com/accounts/activity/",
                    "Profile": "https://www.instagram.com/accounts/edit/"
                }
                page_name, page_url = random.choice(list(pages_to_visit.items()))
                if log_callback:
                    log_callback(f"{username}: Navigating to {page_name} page and scrolling...")
                await page.goto(page_url, wait_until="domcontentloaded")
                await human_like_delay(activity_delay)
                scroll_count = random.randint(*scroll_attempts)
                for i in range(scroll_count):
                    # Check for stop signal before each scroll
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"{username}: Stopping {page_name} scrolling due to user request.")
                        return
                    await human_like_scroll(page)
                if log_callback:
                    log_callback(f"{username}: Finished scrolling on {page_name} page.")
                await human_like_delay(activity_delay)

        except Exception as e:
            if log_callback:
                log_callback(f"{username}: Unhandled error during activity '{activity_type}': {e}", "ERROR")
            
        remaining_time = int(end_time - time.time())
        if remaining_time > 0 and log_callback:
            log_callback(f"{username}: Remaining time for activities: {remaining_time // 60} minutes and {remaining_time % 60} seconds.")
        else:
            if log_callback:
                log_callback(f"{username}: Warmup duration completed.")
            break

    if log_callback:
        log_callback(f"Activities finished for {username}.")

async def worker(playwright: Playwright, account_queue: asyncio.Queue, config, log_callback=None, stop_callback=None):
    """
    Worker task to process accounts. Each worker launches a browser and processes
    accounts from the queue until it's empty. Each account is processed in isolation.
    """
    browser = None
    current_username = "unknown_user"
    accounts_processed = 0
    accounts_successful = 0
    accounts_failed = 0

    try:
        # Force headless mode in production environment (unless explicitly overridden)
        is_production = os.environ.get('ENVIRONMENT') == 'production'
        allow_visual_in_prod = os.environ.get('ENABLE_VISUAL_MODE') == 'true'
        headless_mode = True if (is_production and not allow_visual_in_prod) else not config.get('visual_mode', False)
        
        browser = await playwright.chromium.launch(
            headless=headless_mode,  # Always headless in production unless overridden
            channel="chrome"
        )
        
        if log_callback:
            log_callback("Worker started - processing accounts from queue.")
        
        while True:
            # Check if stop was requested
            if stop_callback and stop_callback():
                if log_callback:
                    log_callback(f"Worker stopping due to user request. Processed: {accounts_processed}, Successful: {accounts_successful}, Failed: {accounts_failed}")
                break
                
            try:
                username, password = account_queue.get_nowait()
                current_username = username
                accounts_processed += 1
            except asyncio.QueueEmpty:
                if log_callback:
                    log_callback(f"Account queue is empty. Worker exiting. Final stats - Processed: {accounts_processed}, Successful: {accounts_successful}, Failed: {accounts_failed}")
                break

            # Process each account in complete isolation
            context = None
            page = None
            account_success = False
            
            try:
                if log_callback:
                    log_callback(f"[Account {accounts_processed}] Starting automation for {current_username}")
                
                # Create new context for this account
                context = await browser.new_context()
                
                # Attempt login
                page = await login(context, username, password, log_callback)
                
                if page:
                    # Check for stop signal before starting activities
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback(f"Worker stopping for {current_username} due to user request before activities.")
                        break
                    
                    # Perform activities
                    await perform_activities(
                        page, username, 
                        config['warmup_duration'], 
                        config['activities'], 
                        config['timing'],
                        log_callback, 
                        stop_callback
                    )
                    
                    account_success = True
                    accounts_successful += 1
                    if log_callback:
                        log_callback(f"[Account {accounts_processed}] ✅ Successfully completed automation for {current_username}")
                else:
                    accounts_failed += 1
                    if log_callback:
                        log_callback(f"[Account {accounts_processed}] ❌ Login failed for {current_username}, skipping activities.")
                        
            except Exception as e:
                accounts_failed += 1
                if log_callback:
                    log_callback(f"[Account {accounts_processed}] ❌ Error during automation for {current_username}: {str(e)}", "ERROR")
                # Log the error but continue with next account
                
            finally:
                # Always clean up the context for this account
                if context:
                    try:
                        await context.close()
                        if log_callback:
                            log_callback(f"[Account {accounts_processed}] Closed browser context for {current_username}.")
                    except Exception as e:
                        if log_callback:
                            log_callback(f"[Account {accounts_processed}] Error closing context for {current_username}: {e}", "ERROR")
                
                # Mark task as done
                account_queue.task_done()
                
                # Add delay between accounts to prevent rate limiting
                if accounts_processed > 0:
                    delay = random.uniform(2, 5)  # 2-5 second delay between accounts
                    if log_callback:
                        log_callback(f"[Account {accounts_processed}] Waiting {delay:.1f}s before next account...")
                    await asyncio.sleep(delay)
                
    except Exception as e:
        if log_callback:
            log_callback(f"Worker encountered a critical error: {e}", "ERROR")
    finally:
        if browser:
            try:
                await browser.close()
                if log_callback:
                    log_callback(f"Browser closed by worker. Final stats - Processed: {accounts_processed}, Successful: {accounts_successful}, Failed: {accounts_failed}")
            except Exception as e:
                if log_callback:
                    log_callback(f"Error closing browser: {e}", "ERROR")

async def run_warmup_automation(
    script_id,
    accounts_file,
    warmup_duration=DEFAULT_WARMUP_DURATION_MINUTES,
    activities=None,
    timing=None,
    visual_mode=False,
    log_callback=None,
    stop_callback=None
):
    """
    Main function to run the Instagram warmup automation.
    """
    logger.info(f"Starting warmup automation - Script ID: {script_id}")
    logger.info(f"Configuration - Duration: {warmup_duration} minutes, Visual mode: {visual_mode}")
    
    def default_log(message, level="INFO"):
        """Default logging function"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        # Also log to the logger
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING" or level == "WARN":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info(f"SUCCESS: {message}")
        else:
            logger.info(message)
    
    # Use default log if no callback provided
    if not log_callback:
        log_callback = default_log
    
    try:
        # Load accounts from file
        logger.info(f"Loading accounts from file: {accounts_file}")
        if accounts_file.endswith('.csv'):
            logger.debug("Reading CSV file")
            df = pd.read_csv(accounts_file)
        else:
            logger.debug("Reading Excel file")
            df = pd.read_excel(accounts_file)
        
        # Standardize column names
        df.columns = df.columns.str.strip().str.title()
        
        # Validate required columns
        if 'Username' not in df.columns or 'Password' not in df.columns:
            logger.error("Missing required columns in accounts file")
            raise ValueError("Accounts file must contain 'Username' and 'Password' columns")
        
        # Filter out empty rows
        accounts = []
        for _, row in df.iterrows():
            if pd.notna(row['Username']) and pd.notna(row['Password']):
                username = str(row['Username']).strip()
                accounts.append((username, str(row['Password']).strip()))
                logger.debug(f"Loaded account: {username}")
        
        if not accounts:
            logger.error("No valid accounts found in the file")
            raise ValueError("No valid accounts found in the file")
        
        logger.info(f"Successfully loaded {len(accounts)} accounts from file")
        if log_callback:
            log_callback(f"Loaded {len(accounts)} accounts from {accounts_file}")
        
        # Set default activities and timing if not provided
        if activities is None:
            logger.debug("Using default activities configuration")
            activities = {
                'feed_scroll': True,
                'watch_reels': True,
                'like_reels': True,
                'like_posts': True,
                'explore_page': True,
                'random_visits': True
            }
        
        if timing is None:
            timing = {
                'activity_delay': DEFAULT_ACTIVITY_DELAY_SECONDS,
                'scroll_attempts': DEFAULT_SCROLL_ATTEMPTS
            }
        
        config = {
            'warmup_duration': warmup_duration,
            'activities': activities,
            'timing': timing,
            'visual_mode': visual_mode
        }
        
        # Use all accounts dynamically (no concurrent limit)
        concurrent_browsers_to_use = len(accounts)
        if log_callback:
            log_callback(f"Using {concurrent_browsers_to_use} concurrent browsers (all accounts from file)")
        
        async with async_playwright() as playwright:
            total_accounts_processed = 0
            while total_accounts_processed < len(accounts):
                # Check if stop was requested
                if stop_callback and stop_callback():
                    if log_callback:
                        log_callback("Warmup automation stopped by user request.")
                    return True
                    
                current_batch = accounts[total_accounts_processed:total_accounts_processed + concurrent_browsers_to_use]
                if not current_batch:
                    if log_callback:
                        log_callback("No more accounts to process.")
                    break

                account_queue = asyncio.Queue()
                for acc in current_batch:
                    await account_queue.put(acc)

                if log_callback:
                    log_callback(f"Starting a new batch of {len(current_batch)} accounts.")
                workers = [asyncio.create_task(worker(playwright, account_queue, config, log_callback, stop_callback)) for _ in range(concurrent_browsers_to_use)]
                
                # Wait for either queue to be empty or stop signal
                while not account_queue.empty():
                    if stop_callback and stop_callback():
                        if log_callback:
                            log_callback("Stop requested - cancelling all workers immediately.")
                        # Cancel all workers immediately
                        for worker_task in workers:
                            worker_task.cancel()
                        # Wait briefly for tasks to cancel
                        await asyncio.gather(*workers, return_exceptions=True)
                        return True
                    await asyncio.sleep(0.5)  # Check every 500ms
                
                # All accounts in queue are picked up, now wait for workers to complete
                await account_queue.join()
                
                if log_callback:
                    log_callback("All accounts in the current batch processed. Cleaning up workers...")
                
                # Cancel any remaining workers
                for worker_task in workers:
                    if not worker_task.done():
                        worker_task.cancel()
                
                # Wait for all workers to finish with timeout
                try:
                    await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=5.0)
                except asyncio.TimeoutError:
                    if log_callback:
                        log_callback("Some workers took too long to stop, forcing shutdown.")
                
                total_accounts_processed += len(current_batch)
                if log_callback:
                    log_callback(f"Finished batch. Total accounts processed so far: {total_accounts_processed}/{len(accounts)}")
                
                if total_accounts_processed < len(accounts):
                    if log_callback:
                        log_callback("Pausing before starting the next batch...")
                    # Check for stop signal during the pause
                    for i in range(10):  # 10 seconds total, checking every second
                        if stop_callback and stop_callback():
                            if log_callback:
                                log_callback("Warmup automation stopped by user request during batch pause.")
                            return True
                        await asyncio.sleep(1)

        if log_callback:
            log_callback("All accounts processed. Warmup automation completed successfully!", "SUCCESS")
        return True
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error in warmup automation: {e}", "ERROR")
        return False
