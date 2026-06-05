def load_config_file(path):
    with open(path, 'r') as f:
        contents = f.read()
    return contents
