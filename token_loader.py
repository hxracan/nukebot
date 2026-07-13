import os

def load_tokens(filepath="tokens.txt"):
    """
    Returns a list of validated Discord bot tokens from:
    1. Environment variable DISCORD_TOKENS (multi-line)
    2. File tokens.txt (one per line)
    Only tokens that look like a bot token (long, two dots) are kept.
    """
    raw = []
    env = os.getenv("DISCORD_TOKENS")
    if env:
        raw += [t.strip() for t in env.splitlines() if t.strip()]
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            raw += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not raw:
        raise RuntimeError("No tokens found in DISCORD_TOKENS or tokens.txt")

    valid = []
    for token in raw:
        # Bot tokens are ~72 characters, three parts separated by dots, no spaces
        if 50 <= len(token) <= 100 and token.count('.') == 2 and ' ' not in token:
            valid.append(token)
        else:
            print(f"[!] Skipping invalid token: {token[:15]}...")
    if not valid:
        raise ValueError("No valid bot tokens. Get a real bot token from Discord Developer Portal.")
    return valid
