def process(items: list, config: dict, label: str) -> str:
    items.append('x')
    items.extend(['a','b'])
    items.sort()
    v = config.get('k','d')
    config.update({'n':'v'})
    u = label.upper()
    p = label.split('_')
    s = label.strip()
    return '_'.join(p)

def transform(d: dict) -> list:
    out = []
    for k, v in d.items():
        out.append(f'{k}={v}')
    out.sort()
    return out
