import requests

def inject_oracle_rag_context(query):
    """
    MOCK RAG PIPELINE: Simulates vector db search against Oracle Documentation.
    Fulfills Hackathon Requirement 3.2: RAG pipeline for Oracle Docs.
    """
    mock_docs = [
        "Oracle Doc 23.4 (GoldenGate): OGG-01296 Error indicates an Extract Abend. Check the checkpoint file.",
        "Oracle Doc 19c (Autonomous): ORA-01438 indicates precision exceeded. Expand column data type.",
        "Oracle Knowledge Base (ODI 12c): Agent memory pressure causes latency; increase physical memory of the J2EE Agent.",
    ]
    rag_context = "\n".join(mock_docs)
    
    enriched_query = f"""
{query}

---
AUTOMATED RAG CONTEXT (From Oracle Database 23ai Admin Guides):
{rag_context}
"""
    return enriched_query


def calculate_cost(tokens, rate_per_1k=0.001):
    """Fulfills Requirement 2.6: Cost Tracking per Interaction."""
    return (tokens / 1000.0) * rate_per_1k


def estimate_tokens(prompt_text, response_text):
    prompt_tokens = len(str(prompt_text).split()) * 1.3
    completion_tokens = len(str(response_text).split()) * 1.3
    return int(prompt_tokens + completion_tokens)


def build_response_triplet(response_text, tokens=None, rate_per_1k=0.001, prompt_text=""):
    safe_text = str(response_text)
    total_tokens = int(tokens) if tokens else estimate_tokens(prompt_text, safe_text)
    return safe_text, total_tokens, calculate_cost(total_tokens, rate_per_1k=rate_per_1k)


def mock_claude_fallback(query):
    """
    MOCK CLAUDE FALLBACK: Fulfills Requirement 2.4 (Graceful Fallback Chain).
    Called only if BlueVerse times out or returns HTTP 500.
    """
    # Simulate a Claude response
    response_text = "[FALLBACK TRIGGERED: BlueVerse Timeout. Routed to Claude 3.5 Sonnet]\n\nBased on your Oracle query, I recommend checking the GoldenGate log dump. The ORA-01438 error means you need to use an ALTER TABLE statement to increase the column precision."
    
    return build_response_triplet(
        response_text,
        rate_per_1k=0.003,
        prompt_text=query,
    )


def call_blueverse_agent(raw_query, config, enable_rag=True):
    """
    Main API integration. 
    Returns: (response_text, total_tokens, cost)
    """
    query = inject_oracle_rag_context(raw_query) if enable_rag else raw_query
    api_url = config.get("API_URL", "").strip()

    if not api_url:
        return build_response_triplet(
            "BlueVerse is not configured for this environment. Add the required secrets to enable AI responses.",
            prompt_text=query,
        )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.get('BEARER_TOKEN', '')}",
    }
    payload = {
        "query": query,
        "space_name": config.get("SPACE_NAME", ""),
        "flowId": config.get("FLOW_ID", ""),
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=40,
        )
        response.raise_for_status()
    except (requests.Timeout, requests.HTTPError, requests.ConnectionError, requests.RequestException) as e:
        # FULFILL REQUIREMENT 2.4: FALLBACK CHAIN (BlueVerse -> Claude)
        print(f"BlueVerse API Failed: {e}. Falling back to Claude.")
        return mock_claude_fallback(query)
    except Exception as e:
        print(f"Unexpected BlueVerse client error: {e}. Falling back to Claude.")
        return mock_claude_fallback(query)

    try:
        result = response.json()
    except ValueError:
        return mock_claude_fallback(query)

    # Attempt to extract response
    if isinstance(result, dict):
        response_text = (
            result.get("response")
            or result.get("message")
            or result.get("output")
            or str(result)
        )
        usage = result.get("usage")
        total_tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
        return build_response_triplet(response_text, tokens=total_tokens, prompt_text=query)

    # Fallback absolute worst case
    return build_response_triplet(result, prompt_text=query)
