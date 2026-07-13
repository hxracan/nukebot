import os

def load_tokens(filepath="tokens.txt"):
    raw = []
    env = os.getenv("DISCORD_TOKENS")
    if env:
        raw += [t.strip() for t in env.splitlines() if t.strip()]
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            raw += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not raw:
        raise RuntimeError("No tokens found. Set DISCORD_TOKENS or fill tokens.txt.")

    valid = []
    for token in raw:
        # Valid bot tokens are 59-70 characters, contain exactly two dots, no spaces
        if 50 <= len(token) <= 100 and token.count('.') == 2 and ' ' not in token:
            valid.append(token)
        else:
            print(f"[!] Skipping invalid token: {token[:15]}... (len={len(token)}, dots={token.count('.')})")
    
    print(f"[i] Loaded {len(valid)} valid token(s).")
    if not valid:
        raise ValueError("No valid bot tokens found. Get a real Bot Token from Discord Developer Portal.")
    return valid
