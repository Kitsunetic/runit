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


def split_into_rank_chunk(values, world_size, rank):
    if world_size == 1:
        return values

    n = len(values)
    base, rem = divmod(n, world_size)
    start = rank * base + min(rank, rem)
    end = start + base + (1 if rank < rem else 0)
    return values[start:end]


def expand_value(val, world_size=1, rank=0, chunk_file_values=False):
    if val.startswith("@"):
        file_path = Path(val[1:])
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                values = [line.strip() for line in f if line.strip()]
            if chunk_file_values:
                return split_into_rank_chunk(values, world_size, rank)
            return values

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
    inline_cmd = None

    if "--cmd" in argv:
        our_print("Error: `--cmd` is no longer supported. Put the command after `--`.")
        sys.exit(1)

    if "--" in argv:
        idx = argv.index("--")
        cmd_parts = argv[idx + 1 :]
        argv = argv[:idx]
        if not cmd_parts:
            our_print("Error: Command must follow `--`.")
            sys.exit(1)
        inline_cmd = " ".join(cmd_parts)

    parser = argparse.ArgumentParser(description="runit: scheduling multiple commands with limited resources")
    parser.add_argument(
        "-n", "--n-threads", type=int, help="Number of parallel threads (used if no other options are provided)"
    )
    parser.add_argument("--log", type=str, help="Log file path format")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds for each command")
    parser.add_argument("--world_size", type=int, default=1, help="Split @file parameter values into this many chunks")
    parser.add_argument("--rank", type=int, default=0, help="Process the chunk at this rank from @file parameter values")

    args, unknown = parser.parse_known_args(argv)
    args.inline_cmd = inline_cmd

    if args.world_size < 1:
        our_print("Error: --world_size must be >= 1.")
        sys.exit(1)
    if not 0 <= args.rank < args.world_size:
        our_print("Error: --rank must satisfy 0 <= rank < world_size.")
        sys.exit(1)

    param_group = defaultdict(list)
    opt_group = defaultdict(list)

    key, flag = None, True
    for k in unknown:
        if k.startswith("--"):
            key, flag = k[2:], True
        elif k.startswith("-"):
            key, flag = k[1:], False
        elif key is not None:
            expanded_vals = expand_value(k, args.world_size, args.rank, chunk_file_values=flag)
            if flag:
                param_group[key].extend(expanded_vals)
            else:
                opt_group[key].extend(expanded_vals)

    # 핵심 로직: 만약 옵션(-g 등)이 없고 -n이 지정되었다면 자동으로 생성
    if not opt_group and args.n_threads:
        opt_group["n"] = [str(i) for i in range(args.n_threads)]

    if not opt_group:
        our_print("Error: Need at least one option (e.g., -g 0 1) or -n <threads>")
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
    if not pg:
        return
    maxlen = max([len(k) for k in pg])
    for k, v in pg.items():
        display_v = f"[{v[0]}, {v[1]}, ..., {v[-1]}] (total: {len(v)})" if len(v) > 10 else str(v)
        our_print(("{k:%d}: {v}" % maxlen).format(k=k, v=display_v))


def check_param_group(pg):
    if not pg:
        return True
    lens = [len(pg[k]) for k in pg]
    return all(l == lens[0] for l in lens)


def t_func(rank, args, **t_kwargs):
    while True:
        x = q.get()
        if x == EXIT_FLAG:
            break

        i, cmd_str, p_kwargs = x
        full_kwargs = {**t_kwargs, **p_kwargs}

        try:
            cmd_t = cmd_str.format(**full_kwargs)
        except KeyError as e:
            our_print(f"Error: Missing placeholder {e} in command.")
            break

        l = len_int(args.n_params - 1)
        msg = "[thread {rank} [{i:0%dd}/{n_params:0%dd}]] {cmd_t}" % (l, l)
        our_print(msg.format(rank=rank, i=i + 1, n_params=args.n_params, cmd_t=cmd_t))

        outpipe = sys.stdout
        if args.log:
            log_file = Path(args.log.format(**full_kwargs))
            log_file.parent.mkdir(parents=True, exist_ok=True)
            outpipe = open(log_file, "a")

        try:
            sp.run(cmd_t.replace("\n", " "), shell=True, stdout=outpipe, stderr=outpipe, stdin=sp.DEVNULL, timeout=args.timeout)
        except sp.TimeoutExpired:
            our_print(f"[thread {rank}] TIMEOUT ({args.timeout}s): {cmd_t}")
        finally:
            if outpipe != sys.stdout:
                outpipe.close()


def main():
    args, param_group, opt_group = getopt()

    our_print("< param groups >")
    if param_group:
        print_param_group(param_group)
        if not check_param_group(param_group):
            our_print("Error: Parameter counts mismatch.")
            sys.exit(1)
    else:
        our_print("No parameters provided.")

    args.n_params = max([len(k) for k in param_group.values()]) if param_group else 0

    our_print("< opt groups >")
    print_param_group(opt_group)
    if not check_param_group(opt_group):
        our_print("Error: Option counts mismatch.")
        sys.exit(1)

    n_opt = max([len(k) for k in opt_group.values()])

    if args.inline_cmd:
        cmd_str = args.inline_cmd
    else:
        print()
        our_print("< type command >")
        lines = []
        while True:
            line = input()
            if not line:
                break
            if line.endswith("\\"):
                lines.append(line[:-1])
                continue
            lines.append(line)
            break
        cmd_str = "\n".join(lines)

    threads = []
    for i in range(n_opt):
        t_kwargs = {k: v[i] for k, v in opt_group.items()}
        t = threading.Thread(target=t_func, args=(i, args), kwargs=t_kwargs, daemon=True)
        threads.append(t)
        t.start()

    for i in range(args.n_params):
        p_kwargs = {k: v[i] for k, v in param_group.items()}
        q.put((i, cmd_str, p_kwargs))

    for _ in threads:
        q.put(EXIT_FLAG)
    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
