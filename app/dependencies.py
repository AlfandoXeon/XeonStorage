_services={}
def configure(**kwargs): _services.update(kwargs)
def get(name): return _services[name]
