# vrdu_data_process
This repository is used to process paper with `.tex` source files.

# Roadmap
- [ ] text,text-eq rendering
- [ ] table rendering (recursive)
- [ ] text-bb matching
- [ ] improved merge_bb
- [ ] `text.json` output


# Install
[TODO]

# Usage
```shell
./pipeline.sh path_to_paper
```
where directory contains all files (must contain a main `.tex` file) related to a paper.

the script then generates the bounding box of the following categories and their corresponding content (if there are text inside the bounding box):

the result is stored in the `output` directory, the structure is given as follows (`paper.tex` as main file):
```shell
path_to_paper
├── output
│   ├── original
│   │   ├── paper.pdf
│   │   ├── paper_page_0.jpg
│   │   ├── paper_page_1.jpg
│   ├── rendered
│   │   ├── paper_rendered.pdf
│   │   ├── paper_rendered_page_0.jpg
│   │   ├── paper_rendered_page_1.jpg
│   └── result
│       ├── annotation.json
│       ├── text.json
│       ├── paper_annotation_page_0.jpg
│       └── paper_annotation_page_1.jpg
```
- The `original` folder contains the original PDF of paper and the screenshot of each page of the paper, naming convention: `${tex_file_name}_page_${index}.jpg`
- The `rendered` folder contains the processed PDF and corresponding screenshot of each page of the paper, naming convention: `${tex_file_name}_rendered_page_${index}.jpg`
- The result contains three parts:

    1. the `annotation.json` gives the bounding box of each element in the given categories, it is represented as [COCO format](https://cocodataset.org/#format-data)
    2. the `text.json` gives the text (if there exists) inside each bounding box in `annotation.json`, the `id` in `text.json` is consistent with `annotation.json`.



# Category
each bounding box is classified into one the following category.

| index   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |  11 | 
| -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | ---------- | ---------- | ---------- |---------- |
| Content | Text  | Text-EQ  | Title  |  Caption  | Equation  |  List | Table | Figure | Algorithm | Footnote | Reference | Others | 

Explanation:  
[TODO]


# Pipeline


# Acknowledgements
This project is based on the following python packages:
- [Texsoup](https://texsoup.alvinwan.com/)
- [pdf2image](https://pypi.org/project/pdf2image/)
- [pdfminer.six](https://pdfminersix.readthedocs.io/en/latest/index.html)
