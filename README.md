# vrdu_data_process
This repository is used to process paper with `.tex` source files.


# Installation
First create a conda environment (if Anaconda has not been installed, see [installation](https://docs.anaconda.com/free/anaconda/install/index.html))
```shell
conda create --name vrdu 
```

Then activate the environment and install packages:
```shell
conda activate vrdu
pip install -e .
```

# Usage
```python
python main.py --file_name path_to_paper/paper.tex
```
the script then generates the bounding box of the following categories and their corresponding content (if there are text inside the bounding box):
1. layout annotation, with a bounding box around each semantic element, such as table, text paragraph, equation, etc.
2. reading annotation, which is a pair that links the bounding box and corresponding latex source code.

the result is stored in the `path_to_paper/output/result`, the folder structure is given as follows:
```shell
path_to_paper
├── output
│   └── result
│       ├── layout_annotation.json
│       ├── text.json
│       ├── paper_annotation_page_0.jpg
│       └── paper_annotation_page_1.jpg
```
The result contains three parts:
1. the `layout_annotation.json` gives the bounding box of each element in the given categories, it is represented as [COCO format](https://cocodataset.org/#format-data)
2. the `reading_annotation.json` gives the source code of text (if there exists) inside each bounding box in `layout_annotation.json`.



# Category
each bounding box is classified into one the following category.

| Category   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |  11 | 
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |--- |
| Name | Algorithm  | Caption | Equation | Figure | Footnote | List | Others | Table | Text | Text-EQ | Title | Reference | 

Explanation:  
-  `Algorithm` contains Algorithm environment and Code listing environments;
-  `Caption` contains Figure caption, Table caption and Algorithm caption
-  `Equation` contains all display equations such as `equation`, `align` environments.
-  `List` contains `itemize`, `enumerate` and `description`.
-  `Others` Currently there is no element that is classified into Others
-  `Text` refers to a paragraph of texts without inline equations, 
-  `Text-EQ` refers to text with equations, such as `$a$`. 
-  `Title` contains section title, subsection title. Others titles are ignored.

For more details, see `config/envs.py`.

# Pipeline
1. Use `TexSoup` to parse the `.tex` source file into a `list`, whose elements may be `dict` or `str`
2. Use Rule-based method to render elements that belong to different categories. 
3. Compile the rendered `.tex` file  into PDF
4. Use `pdfminer` to generate candidate bounding boxes
5. Processing candidate bounding boxes (merge by rules)
6. Use `opencv` to identify the color of content in each bounding box and classify bounding boxes
7. Build the relationship between source file and the bounding boxes


# Update log
## 2023.11
- [x] release v0.2 that correctly annotate all environments.
    - [x] fix pdf figure bounding box generation error
    - [x] fix cross column environments bounding box generation error
    - [x] fix pdfminer cannot match source with bb error
    - [x] fix pdfminer cannot accurately generate bounding box error

    - [x] feat: add bb-source_code match algorithm 


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
- [arxiv_cleaner](https://github.com/elsa-lab/arxiv-cleaner.git)
