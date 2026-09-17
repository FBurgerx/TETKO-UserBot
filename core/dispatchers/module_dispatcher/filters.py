import re

def command_name(message):
    text = getattr(message, 'raw_text', '') or getattr(message, 'text', '') or ''
    return (text.split(maxsplit=1)[0][1:].lower() if text.startswith('.') else None)

def matches_prefix(message, prefix='.'):
    text = getattr(message, 'raw_text', '') or getattr(message, 'text', '') or ''
    return text.startswith(prefix)
