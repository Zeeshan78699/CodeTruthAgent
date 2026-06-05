import os

def cleanup_temp_file(path):
    os.remove(path)
    return True
