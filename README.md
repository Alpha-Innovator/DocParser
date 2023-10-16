# vrdu_data_process
This repository is used to process paper with `.tex` source files.

# Roadmap
- [ ] text-bb matching
- [ ] improved merge_bb
- [ ] `text.json` output


# Install
First create a conda environment (if Anaconda has not been installed, see [installtion](https://docs.anaconda.com/free/anaconda/install/index.html))
```shell
conda create --name vrdu 
```

Then activate the environment and install packages:
```shell
conda activate vrdu
conda install --file requirements.txt
```

# Usage
```shell
./pipeline.sh path_to_paper/paper.tex
```
where directory contains all files (must contain a main `.tex` file) related to a paper.

the script then generates the bounding box of the following categories and their corresponding content (if there are text inside the bounding box):

the result is stored in the `output` directory inside the `path_to_paper`, the structure is given as follows:
```shell
path_to_paper
├── output
│   ├── original
│   │   ├── paper.pdf
│   │   ├── paper_page_0.jpg
│   │   ├── paper_page_1.jpg
│   └── result
│       ├── layout_annotation.json
│       ├── text.json
│       ├── paper_annotation_page_0.jpg
│       └── paper_annotation_page_1.jpg
```
- The `original` folder contains the original PDF of paper and the screenshot of each page of the paper, naming convention: `${tex_file_name}_page_${index}.jpg`
- The result contains three parts:

    1. the `layout_annotation.json` gives the bounding box of each element in the given categories, it is represented as [COCO format](https://cocodataset.org/#format-data)
    2. the `text.json` gives the text (if there exists) inside each bounding box in `annotation.json`, the `id` in `text.json` is consistent with `annotation.json`.



# Category
each bounding box is classified into one the following category.

| index   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |  11 | 
| -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | ---------- | ---------- | ---------- |---------- |
| Content | Text  | Text-EQ  | Title  |  Caption  | Equation  |  List | Table | Figure | Algorithm | Footnote | Reference | Others | 

Explanation:  
`Text` refers to a paragraph of texts without no inline equations, while `Text-EQ` refers to text with equations


# Pipeline
1. Use `TexSoup` to parse the `.tex` source file into a `list`, whose elements may be `dict` or `str`
2. Use Rule-based method to render elements that belong to different categories. 
3. Compile the rendered `.tex` file  into PDF
4. Use `pdfminer` to generate candidate bounding boxes
5. Processing candidate bounding boxes (merge by rules)
6. Use `opencv` to identify the color of content in each bounding box and classify bounding boxes
7. Build the relationship between source file and the bounding boxes


# Update log
## 2023.10
- [x] release v0.1 that can handle algorithm, equation, table environments.

## 2023.09
- [x] extract elements in '.tex' files
- [x] fix environment with argument parsing error.
- [x] fix align environment rendering error
- [x] fix list environment parsing error


# Acknowledgements
This project is based on the following python packages:
- [Texsoup](https://texsoup.alvinwan.com/)
- [pdf2image](https://pypi.org/project/pdf2image/)
- [pdfminer.six](https://pdfminersix.readthedocs.io/en/latest/index.html)
