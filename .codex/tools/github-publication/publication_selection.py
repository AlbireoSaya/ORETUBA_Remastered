def publication_decision(path, config):
    from pathlib import PurePosixPath
    if not path or path.startswith("/") or "\\" in path or ":" in path:
        return False, "unsafe_path"
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return False, "unsafe_path"
    first, base = parts[0], parts[-1]
    denied = {c.casefold() for c in config.get("denied_components", [])}
    if any(p.casefold() in denied for p in parts):
        return False, "private_path"
    if first.casefold() in {r.casefold() for r in config.get("denied_roots", [])}:
        return False, "private_path"
    secret = {s.casefold() for s in config.get("secret_names", [])}
    if base.casefold() in secret or base.casefold().startswith(".env."):
        return False, "private_path"
    if path in config.get("root_files", []):
        return True, "root_config"
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in config.get("suffixes", []):
        return False, "binary_or_unsupported"
    if path.startswith("工程记录/"):
        if suffix == ".md" and any(t in base for t in config.get("record_tokens", [])):
            return True, "engineering_record"
        return False, "outside_scope"
    for prefix, reason in config.get("prefixes", {}).items():
        if path.startswith(prefix):
            return True, reason
    return False, "outside_scope"