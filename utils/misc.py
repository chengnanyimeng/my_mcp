def Deprecated(obj):
    """给类或方法打上__deprecation_warning__标记"""
    setattr(obj, "__deprecation_warning__", True)
    return obj