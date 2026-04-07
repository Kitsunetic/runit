import tempfile
import unittest
from pathlib import Path
from unittest.mock import ANY, patch

from runit.runit import EXIT_FLAG, getopt, q, t_func


class GetoptTests(unittest.TestCase):
    def test_file_backed_param_chunking_with_rank_options(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.txt"
            targets.write_text("a\nb\nc\nd\n", encoding="utf-8")

            argv = [
                "runit",
                "-g",
                "0",
                "1",
                "--world_size",
                "2",
                "--rank",
                "1",
                "--target",
                f"@{targets}",
                "--",
                "echo",
                "{target}",
            ]

            with patch("sys.argv", argv):
                args, param_group, opt_group = getopt()

        self.assertEqual(args.world_size, 2)
        self.assertEqual(args.rank, 1)
        self.assertEqual(param_group["target"], ["c", "d"])
        self.assertEqual(opt_group["g"], ["0", "1"])

    def test_rank_options_after_file_backed_param_still_parse(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            targets = Path(tmpdir) / "targets.txt"
            targets.write_text("a\nb\nc\nd\n", encoding="utf-8")

            argv = [
                "runit",
                "-g",
                "0",
                "1",
                "--target",
                f"@{targets}",
                "--world_size",
                "2",
                "--rank",
                "1",
                "--",
                "echo",
                "{target}",
            ]

            with patch("sys.argv", argv):
                args, param_group, opt_group = getopt()

        self.assertEqual(args.world_size, 2)
        self.assertEqual(args.rank, 1)
        self.assertEqual(param_group["target"], ["c", "d"])
        self.assertEqual(opt_group["g"], ["0", "1"])

    def test_n_threads_creates_worker_axis_without_worker_option(self):
        argv = [
            "runit",
            "-n",
            "2",
            "--item",
            "x",
            "y",
            "--",
            "echo",
            "{item}",
        ]

        with patch("sys.argv", argv):
            args, param_group, opt_group = getopt()

        self.assertEqual(args.n_threads, 2)
        self.assertEqual(param_group["item"], ["x", "y"])
        self.assertEqual(opt_group["n"], ["0", "1"])

    def test_inline_command_parts_are_preserved(self):
        argv = [
            "runit",
            "-n",
            "1",
            "--item",
            "Walk In The Air Idle.fbx",
            "--",
            "python",
            "script.py",
            "--rel_path",
            "{item}",
        ]

        with patch("sys.argv", argv):
            args, _, _ = getopt()

        self.assertEqual(
            args.inline_cmd_parts,
            ["python", "script.py", "--rel_path", "{item}"],
        )


class ExecutionTests(unittest.TestCase):
    def test_inline_command_runs_placeholder_with_spaces_as_single_argument(self):
        args = type("Args", (), {"n_params": 1, "log": None, "timeout": None})()
        cmd_spec = ["python", "script.py", "--rel_path", "{item}"]

        with patch("runit.runit.sp.run") as mock_run:
            q.put((0, cmd_spec, {"item": "Walk In The Air Idle.fbx"}))
            q.put(EXIT_FLAG)
            t_func(0, args, n="0")

        mock_run.assert_called_once_with(
            ["python", "script.py", "--rel_path", "Walk In The Air Idle.fbx"],
            shell=False,
            stdout=ANY,
            stderr=ANY,
            stdin=ANY,
            timeout=None,
        )


if __name__ == "__main__":
    unittest.main()
