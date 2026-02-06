"""ZAI (BigModel/Zhipu AI) API client for Reddit discovery using web_search tool."""

import json
import re
import sys
from typing import Any, Dict, List, Optional

from . import http


def _log_error(msg: str):
    """Log error to stderr."""
    sys.stderr.write(f"[ZAI REDDIT ERROR] {msg}\n")
    sys.stderr.flush()


# ZAI API endpoints
ZAI_CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# Depth configurations: (min, max) threads to request
DEPTH_CONFIG = {
    "quick": (15, 25),
    "default": (30, 50),
    "deep": (70, 100),
}

REDDIT_SEARCH_PROMPT = """Find Reddit discussion threads about: {topic}

STEP 1: EXTRACT THE CORE SUBJECT
Get the MAIN NOUN/PRODUCT/TOPIC:
- "best nano banana prompting practices" → "nano banana"
- "killer features of clawdbot" → "clawdbot"
- "top Claude Code skills" → "Claude Code"
DO NOT include "best", "top", "tips", "practices", "features" in your search.

STEP 2: SEARCH BROADLY
Search for the core subject on Reddit:
1. "[core subject] site:reddit.com"
2. "reddit [core subject]"
3. "[core subject] reddit"

Return as many relevant threads as you find. We filter by date server-side.

STEP 3: INCLUDE ALL MATCHES
- Include ALL threads about the core subject
- Set date to "YYYY-MM-DD" if you can determine it, otherwise null
- We verify dates and filter old content server-side
- DO NOT pre-filter aggressively - include anything relevant

REQUIRED: URLs must contain "/r/" AND "/comments/"
REJECT: developers.reddit.com, business.reddit.com

Find {min_items}-{max_items} threads. Return MORE rather than fewer.

Return JSON:
{{
  "items": [
    {{
      "title": "Thread title",
      "url": "https://www.reddit.com/r/sub/comments/xyz/title/",
      "subreddit": "subreddit_name",
      "date": "YYYY-MM-DD or null",
      "why_relevant": "Why relevant",
      "relevance": 0.85
    }}
  ]
}}"""


def _extract_core_subject(topic: str) -> str:
    """Extract core subject from verbose query for retry."""
    noise = ['best', 'top', 'how to', 'tips for', 'practices', 'features',
             'killer', 'guide', 'tutorial', 'recommendations', 'advice',
             'prompting', 'using', 'for', 'with', 'the', 'of', 'in', 'on']
    words = topic.lower().split()
    result = [w for w in words if w not in noise]
    return ' '.join(result[:3]) or topic  # Keep max 3 words


def search_reddit(
    api_key: str,
    model: str,
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    base_url: str = None,
    mock_response: Optional[Dict] = None,
    _retry: bool = False,
) -> Dict[str, Any]:
    """Search Reddit for relevant threads using ZAI API with web_search tool.

    Args:
        api_key: ZAI API key
        model: Model to use (e.g., glm-4, glm-4.7)
        topic: Search topic
        from_date: Start date (YYYY-MM-DD) - only include threads after this
        to_date: End date (YYYY-MM-DD) - only include threads before this
        depth: Research depth - "quick", "default", or "deep"
        base_url: Optional custom base URL for ZAI API
        mock_response: Mock response for testing

    Returns:
        Raw API response
    """
    if mock_response is not None:
        return mock_response

    min_items, max_items = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Adjust timeout based on depth
    timeout = 90 if depth == "quick" else 120 if depth == "default" else 180

    # Build the search query for ZAI's web_search tool
    search_query = f"{topic} site:reddit.com"

    # ZAI uses chat completions endpoint with web_search tool
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": REDDIT_SEARCH_PROMPT.format(
                    topic=topic,
                    from_date=from_date,
                    to_date=to_date,
                    min_items=min_items,
                    max_items=max_items,
                ),
            }
        ],
        "tools": [
            {
                "type": "web_search",
                "web_search": {
                    "enable": True,
                    "search_query": search_query,
                    "search_result": True,
                }
            }
        ],
    }

    url = base_url or ZAI_CHAT_URL
    return http.post(url, payload, headers=headers, timeout=timeout)


def parse_reddit_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse ZAI response to extract Reddit items.

    Args:
        response: Raw API response

    Returns:
        List of item dicts
    """
    items = []

    # Check for API errors first
    if "error" in response and response["error"]:
        error = response["error"]
        err_msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
        _log_error(f"ZAI API error: {err_msg}")
        if http.DEBUG:
            _log_error(f"Full error response: {json.dumps(response, indent=2)[:1000]}")
        return items

    # Try to find the output text from ZAI's chat completions format
    output_text = ""

    # ZAI chat completions format
    if "choices" in response:
        for choice in response["choices"]:
            if "message" in choice:
                message = choice["message"]
                # Check for content
                if "content" in message and message["content"]:
                    output_text = message["content"]
                    break
                # Check for tool_calls results
                if "tool_calls" in message:
                    for tool_call in message["tool_calls"]:
                        if tool_call.get("type") == "web_search":
                            # Web search results might be in the function response
                            if "function" in tool_call:
                                output_text = tool_call["function"].get("arguments", "")
                                break

    # Also check for direct output field (some API versions)
    if not output_text and "output" in response:
        output = response["output"]
        if isinstance(output, str):
            output_text = output
        elif isinstance(output, list):
            for item in output:
                if isinstance(item, dict):
                    if item.get("type") == "message":
                        content = item.get("content", [])
                        for c in content:
                            if isinstance(c, dict) and c.get("type") == "output_text":
                                output_text = c.get("text", "")
                                break
                    elif "text" in item:
                        output_text = item["text"]
                elif isinstance(item, str):
                    output_text = item
                if output_text:
                    break

    # Extract JSON from the LLM's content response
    if output_text:
        json_match = re.search(r'\{[\s\S]*"items"[\s\S]*\}', output_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                items = data.get("items", [])
            except json.JSONDecodeError:
                pass

    # If no items from LLM content, try to parse from web_search field
    # ZAI returns raw search results in a separate web_search field
    if not items and "web_search" in response:
        web_results = response["web_search"]
        if isinstance(web_results, list):
            for ws_item in web_results:
                if not isinstance(ws_item, dict):
                    continue

                link = ws_item.get("link", "")
                content = ws_item.get("content", "")

                # Look for Reddit URLs in the link or content
                reddit_urls = re.findall(
                    r'https?://(?:www\.)?reddit\.com/r/\w+/comments/\w+[^\s"\'<>]*',
                    link + " " + content
                )

                for reddit_url in reddit_urls:
                    # Extract subreddit from URL
                    sub_match = re.search(r'/r/(\w+)/', reddit_url)
                    subreddit = sub_match.group(1) if sub_match else ""

                    items.append({
                        "title": ws_item.get("title", ""),
                        "url": reddit_url.rstrip('/'),
                        "subreddit": subreddit,
                        "date": ws_item.get("publish_date"),
                        "why_relevant": content[:200] if content else "",
                        "relevance": 0.7,  # Default relevance for web_search items
                    })

                # Also check if the link itself is a Reddit URL
                if "reddit.com/r/" in link and "/comments/" in link:
                    sub_match = re.search(r'/r/(\w+)/', link)
                    subreddit = sub_match.group(1) if sub_match else ""

                    items.append({
                        "title": ws_item.get("title", ""),
                        "url": link.rstrip('/'),
                        "subreddit": subreddit,
                        "date": ws_item.get("publish_date"),
                        "why_relevant": content[:200] if content else "",
                        "relevance": 0.7,
                    })

    if not items and not output_text:
        if http.DEBUG:
            _log_error(f"No output text or web_search found in ZAI response. Keys present: {list(response.keys())}")
        return items

    # Validate and clean items, removing duplicates
    clean_items = []
    seen_urls = set()

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        url = item.get("url", "")
        if not url or "reddit.com" not in url:
            continue

        # Skip duplicates
        if url in seen_urls:
            continue
        seen_urls.add(url)

        clean_item = {
            "id": f"R{i+1}",
            "title": str(item.get("title", "")).strip(),
            "url": url,
            "subreddit": str(item.get("subreddit", "")).strip().lstrip("r/"),
            "date": item.get("date"),
            "why_relevant": str(item.get("why_relevant", "")).strip(),
            "relevance": min(1.0, max(0.0, float(item.get("relevance", 0.5)))),
        }

        # Validate date format
        if clean_item["date"]:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(clean_item["date"])):
                clean_item["date"] = None

        clean_items.append(clean_item)

    return clean_items
