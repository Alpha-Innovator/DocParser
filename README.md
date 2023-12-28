# vrdu_data_process
This repository is used to process paper with `.tex` source files to obtain:
1. object detection results
2. latex source code - visual bounding box pairs
3. layout reading orders.


# Installation
## Step 1 Install package
First create a conda environment (if Anaconda has not been installed, see [installation](https://docs.anaconda.com/free/anaconda/install/index.html))
```shell
conda create --name vrdu python=3.8
```

Then activate the environment and install packages:
```shell
conda activate vrdu
pip install -e .
```

## Step 2 Install TexLive
To compile latex, we need to install **Tex Live Distribution**, where you can find installation guide on [this page](https://www.tug.org/texlive/).

For Ubuntu, we recommend install `texlive-full` by running the following command on terminal (Requires ~5.4GB disk space)
```shell
sudo apt-get install texlive-full 
``` 
this version avoids missing package error, to see differences among versions, see [Differences between texlive packages in Linux](https://tex.stackexchange.com/a/504566)

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
│       ├── reading_annotation.json
│       ├── ordering_annotation.json
│       ├── quality_report.json
│       ├── texts.json
│       ├── env_orders.json
│       ├── layout_info.json
│       ├── layout_metadata.json
│       ├── raw_parsed_data.json
│       ├── page_0.jpg
|       ├── page_1.jpg
|       ├── block_0.jpg
└─      └── block_1.jpg

```
The result contains three parts:  
1. Object detection result, which includes `layout_annotation.json` and `page_{n}.png`, the result is is represented as [COCO format](https://cocodataset.org/#format-data)
2. Reading detection result, which includes `reading_annotation.json` and `block_{n}.png`, it matches the bounding box and its original tex represented contents
3. Reading order result, which includes `ordering_annotation.json`. The reading order is represented via triple (`relationship`, `from`, `to`), indicates the relationship between the block with id `from` and the block with id `to`.
4. Debugging infos, this parts contains:
    - `texts.json`, it contains the original tex contents
    - `env_orders.json`, it is used to annotate reading orders
    - `layout_info.json`, it is the raw content of object detection result
    - `layout_metadata.json`, it contains the information about the paper layouts
    - `raw_parsed_data.json`, it contains the result of main content of the tex file parsed by `TexSoup`.

## Common issues
### 1. `latexpand` command running error
```
ValueError: Failed to run the command "latexpand --output="/tmp/arxiv_cleaner.46fp5l_e.latexpand_output/paper_original.tex" --fatal --out-encoding="encoding(UTF-8)"  "paper_original.tex""
Return code: 2
```
if this error occurs, please check the version of installed `latexpand` with
```
latexpand --help
```
in the last line of output will print the version. If the version is below $1.6$, then we need to upgrade it to $\geq1.6$, the simplest way is
1. go to [latexpand v1.6](https://gitlab.com/latexpand/latexpand/-/tags/v1.6) download the source code
2. use `sudo vim $(which latexpand)` to edit the content of `latexpand` script (`sudo` is necessary since `latexpand` usually locates in `/usr/bin`)
3. copy the content of `v1.6/latexpand` to the old version of `latexpand` (opened with vim)  

### 2. `pdf2image` error
```
pdf2image.exceptions.PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?
```
use the following command to install `poppler`:
```
sudo apt-get install poppler-utils
```
for details, see [reference](https://pdf2image.readthedocs.io/en/latest/installation.html#installing-poppler).

### 3. `path_to_paper/block_*****.pdf` not found
Usually, this means the rendering process destroys the original latex, therefore it is not compilable, the reason varies from case to case.


# Documentation
The documentation is built with [Sphinx](https://www.sphinx-doc.org/en/master/), to build documentation, run the following commands:
```
cd docs
sphinx-build . _build
```
then the documentations are listed in `docs/_build`, which can be viewed by open `index.html` with a browser.

# Category
each bounding box is classified into one the following category.

| Category   | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |  11 | 12 | 13 | 14|
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |--- |--- |--- |---|
| **Name** | Algorithm  | Caption | Equation | Figure | Footnote | List | Others | Table | Text | Text-EQ | Title | Reference | PaperTitle | Code | Abstract|
| **Super Category** | Algorithm  | Caption | Equation | Figure | Footnote | List | Others | Table | Text | Text | Title | Reference | Title | Algorithm | Text|

Explanation:  
-  `Algorithm` contains Algorithm environment 
-  `Code` contains listing environments
-  `Caption` contains Figure caption, Table caption and Algorithm caption
-  `Equation` contains all display equations such as `equation`, `align` environments.
-  `List` contains `itemize`, `enumerate` and `description`.
-  `Others` Currently there is no element that is classified into Others
-  `Text` refers to a paragraph of texts without inline equations, 
-  `Text-EQ` refers to text with equations, such as `$a$`. 
-  `Title` contains section title, subsection title. Others titles are ignored.
-  `PaperTitle` contains paper title.


For more details, see `config/envs.py`.

# Pipeline
1. Preprocess the original tex file (copy), this includes two substeps:
    - resolve inputs and clean comments with `arxiv_cleaner`
    - convert all pdf figures into png format
    - delete table of contents
2. render tex file, this process first call `TexSoup` to parse tex files into a list, then add a color to each semantic element. This process generates a bunch of tex files, each tex file is different with the original colored tex file in a small part 
3. Compile these tex files into PDFs and further transform the PDFs into png images.
4. Extract the layout metadata of PDF, so that one-column and multi-column can be classified.
5. Generating bounding box for each semantic elements, generation is composed of two methods:
    - For `Figure` elements, we use `PDFMiner` to get the bounding box
    - For other semantic elements, we use the difference of two images to get the bounding box
6. By linking the bounding box and its related latex source code, we obtain the reading annotations.
7. After processing, we remove all redundant files.

# Update log
## 2023.12
- [x] fix known bugs
- [x] add new categories
- [x] add quality report



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


# Known Issues
1. Some customized environments will not be annotated, for example, `\newtheorem{defn}[thm]{Definition}`. This can be solved by adding the customized environment to `envs.text_envs`, then the environment will be annotated.
2. Rendering error, this happens when we render a environment successfully, but we cannot compile the rendered tex file into a PDF. This is still an open problem.
3. Some figures such as `tikz` format, will not be correctly classified, this may cause further error.

# Acknowledgements
This project is based on the following python packages:
- [Texsoup](https://texsoup.alvinwan.com/)  
- [pdf2image](https://pypi.org/project/pdf2image/)  
- [pdfminer.six](https://pdfminersix.readthedocs.io/en/latest/index.html)  
- [arxiv_cleaner](https://github.com/elsa-lab/arxiv-cleaner.git)



# License
