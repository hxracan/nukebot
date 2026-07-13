def load_tokens(filepath):
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]
