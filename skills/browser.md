# Playwright Browser Skill
Use this skill to fetch data from the internet. Write a Python script and execute it via `run_python_file`.

**CRITICAL RULES:**
1. ALWAYS default to `headless=False`, unless the user explicitly asks to use headless mode.
2. If you are using `headless=False`, then make sure to keep this at the end of the script `page.wait_for_event('close')` so that the user can interact with the browser later.
3. DO NOT use `google.com` for searches. It blocks bots. Use `https://html.duckduckgo.com/html/?q=YOUR+QUERY`.
4. DO NOT rely on specific CSS selectors (e.g., `page.locator('.temp')`). They will fail. Instead, extract the page content using BeautifulSoup and print the raw text.
5. Limit your printed output to 2000 characters to protect your context window.
6. Use aggresive stealth measures to avoid being flagged as a bot while browsing the internet.
7. Whatever scripts you write should be strictly in a `temp/Browser` folder.

**Bulletproof Template:**
```python
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import sys

def run():
    with sync_playwright() as p:
        # 1. Run headless by default
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"] # Strips the bot flag
        )
        context = browser.new_context(
            user_agent="Chrome/120.0.0.0",
            viewport={"width": 1920, "height": 1080}
        )
        page = browser.new_page()
        
        # 2. Navigate (Use DuckDuckGo for searches to avoid CAPTCHAs)
        target_url = '[https://html.duckduckgo.com/]()'
        try:
            page.goto(target_url, timeout=10000)
            page.wait_for_load_state('domcontentloaded')
        except Exception as e:
            print(f"Navigation failed: {e}")
            sys.exit(1)
            
        # 3. Extract pure text to avoid brittle CSS selectors
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator=' ', strip=True)
        
        # 4. Print the first 2000 chars for the agent to read
        print(text[:2000])
        page.wait_for_event('close')
        browser.close()

if __name__ == '__main__':
    run()
```
