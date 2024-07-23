__all__ = ["os", "sys", "str_user"]

import os
import sys

from dotenv import load_dotenv

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, base_path)

load_dotenv(os.path.join(base_path, ".env"))

# --------------------------------------------------------------------


def append_paths():

    list_folders = ["btg_faas", "controlPanel", "risco", "tools"]

    for folder in list_folders:
        if os.path.exists(os.path.join(base_path, folder)):
            sys.path.insert(0, os.path.join(base_path, folder))


str_user = os.getlogin()
