def read_file_content(file_path, max_size=1000000):
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            content = f.read(max_size + 1)
            if len(content) > max_size:
                return content[:max_size] + '... [Truncated]'
            return content
    except (UnicodeDecodeError, OSError):
        return '[Content Unreadable]'
