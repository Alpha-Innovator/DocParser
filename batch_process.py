import os
import subprocess
import multiprocessing
import argparse


def run_script(file):
    os.system(f"python main.py --file_name {file}")


def main(start, end):
    path = os.path.expanduser("~/vrdu_data")

    tex_files = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(".tex"):
                continue
            if file.startswith("paper_"):
                continue
            tex_file = os.path.join(root, file)

            try:
                with open(tex_file) as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            if "\\begin{document}" not in content:
                continue

            tex_files.append(tex_file)

    for tex_file in sorted(tex_files)[start:end]:
        subprocess.run(["python", "main.py", "--file_name", tex_file])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--start",
        type=int,
        required=True,
    )
    parser.add_argument(
        "-e",
        "--end",
        type=int,
        required=True,
    )
    args = parser.parse_args()
    start = args.start
    end = args.end
    main(start, end)
