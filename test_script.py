# test_script.py
import argparse
import time
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--val", type=int, default=1)
parser.add_argument("-w", "--worker", type=str, default="0")
args = parser.parse_args()

print(f"Worker {args.worker} starting task with value {args.val}")
time.sleep(args.val)
print(f"Worker {args.worker} finished value {args.val}")
