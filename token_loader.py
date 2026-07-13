import os

def load_tokens(filepath="tokens.txt"):
    env_tokens = os.getenv("DISCORD_TOKENS")
    if env_tokens:
        tokens = [t.strip() for t in env_tokens.splitlines() if t.strip()]
    elif os.path.exists(filepath):
        with open(filepath, "r") as f:
            tokens = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        raise FileNotFoundError("No tokens found.")
    
    # Basic validation: Discord bot tokens are 59–70 characters, contain three parts separated by dots
    valid = []
    for t in tokens:
        if len(t) > 50 and '.' in t and ':' not in t:  # rough check
            valid.append(t)
        else:
            print(f"[!] Skipping invalid token: {t[:10]}...")
    if not valid:
        raise ValueError("No valid tokens found after filtering. Check token.txt.")
    return valid
