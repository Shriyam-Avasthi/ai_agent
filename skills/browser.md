# Live Browser Interaction Skill
A persistent, anti-bot configured Chromium browser is currently running on Port 9222. You have three primary methods to interact with the web.
### 1. Navigation & Anti-Bot Strategy (CRITICAL)
Modern websites actively block bots. To navigate reliably, you MUST follow these rules:
*   **DO NOT** use Google.com. It will instantly block you.
*   **DO NOT** guess exact URLs for specific database items (like Codeforces contests or Jira tickets). Internal IDs do not match public IDs.
*   **DO** use search-assisted navigation via DuckDuckGo: `browser_navigate("https://html.duckduckgo.com/html/?q=Your+Query")`. 
*   **SEARCH HEURISTIC (The Pivot):** If the search results do not contain the direct link to the tool/problem you need, **do not keep searching**. Instead, click on the official pages like the Documentation page, or the github repo. These pages MOSTLY contain hyperlinks closely related to the search query, that's why they are ranked high on the search engine. Navigate there, then click the link you need.
*   **ADVANCED SEARCH:** Use advanced flags like `site:required_site.com` in your query to filter out YouTube videos and GitHub repos.

### 2. Standard Interaction (Token Optimized)
Use atomic tools to navigate the UI. When you call these tools, you will receive a screenshot and a highly optimized DOM Map of ONLY the visible, interactive elements.
*   `browser_navigate(url)`: Loads a page.
*   `browser_action(action_type, element_id, text)`: Interact with the UI. Valid actions: `click`, `type`, `hover`.
*   **Scrolling:** If an element is off-screen, it will NOT be in the DOM map. Use `browser_action('scroll_down')` to move down the page and refresh the DOM Map.

### 3. Targeted Extraction (Avoiding Token Bloat)
The DOM Map only shows buttons and links. It DOES NOT show long paragraphs, problem statements, or articles. 
*   If you dump the whole page HTML into your context window, you will fail.
*   To read static content, you MUST use the `browser_extract(selector)` tool.
*   Target your extraction! Use specific CSS selectors (e.g., `main`, `article`) to get exactly what you need without pulling in sidebars and footers.

### 4. Complex Scripting (The CDP Bridge)
If a visual element is hidden in a Canvas, requires drag-and-drop, or isn't caught by the standard tools, you can take manual control. Write a Python script using `run_python_file` to connect directly to the live window via CDP:
Note that write all these python scripts strictly in this folder: 'temp/browser'
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    # Connect to the ALREADY RUNNING browser on port 9222
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    page = browser.contexts[0].pages[0]
    
    # Execute complex, coordinate-based Playwright commands
    page.mouse.click(500, 300)
