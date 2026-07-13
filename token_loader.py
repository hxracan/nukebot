import os

def load_tokens():
    raw = os.getenv("DISCORD_TOKENS", "")
    if not raw:
        raise RuntimeError("DISCORD_TOKENS secret not set.")
    tokens = [t.strip() for t in raw.splitlines() if t.strip()]
    valid = []
    for t in tokens:
        if 50 <= len(t) <= 120 and t.count('.') == 2 and ' ' not in t:
            valid.append(t)
        else:
            print(f"[!] Skipping invalid: {t[:10]}... len={len(t)} dots={t.count('.')}")
    if not valid:
        raise ValueError("No valid bot tokens in DISCORD_TOKENS.")
    print(f"[i] {len(valid)} token(s) loaded.")
    return valid
