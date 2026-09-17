def check_native(module):
    return not getattr(module, "_tetko_translator", None) and not getattr(module, "_mcub_compat_release", False) and not getattr(module, "_hikka_compat", False)
