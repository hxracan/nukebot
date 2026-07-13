import os

def load_tokens(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"{filepath} not found. Create it with one token per line.")
    with open(filepath, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]
