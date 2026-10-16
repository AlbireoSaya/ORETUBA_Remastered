from pathlib import Path

def resolve_exact_guest_path(request: bytes, allowed: dict[bytes, Path], workspace: Path) -> Path:
    """Resolve an explicitly approved byte-path mapping.

    Serial-validator use only; not a sandbox. TOCTOU is still possible.
    The allow-list and target ownership are the caller's responsibility.
    """
    if not isinstance(request, bytes) or b"\x00" in request:
        raise ValueError("request must be NUL-free bytes")
    if request not in allowed:
        raise ValueError("request is not in the allow-list")

    target = Path(allowed[request]).absolute()
    workspace_resolved = workspace.resolve(strict=True)
    if not workspace_resolved.is_dir():
        raise ValueError("workspace must be an existing directory")

    for path in (target, *target.parents):
        if path.is_symlink():
            raise ValueError("symlink in target path")
        if hasattr(path, "is_junction") and path.is_junction():
            raise ValueError("junction in target path")

    target_resolved = target.resolve()
    if not target_resolved.is_relative_to(workspace_resolved):
        raise ValueError("target resolves outside workspace")
    return target_resolved