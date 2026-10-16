def disable_registered_guest_threads(modules, handle):
    module = modules[handle]
    if module["static_tls_active"]:
        raise NotImplementedError("static TLS module")
    module["thread_notifications_disabled"] = True
    return 1
