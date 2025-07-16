import os
import re
import sys

import fitz

program_directory = os.path.dirname(os.path.realpath(sys.argv[0]))
regex = re.compile(r"(UP|DOWN)\d+°(?:R[\d.]+)?")


def get_bend_hits(pdf_path: str) -> int:
    pdf_path.replace("\\", "/")
    pdf_file = fitz.open(pdf_path)
    pages = list(range(pdf_file.page_count))
    page_lines = []
    for pg in range(pdf_file.page_count):
        if pg in pages:
            page = pdf_file[pg]
            page_lines.append(page.get_text("text").replace(" ", ""))
    all_text = "".join(page_lines)
    return len(regex.findall(all_text))
