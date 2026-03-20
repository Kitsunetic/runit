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


def expand_value(val):
    """
    1. @파일명: 텍스트 파일의 각 줄을 읽어 리스트로 반환
    2. 시작:끝 또는 시작:끝:스텝: Pythonic하게 범위를 풀어서 리스트로 반환
    3. 일반 값: 그대로 리스트로 감싸서 반환
    """
    # 1. 파일에서 읽기 (@파일명)
    if val.startswith("@"):
        file_path = Path(val[1:])
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

    # 2. 파이썬 슬라이싱 스타일 범위 및 스텝 처리 (시작:끝 또는 시작:끝:스텝)
    if ":" in val:
        parts = val.split(":")
        try:
            # 시작:끝 (예: 1:80) -> 스텝 기본값 1
            if len(parts) == 2:
                start, end = int(parts[0]), int(parts[1])
                # 역방향도 지원
                step = 1 if start <= end else -1
                return [str(i) for i in range(start, end + step, step)]

            # 시작:끝:스텝 (예: 0:80000:1000)
            elif len(parts) == 3:
                start, end, step = int(parts[0]), int(parts[1]), int(parts[2])
                # CLI 직관성을 위해 끝값(end)을 포함하도록 처리
                if step > 0:
                    return [str(i) for i in range(start, end + 1, step)]
                elif step < 0:
                    return [str(i) for i in range(start, end - 1, step)]
        except ValueError:
            # 숫자로 변환할 수 없는 문자열(예: 시간 형식 12:30:00)이 섞여 있으면 무시하고 원본 반환
            pass

    # 3. 위 조건에 해당하지 않는 일반 값이면 그대로 반환
    return [val]


def getopt():
    # 1. Manually handle the '--' separator
    argv = sys.argv[1:]
    cmd_from_dash = None

    if "--" in argv:
        idx = argv.index("--")
        # Everything after '--' is the command
        cmd_parts = argv[idx + 1 :]
        # Everything before '--' are runit args
        argv = argv[:idx]
        # Join command parts back into a string
        cmd_from_dash = " ".join(cmd_parts)

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--log", type=str)
    parser.add_argument("--cmd", type=str)

    # 2. Pass the sliced argv explicitly to parse_known_args
    args, unknown = parser.parse_known_args(argv)

    # 3. If we found a command after '--', assign it to args.cmd
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
            # 확장된 값들을 extend로 이어 붙임
            expanded_vals = expand_value(k)
            if flag:
                param_group[key].extend(expanded_vals)
            else:
                opt_group[key].extend(expanded_vals)

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
        # 리스트가 너무 길면 터미널 출력이 지저분해지므로 앞뒤 일부만 출력하도록 개선할 수도 있지만, 우선 유지합니다.
        if len(v) > 10:
            display_v = f"[{v[0]}, {v[1]}, ..., {v[-2]}, {v[-1]}] (total: {len(v)})"
        else:
            display_v = str(v)
        our_print(("{k:%d}: {v}" % maxlen).format(k=k, v=display_v))


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
    print("hihi")

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

    if args.cmd is not None:
        cmd = args.cmd
    else:
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
