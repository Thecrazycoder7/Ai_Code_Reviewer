def to_google(fn: dict, content: dict) -> str:
    """Formats the content into Google Style docstrings."""
    lines = [content.get("summary", ""), ""]

    if fn.get("args"):
        lines.append("Args:")
        for a in fn["args"]:
            annot = a.get('annotation') or 'Any'
            desc = content.get('arg_descs', {}).get(a['name'], '')
            lines.append(f"    {a['name']} ({annot}): {desc}")

    if fn.get("returns"):
        lines.extend([
            "",
            "Returns:",
            f"    {fn['returns']}: {content.get('ret_desc', '')}"
        ])

    return "\n".join(lines)


def to_numpy(fn: dict, content: dict) -> str:
    """Formats the content into NumPy Style docstrings."""
    lines = [content.get("summary", ""), "", "Parameters", "----------"]

    for a in fn.get("args", []):
        annot = a.get('annotation') or 'Any'
        desc = content.get('arg_descs', {}).get(a['name'], '')
        lines.append(f"{a['name']} : {annot}")
        lines.append(f"    {desc}")

    if fn.get("returns"):
        lines.extend([
            "",
            "Returns",
            "-------",
            str(fn["returns"]),
            f"    {content.get('ret_desc', '')}"
        ])

    return "\n".join(lines)

def to_rest(fn: dict, content: dict) -> str:
    """Formats the content into reStructuredText (reST) Style docstrings."""
    lines = [content.get("summary", ""), ""]

    for a in fn.get("args", []):
        desc = content.get('arg_descs', {}).get(a['name'], '')
        annot = a.get('annotation') or 'Any'
        lines.append(f":param {a['name']}: {desc}")
        lines.append(f":type {a['name']}: {annot}")

    if fn.get("returns"):
        lines.append(f":returns: {content.get('ret_desc', '')}")
        lines.append(f":rtype: {fn['returns']}")

    return "\n".join(lines)