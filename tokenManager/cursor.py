import requests

class Cursor:

    models = [
        'claude-3-5-sonnet-20241022', 
        'claude-3-opus', 
        'claude-3.5-haiku', 
        'claude-3.5-sonnet', 
        "cursor-fast",
        "cursor-small",
        "deepseek-r1",
        "deepseek-v3",
        'gemini-2.0-flash', 
        'gemini-2.0-flash-exp', 
        'gemini-2.0-flash-thinking-exp', 
        'gemini-2.0-pro-exp', 
        'gpt-3.5-turbo', 
        'gpt-4', 
        'gpt-4-turbo-2024-04-09', 
        'gpt-4o', 
        'gpt-4o-mini', 
        'o1', 
        'o1-mini', 
        'o1-preview',
        "o3-mini"
    ]    
    
    @classmethod
    def get_remaining_balance(cls, token):
        user = token.split("%3A%3A")[0]
        url = f"https://www.cursor.com/api/usage?user={user}"

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"WorkosCursorSessionToken={token}"
        }
        response = requests.get(url, headers=headers)
        usage = response.json().get("gpt-4", None)
        if usage is None or "maxRequestUsage" not in usage or "numRequests" not in usage:
            return None
        return usage["maxRequestUsage"] - usage["numRequests"]

    @classmethod
    def get_trial_remaining_days(cls, token):
        url = f"https://www.cursor.com/api/auth/stripe"

        headers = {
            "Content-Type": "application/json",
            "Cookie": f"WorkosCursorSessionToken={token}"
        }
        response = requests.get(url, headers=headers)
        remaining_days = response.json().get("daysRemainingOnTrial", None)
        return remaining_days
