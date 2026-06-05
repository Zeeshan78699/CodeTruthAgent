"""Module containing os.remove call."""

import os

def remove_temp_file(path):
    os.remove(path)
    return True
