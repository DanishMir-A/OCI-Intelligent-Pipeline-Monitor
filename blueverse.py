import requests


def call_blueverse_agent(query, config):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['BEARER_TOKEN']}",
    }
    payload = {
        "query": query,
        "space_name": config["SPACE_NAME"],
        "flowId": config["FLOW_ID"],
    }

    try:
        response = requests.post(
            config["API_URL"],
            headers=headers,
            json=payload,
            timeout=40,
        )
        response.raise_for_status()
    except requests.Timeout:
        return "BlueVerse request timed out after 40 seconds. Please try again."
    except requests.HTTPError:
        status = response.status_code if "response" in locals() else "unknown"
        body = ""
        if "response" in locals():
            body = response.text.strip()[:300]
        detail = f" Status: {status}."
        if body:
            detail += f" Response: {body}"
        return f"BlueVerse request failed.{detail}"
    except requests.RequestException as exc:
        return f"Unable to reach BlueVerse: {exc}"

    try:
        result = response.json()
    except ValueError:
        preview = response.text.strip()[:300]
        if not preview:
            preview = "Empty response body."
        return f"BlueVerse returned a non-JSON response: {preview}"

    if isinstance(result, dict):
        return (
            result.get("response")
            or result.get("message")
            or result.get("output")
            or str(result)
        )

    return str(result)
