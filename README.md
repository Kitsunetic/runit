# runit-parallel

*Rise from a cup of beer.* 🍺

A **simple, zero-dependency** command-line tool for scheduling multiple commands with limited resources, inspired by `GNU parallel`.


## 🚀 Installation

```sh
pip install git+https://github.com/Kitsunetic/runit.git
```


### ✨ Key Features

- Zero Dependencies: Built entirely with Python standard libraries.
- Resource Management: Keeps your limited resources (like GPUs) constantly working without idle time.
- Smart Expansion: Automatically expands ranges (e.g., 1:5) and reads arguments from text files (@args.txt).
- Timeout Support: Prevent hanging tasks with the --timeout option.
- Inline Execution: Pass commands directly without waiting for a prompt.



# 📖 How it Works

runit separates your inputs into two concepts:

1. Options (Resources): Prefixed with a single dash - (e.g., -g 0 1 2 3). These act as the "workers" (like threads, CPUs, or GPUs).
1. Parameters (Tasks): Prefixed with a double dash -- (e.g., --category a b c). These are the actual jobs to be processed.

Note: You can specify multiple groups for options and parameters, but the number of items within each type must match.


## 💻 Usage Example

Imagine you have 4 GPUs and 20 test scripts to run. You want to process all jobs using a single command, keeping the GPUs fully occupied.

### Step 1: Define Resources and Tasks

```sh
runit -g 0 1 2 3 \
    --category \
        a b c d e f g h i j \
        k l m n o p q r s t \
    --log logs/runit/{category}-{g}.log
```

### Step 2: Type the Command

After running the above, runit will prompt you to type the command to execute. Use `{g}` and `{category}` as placeholders.
(Multi-line commands are supported by appending `\` at the end of the line).

```sh
< type command >
CUDA_VISIBLE_DEVICES={g} python test_script.py \
--input {category}
```

### Alternative: Inline Command Execution

You can also pass the command directly in one line after a double dash `--`. This is highly recommended for shell scripts and automation:

```sh
runit -g 0 1 2 3 --category a b c d -- CUDA_VISIBLE_DEVICES={g} python test_script.py --input {category}
```


## 🛠 Advanced Features

### 1. Value Expansion (Pythonic Ranges)

You don't need to type every number manually. runit supports Python-like slicing syntax start:end or start:end:step.

```sh
# Expands to 1 2 3 4 5
runit -g 0 1 --id 1:5 -- echo GPU:{g} ID:{id}

# Expands to 10 8 6 4 2 (Negative step)
runit -g 0 1 --id 10:1:-2 -- echo GPU:{g} ID:{id}
```

### 2. Reading from a File

If you have a long list of parameters, save them in a text file (one per line) and use the @ prefix.

```sh
# Reads arguments line-by-line from targets.txt
runit -g 0 1 2 3 --target @targets.txt -- python process.py --target {target}
```

You can also split `@file` values across multiple machines with `--world_size` and `--rank`. Each machine processes only its own contiguous chunk from the file-backed parameter list.

```sh
# Machine 0 processes the first half, machine 1 processes the second half
runit -g 0 1 --world_size 2 --rank 0 --target @targets.txt -- python process.py --target {target}
runit -g 0 1 --world_size 2 --rank 1 --target @targets.txt -- python process.py --target {target}
```

### 3. Execution Timeout

Use --timeout <seconds> to automatically kill tasks that hang or take too long to complete.

```sh
# Automatically kills any task taking longer than 3600 seconds (1 hour)
runit -g 0 1 --dataset a b c --timeout 3600 -- python train.py --data {dataset}
```


# 🧪 Testing & Verification

### Scenario A: Basic Parallelism & Ranges

Run 5 tasks using 3 threads, where each task sleeps for 1-5 seconds.

```sh
python runit/runit.py -n 3 --val 1 2 1 2 1 2 -- python test_script.py -w {n} -a {val}
```

### Scenario B: Resource Mapping & Logging

Map tasks to specific "GPU" IDs and save output to log files.

```sh
python runit/runit.py -g 0 1 --task_id A B C D -- python test_script.py -w GPU_{g} -a 2
```

### Scenario C: Timeout Verification

Force a task to fail if it takes longer than 2 seconds.

```sh
python runit/runit.py -n 2 --val 1:3 -- python test_script.py -w {n} -a {val}
```
