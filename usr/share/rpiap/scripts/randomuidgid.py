#!/usr/bin/env python3
  
import os, sys, secrets

uid = 100000000 + 100000 * secrets.randbelow(1000) + os.getpid() % 100000

os.environ["UID"] = str(uid)
os.environ["GID"] = str(uid)

os.execvp(sys.argv[1], sys.argv[1:])
sys.exit(111)
