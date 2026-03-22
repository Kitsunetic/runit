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


def expand_value(val):
    """
    1. @파일명: 텍스트 파일의 각 줄을 읽어 리스트로 반환
    2. 시작:끝 또는 시작:끝:스텝: Pythonic하게 범위를 풀어서 리스트로 반환
    3. 일반 값: 그대로 리스트로 감싸서 반환
    """
    if val.startswith("@"):
        file_path = Path(val[1:])
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

    if ":" in val:
        parts = val.split(":")
        try:
            if len(parts) == 2:
                start, end = int(parts[0]), int(parts[1])
                step = 1 if start <= end else -1
                return [str(i) for i in range(start, end + step, step)]

            elif len(parts) == 3:
                start, end, step = int(parts[0]), int(parts[1]), int(parts[2])
                if step > 0:
                    return [str(i) for i in range(start, end + 1, step)]
                elif step < 0:
                    return [str(i) for i in range(start, end - 1, step)]
        except ValueError:
            pass

    return [val]


def getopt():
    argv = sys.argv[1:]
    cmd_from_dash = None

    if "--" in argv:
        idx = argv.index("--")
        cmd_parts = argv[idx + 1 :]
        argv = argv[:idx]
        cmd_from_dash = " ".join(cmd_parts)

    parser = argparse.ArgumentParser(description="runit: scheduling multiple commands with limited resources")
    # 기존에 있던 -n 파라미터는 데드 코드이므로 삭제되었습니다.
    parser.add_argument("--log", type=str, help="Log file path format")
    parser.add_argument("--cmd", type=str, help="Command to execute")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds for each command")

    args, unknown = parser.parse_known_args(argv)

    if cmd_from_dash:
        args.cmd = cmd_from_dash

    param_group = defaultdict(list)
    opt_group = defaultdict(list)

    key, flag = None, True
    for k in unknown:
        if k.startswith("--"):
            key, flag = k[2:], True
        elif k.startswith("-"):
            key, flag = k[1:], False
        elif key is not None:
            expanded_vals = expand_value(k)
            if flag:
                param_group[key].extend(expanded_vals)
            else:
                opt_group[key].extend(expanded_vals)

    if not opt_group:
        our_print("Error: Need at least one option (e.g., -g 0 1)")
        sys.exit(1)

    return args, param_group, opt_group


def our_print(*msgs, **kwargs):
    if msgs:
        msg = "\033[1;33;44m" + " ".join(msgs) + "\033[0m"
        print(msg, **kwargs)
    else:
        print(**kwargs)


def len_int(x):
    return math.ceil(math.log10(x + 1)) if x > 0 else 1


def print_param_group(pg):
    maxlen = max([len(k) for k in pg])
    for k, v in pg.items():
        if len(v) > 10:
            display_v = f"[{v[0]}, {v[1]}, ..., {v[-2]}, {v[-1]}] (total: {len(v)})"
        else:
            display_v = str(v)
        our_print(("{k:%d}: {v}" % maxlen).format(k=k, v=display_v))


def check_param_group(pg):
    if not pg:
        return True
    lens = [len(pg[k]) for k in pg]
    maxlen = max(lens)
    is_ok = [k == maxlen for k in lens]
    return all(is_ok)


def t_func(rank, args, **t_kwargs):
    while True:
        x = q.get()
        if x == EXIT_FLAG:
            break

        i, cmd_str, p_kwargs = x
        kwargs = {}
        kwargs.update(t_kwargs)
        kwargs.update(p_kwargs)

        cmd_t = cmd_str.format(**kwargs)
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
        outpipe.flush()

        try:
            sp.run(cmd_t, shell=True, stdout=outpipe, stderr=outpipe, stdin=sp.DEVNULL, timeout=args.timeout)
        except sp.TimeoutExpired:
            timeout_msg = f"\n[TIMEOUT WARNING] Command killed after {args.timeout} seconds!\n"
            our_print(f"[thread {rank}] TIMEOUT ({args.timeout}s): {cmd_t}")

            if outpipe != sys.stdout:
                outpipe.write(timeout_msg)
                outpipe.flush()

        if outpipe != sys.stdout:
            outpipe.close()


def main():
    args, param_group, opt_group = getopt()

    our_print("< param groups >")
    if param_group:
        print_param_group(param_group)
        if not check_param_group(param_group):
            our_print("Error: The number of parameters is not equal across groups.")
            sys.exit(1)
    else:
        our_print("No parameters provided.")

    args.n_params = max([len(k) for k in param_group.values()]) if param_group else 0

    our_print("< opt groups >")
    print_param_group(opt_group)
    if not check_param_group(opt_group):
        our_print("Error: The number of options is not equal across groups.")
        sys.exit(1)

    n_opt = max([len(k) for k in opt_group.values()])

    if args.cmd is not None:
        cmd_str = args.cmd
    else:
        print()
        our_print("< type command >")
        x = input()
        cmd_lines = [x]
        while x and x[-1] == "\\":
            cmd_lines[-1] = cmd_lines[-1][:-1]
            x = input()
            cmd_lines.append(x)
        cmd_str = "\n".join(cmd_lines)

    threads = []
    for i in range(n_opt):
        t_kwargs = {k: v[i] for k, v in opt_group.items()}
        t = threading.Thread(target=t_func, args=(i, args), kwargs=t_kwargs, daemon=True)
        threads.append(t)
        t.start()

    for i in range(args.n_params):
        p_kwargs = {k: v[i] for k, v in param_group.items()}
        q.put((i, cmd_str, p_kwargs))

    for t in threads:
        q.put(EXIT_FLAG)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
