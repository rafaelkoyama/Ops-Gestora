__all__ = ["os", "sys", "str_user"]

import os
import sys

from dotenv import load_dotenv

base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)

load_dotenv(os.path.join(base_path, ".env"))

str_user = os.getlogin()
