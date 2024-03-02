# runit

Rise form ~ashes~a cup of bear.

A **simple** command line tool for scheduling multiple commands with limited resources similar to `GNU parallel`.




# Install

<!-- pip install git+https://github.com/Kitsunetic/runit.git -->
```sh
pip install runit-parallel
```



# Example

For example, I have 4 GPUs and 20 test scripts to execute.
Each the script consumes arbitrary time, and need a GPU.
I want to process all the jobs with only single command, and to make the GPUs work constantly without rest.

TL;DR

```sh
runit -g 0 1 2 3 \
    --category \
        a b c d e f g h i j \
        k l m n o p q r s t \
    --log logs/runit/{category}-{g}.log

---

< param groups >
category: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
< opt groups >
g: ['0', '1', '2', '3']
```

Then, type a command to run.
Multi-line command is available by attaching `\`.

```sh
< type command >
CUDA_VISIBLE_DEVICES={g} python test_script.py \
--input {category}

---

[thread 3 [01/20]] CUDA_VISIBLE_DEVICES=3 python test_script.py --input b
[thread 1 [02/20]] CUDA_VISIBLE_DEVICES=1 python test_script.py --input c
[thread 2 [03/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input d
[thread 0 [04/20]] CUDA_VISIBLE_DEVICES=0 python test_script.py --input h

---
As soon as the running task is finished, the following tasks continue to run.

[thread 2 [05/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input e
[thread 1 [06/20]] CUDA_VISIBLE_DEVICES=1 python test_script.py --input f
[thread 2 [07/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input g
[thread 3 [08/20]] CUDA_VISIBLE_DEVICES=3 python test_script.py --input i
[thread 2 [09/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input j
[thread 0 [10/20]] CUDA_VISIBLE_DEVICES=0 python test_script.py --input k
[thread 2 [11/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input l
[thread 2 [12/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input m
[thread 1 [13/20]] CUDA_VISIBLE_DEVICES=1 python test_script.py --input n
[thread 3 [14/20]] CUDA_VISIBLE_DEVICES=3 python test_script.py --input o
[thread 0 [15/20]] CUDA_VISIBLE_DEVICES=0 python test_script.py --input p
[thread 0 [16/20]] CUDA_VISIBLE_DEVICES=0 python test_script.py --input q
[thread 3 [17/20]] CUDA_VISIBLE_DEVICES=3 python test_script.py --input r
[thread 1 [18/20]] CUDA_VISIBLE_DEVICES=1 python test_script.py --input s
[thread 0 [19/20]] CUDA_VISIBLE_DEVICES=0 python test_script.py --input t
[thread 2 [20/20]] CUDA_VISIBLE_DEVICES=2 python test_script.py --input t
```

- opt (option) group: list of the resources (such as GPU, CPU, e.t.c.). \
The option can be set with a `-` (e.g. `-g 1 2 3 4`, `-cpu 0,1 2,3 4,5 6,7`). \
Multiple options is possible but every option must have same number.
- param groups: list of the parameters. \
The parameters can be set with two `--` (e.g. `--docu 1.txt 2.txt 3.txt 4.txt`). \
Multiple options is possible but every params must have same number.
- `--log`: path to save logs. Log file path can contain opt and param \
(e.g. `--log save/to/logs/logname_{g}_{cpu}_{docu}.log`)




