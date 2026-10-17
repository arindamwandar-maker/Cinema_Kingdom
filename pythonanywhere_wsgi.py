# PythonAnywhere: Web tab -> WSGI configuration file.
# Replace the whole generated file with this, then click Reload.
# Change PROJECT_DIR if your folder is not named Cinema_Kingdom.

import os
import sys

PROJECT_DIR = os.path.expanduser("~/Cinema_Kingdom")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

os.chdir(PROJECT_DIR)

from web import app as application
