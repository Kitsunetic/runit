"""
PYTHONPATH=`pwd` python runit/runit.py -c 0 1 --a 4 5 6 7 -- python test_script.py -a {a}
"""

import argparse
import sys
import time

print(sys.argv)

P = argparse.ArgumentParser()
P.add_argument("-a", type=int, default=0)
args = P.parse_args()
time.sleep(args.a)
print(args.a)
