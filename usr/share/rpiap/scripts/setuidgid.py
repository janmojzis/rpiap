#!/usr/bin/env python3
  
import os, sys

os.setgid(int(os.environ["GID"]))
os.setuid(int(os.environ["UID"]))

os.execvp(sys.argv[1], sys.argv[1:])
sys.exit(111)
