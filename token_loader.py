import os

def load_tokens(filepath="tokens.txt"):
    raw = []
    env = os.getenv("DISCORD_TOKENS")
    if env:
        raw += [t.strip() for t in env.splitlines() if t.strip()]
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw += [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not raw:
        raise RuntimeError("No tokens found. Put a bot token in tokens.txt or set DISCORD_TOKENS.")

    valid = []
    for token in raw:
        # Basic check: length ~72, contains two dots, no whitespace
        if 50 <= len(token) <= 120 and token.count('.') == 2 and ' ' not in token:
            valid.append(token)
        else:
            print(f"[!] Invalid token skipped: {token[:15]}... (len={len(token)}, dots={token.count('.')})")
    print(f"[i] Loaded {len(valid)} valid bot token(s).")
    if not valid:
        raise ValueError("All tokens failed validation. Ensure you copied a real Bot Token.")
    return valid
