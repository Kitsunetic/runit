#!/usr/bin/env python

import argparse
import math
import subprocess as sp
import sys
import threading
from collections import defaultdict
from pathlib import Path
from queue import Queue

EXIT_FLAG = 7150297589271389562308946091234730894710298437
q = Queue()
cmd = None


def getopt():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--log", type=str)
    # parser.add_argument("--cmd", type=str)
    args, unknown = parser.parse_known_args()

    param_group = defaultdict(list)
    opt_group = defaultdict(list)

    key, flag = None, True
    for k in unknown:
        if k.startswith("--"):
            key, flag = k[2:], True
        elif k.startswith("-"):
            key, flag = k[1:], False
        elif key is not None:
            if flag:
                param_group[key].append(k)
            else:
                opt_group[key].append(k)

    if not opt_group:
        our_print("need at least an option")
        exit(1)

    return args, param_group, opt_group


def our_print(*msgs, **kwargs):
    if msgs:
        msg = "\033[1;33;44m" + " ".join(msgs) + "\033[0m"
        print(msg, **kwargs)
    else:
        print(**kwargs)


def len_int(x):
    return math.ceil(math.log10(x + 1))


def print_param_group(pg):
    maxlen = max([len(k) for k in pg])
    for k, v in pg.items():
        our_print(("{k:%d}: {v}" % maxlen).format(k=k, v=v))


def check_param_group(pg):
    lens = [len(pg[k]) for k in pg]
    maxlen = max(lens)
    is_ok = [k == maxlen for k in lens]
    return all(is_ok)


def t_func(rank, args, **t_kwargs):
    while True:
        x = q.get()
        if x == EXIT_FLAG:
            break
        i, cmd, p_kwargs = x
        kwargs = {}
        kwargs.update(t_kwargs)
        kwargs.update(p_kwargs)

        cmd_t = cmd.format(**kwargs)
        l = len_int(args.n_params - 1)
        msg = "[thread {rank} [{i:0%dd}/{n_params:0%dd}]] {cmd_t}" % (l, l)
        our_print(msg.format(rank=rank, i=i + 1, n_params=args.n_params, cmd_t=cmd_t))

        outpipe = sys.stdout
        if args.log is not None:
            log_file = Path(args.log.format(**kwargs))
            if not log_file.parent.exists():
                log_file.parent.mkdir(parents=True, exist_ok=True)
            outpipe = open(log_file, "a")

        cmd_t = cmd_t.replace("\n", " ")
        outpipe.write(cmd_t)
        outpipe.flush()

        sp.run(cmd_t, shell=True, stdout=outpipe, stderr=outpipe, stdin=sp.DEVNULL)

        if outpipe != sys.stdout:
            outpipe.close()


def main():
    args, param_group, opt_group = getopt()
    our_print("< param groups >")
    print_param_group(param_group)
    if not check_param_group(param_group):
        our_print("The number of parameters is not equal")
        return
    n_params = args.n_params = max([len(k) for k in param_group.values()]) if param_group else 0

    our_print("< opt groups >")
    print_param_group(opt_group)
    if not check_param_group(opt_group):
        our_print("The number of options is not equal")
        return
    n_opt = args.n_opt = max([len(k) for k in opt_group.values()])

    # if args.cmd is not None:
    #     cmd = args.cmd
    # else:
    print()
    our_print("< type command >")
    x = input()
    cmd = [x]
    while x[-1] == "\\":
        cmd[-1] = cmd[-1][:-1]
        x = input()
        cmd.append(x)
    cmd = "\n".join(cmd)

    threads = []
    for i in range(n_opt):
        t_kwargs = {k: v[i] for k, v in opt_group.items()}
        t = threading.Thread(target=t_func, args=(i, args), kwargs=t_kwargs, daemon=True)
        threads.append(t)
        t.start()

    for i in range(n_params):
        p_kwargs = {k: v[i] for k, v in param_group.items()}
        q.put((i, cmd, p_kwargs))

    for t in threads:
        q.put(EXIT_FLAG)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
