import os
import subprocess
import argparse
import random
from multiprocessing import Pool


def extract_tex_files(path):
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
    return tex_files


def run_process(tex_file):
    path = os.path.dirname(tex_file)
    result_path = os.path.join(path, "output/result")
    quality_report_file = os.path.join(result_path, "quality_report.json")
    if os.path.exists(quality_report_file):
        # this paper has been processed
        return
    subprocess.run(["python", "main.py", "--file_name", tex_file])


def main(directory, processes=60):
    path = os.path.expanduser(directory)
    tex_files = extract_tex_files(path)
    random.shuffle(tex_files)

    p = Pool(processes)

    for tex_file in tex_files:
        p.apply_async(run_process, args=(tex_file,))
    
    p.close()
    p.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
    )
    args = parser.parse_args()

    main(args.directory)
