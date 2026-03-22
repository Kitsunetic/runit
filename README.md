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

You can also pass the command directly in one line using the `--cmd` argument or a double dash `--` separator. This is highly recommended for shell scripts and automation:

```sh
runit -g 0 1 2 3 --category a b c d -- CUDA_VISIBLE_DEVICES={g} python test_script.py --input {category}
```


## 🛠 Advanced Features

### 1. Value Expansion (Pythonic Ranges)

You don't need to type every number manually. runit supports Python-like slicing syntax start:end or start:end:step.

```sh
# Expands to 1 2 3 4 5
runit -g 0 1 --id 1:5 --cmd "echo GPU:{g} ID:{id}"

# Expands to 10 8 6 4 2 (Negative step)
runit -g 0 1 --id 10:1:-2 --cmd "echo GPU:{g} ID:{id}"
```

### 2. Reading from a File

If you have a long list of parameters, save them in a text file (one per line) and use the @ prefix.

```sh
# Reads arguments line-by-line from targets.txt
runit -g 0 1 2 3 --target @targets.txt --cmd "python process.py --target {target}"
```

### 3. Execution Timeout

Use --timeout <seconds> to automatically kill tasks that hang or take too long to complete.

```sh
# Automatically kills any task taking longer than 3600 seconds (1 hour)
runit -g 0 1 --dataset a b c --timeout 3600 --cmd "python train.py --data {dataset}"
```
