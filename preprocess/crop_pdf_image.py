import subprocess
import os
import re


def crop_pdf_image(tex_file):
    path = os.path.dirname(tex_file)
    with open(tex_file) as f:
        file_content = f.read()

    includegraphics_pattern = r"\\includegraphics\{(.*?)\}"
    for match_str in re.finditer(includegraphics_pattern, file_content):
        pdf_name = match_str.group(1)
        if not match_str.endswith(".pdf"):
            continue
        pdf_graphic = os.path.join(path, pdf_name)
        subprocess.run(["pdfcrop", pdf_graphic, pdf_graphic])
