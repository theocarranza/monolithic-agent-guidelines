"""Extract exact Markdown sections, including children and excluding fenced code."""
import re


def slug(text):
    return re.sub(r'[^\w\s-]', '', text.lower()).strip().replace(' ', '-')


def section(text, name):
    headings = []
    fence = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence) and not line[marker.end():].strip():
                fence = None
        elif fence is None:
            heading = re.match(r'^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
            if heading:
                headings.append((offset, len(heading.group(1)), slug(heading.group(2))))
        offset += len(line)
    matches = [i for i, heading in enumerate(headings) if heading[2] == slug(name)]
    if len(matches) != 1:
        raise ValueError('Section is missing or ambiguous: ' + name)
    index = matches[0]
    start, level, _ = headings[index]
    end = next((pos for pos, depth, _ in headings[index + 1:] if depth <= level), len(text))
    return text[start:end]
