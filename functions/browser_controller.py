import subprocess
import time
import base64
import json
from playwright.sync_api import sync_playwright

class BrowserController:
    def __init__(self, port=9222):
        self.port = port
        self.cdp_url = f"http://localhost:{port}"
        self.playwright = None
        self.browser = None
        self.page = None
        self.element_map = {}

    def _ensure_connection(self):
        """Connects to the daemon. If it's not running, launches it."""
        if self.page and not self.page.is_closed():
            return

        if not self.playwright:
            self.playwright = sync_playwright().start()

        try:
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.page = self.browser.contexts[0].pages[0]
        except Exception:
            print(f"Starting persistent browser daemon on port {self.port}...")
            # Launch Chromium directly as a background daemon (with Wayland GUI support)
            subprocess.Popen([
                "chromium", 
                f"--remote-debugging-port={self.port}",
                "--disable-blink-features=AutomationControlled",
                "--user-data-dir=/tmp/agent_browser_profile" # Keeps state/cookies!
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            time.sleep(3) # Wait for startup
            self.browser = self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.page = self.browser.contexts[0].pages[0]

    def _get_state(self):
        if self.page is None:
            return f"Error: Page is None."
        # Use a try-except because some heavy sites never reach pure 'networkidle'
        try:
            self.page.wait_for_load_state('networkidle', timeout=3000)
        except Exception:
            pass 

        # 1. Capture Multimodal Screenshot
        screenshot_bytes = self.page.screenshot(type="jpeg", quality=60)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        # 2. Inject JS to build the map instantly and tag elements
        js_code = """
        () => {
            let elements = document.querySelectorAll('button, a, input, select, textarea, [role="button"]');
            let mapText = [];
            let counter = 0;

            for (let el of elements) {
                let rect = el.getBoundingClientRect();
                
                // 1. Skip elements with no physical size
                if (rect.width === 0 || rect.height === 0) continue;

                // 2. Viewport Filtering: Skip elements far outside the current screen
                if (rect.top > window.innerHeight * 2 || rect.bottom < -window.innerHeight) continue;

                // 3. Extract text
                let text = el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('title') || '';
                text = text.trim().replace(/\\n/g, ' ');

                // 4. Skip useless/empty elements
                if (!text) continue;

                text = text.length > 45 ? text.substring(0, 45) + '...' : text;

                // 5. Inject a custom attribute for targeted clicking later
                let elementId = 'el_' + counter;
                el.setAttribute('data-agent-id', elementId);

                mapText.push(`[${elementId}] ${el.tagName.toUpperCase()}: ${text}`);
                counter++;

                // 6. Hard cap at 100 elements to prevent token explosions
                // if (counter >= 100) break;
            }
            return mapText.join('\\n');
        }
        """
        
        # This executes in ~50 milliseconds instead of 45 seconds
        dom_map = self.page.evaluate(js_code)
        
        full_map = f"--- PAGE TITLE: {self.page.title()} ---\n--- URL: {self.page.url} ---\n--- INTERACTIVE ELEMENTS (Viewport) ---\n{dom_map}"

        return json.dumps({
            "dom_map": full_map,
            "screenshot": None #screenshot_b64
        })

    
    def extract_text(self, selector: str = "body"):
        self._ensure_connection()
        if self.page is None:
            return f"Page is None"
        try:
            # Wait a moment for the selector to be present
            self.page.wait_for_selector(selector, timeout=5000)
            
            # Extract clean, inner text
            text = self.page.evaluate(f"""() => {{
                const el = document.querySelector('{selector}');
                return el ? el.innerText : 'Selector not found.';
            }}""")
            
            # Cap the output to protect the context window
            capped_text = text[:8000] + ("\n...[TRUNCATED]" if len(text) > 8000 else "")
            return json.dumps({"extracted_text": capped_text, "screenshot": None})
            
        except Exception as e:
            return json.dumps({"error": f"Extraction failed: {str(e)}", "screenshot": None})

    def navigate(self, url: str):
        self._ensure_connection()
        if self.page is None:
            return f"Error: Page is None."
        self.page.goto(url)
        return self._get_state()

    def action(self, action_type: str, element_id: str = "", text: str = ""):
        self._ensure_connection()
        if self.page is None:
            return f"Error: Page is None."
        try:
            # Handle Scrolling
            if action_type == 'scroll_down':
                self.page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
                self.page.wait_for_timeout(1000) # Wait for map to settle
                return self._get_state()
            elif action_type == 'scroll_up':
                self.page.evaluate("window.scrollBy(0, -window.innerHeight * 0.8)")
                self.page.wait_for_timeout(1000)
                return self._get_state()

            # Handle Element Interactions
            # We don't use a Python dict anymore; we query the DOM directly for our injected ID!
            locator = self.page.locator(f'[data-agent-id="{element_id}"]')

            if locator.count() == 0:
                return json.dumps({"error": f"Element {element_id} not found in current view. You may need to scroll.", "screenshot": None})

            el = locator.first
            
            # Ensure the browser scrolls to the element before acting
            el.scroll_into_view_if_needed()

            if action_type == 'click':
                el.click(timeout=5000)
            elif action_type == 'type':
                el.fill(text, timeout=5000)
            elif action_type == 'hover':
                el.hover(timeout=5000)

            return self._get_state()
        except Exception as e:
             return json.dumps({"error": f"Action failed: {str(e)}", "screenshot": None})

# Singleton instance
browser_controller_instance = BrowserController()
