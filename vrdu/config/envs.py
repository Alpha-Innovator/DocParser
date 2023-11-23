math_envs = [
    "equation",
    "equation*",
    "align",
    "align*",
    "$$",
    "displaymath",  # see TexSoup.TexSoup.data.TexDisplayMathEnv
    "math",  # see TexSoup.TexSoup.data.TexMathEnv
    "gather",
    "gather*",
    "flalign",
    "falign*",
    "multiline",
    "multiline*",
    "alignat",
    "alignat*",
    "split",
    "eqnarray",
    "eqnarray*",
    "subequations",
    # chemical envs
    "chem",
    "chem*",
    "ceqn",
    "ceqn*",
]

inline_math_envs = [
    "$",
    "math",
]

section_envs = [
    "chapter",
    "chapter*",
    "section*",
    "section",
    "subsection",
    "subsection*",
]

table_envs = [
    "table",
    "table*",
    "wraptable",
]
tabular_envs = [
    "tabular",
    "tabularx",
    "tabulary",
    "longtable",
    "rotatebox",
]
figure_envs = [
    "figure",
    "minipage",
    "subfigure",
    "subfigure*",
]
graphic_envs = [
    "centerline",
    "includegraphics",
    "subfigure",
    "gridline",
]
algorithm_envs = [
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "algorithm2e",
]
code_envs = [
    "verbatim",
    "verbatim*",
    "lstlisting",
    "lstinputlisting",
]
algorithm_envs += code_envs

list_envs = [
    "itemize",
    "enumerate",
    "description",
]
reference_envs = [
    "bibliography",
]
caption_envs = [
    "caption",
    "caption*",
]
footnote_envs = [
    "footnote",
    "footnotetext",
    "tablefootnote",
]
non_text_envs = (
    math_envs
    + table_envs
    + figure_envs
    + reference_envs
    + caption_envs
    + algorithm_envs
    + list_envs
    + section_envs
    + ["abstract"]
    + ["bibliography"]
    + ["newcolumntype", "label"]  # corner case
)


complex_env_list = [
    "Text-EQ",
    "Algorithm",
    "Equation",
    "Table",
    "List",
    "Text",
    "Title",
    "Caption",
    "Footnote",
]


# these envs or commands will not be parsed
# https://journals.aas.org/natbib/
ignore_envs = [
    "cite",
    "citet",
    "citet*",
    "citep",
    "citep*",
    "citealt",
    "citealt*",
    "citealp",
    "citealp*",
    "citeauthor",
    "citeauthor*",
    "citeyear",
    "citeyearpar",
    "eqref",
    "ref",
    "emph",
    "textbf",
    "textit",
    "textsc",
    "textsl",
    "texttt",
    "textup",
    "textbf",
    "textit",
    "textsc",
    "textsl",
    "texttt",
    "textup",
    "message",
] + footnote_envs

nonexpand_envs = [
    "thebibliography",
    "abstract",
]

text_envs = [
    "theorem",
    "thm",
    "definition",
    "lemma",
    "remark",
    "corollary",
    "proposition",
    "example",
    "proof",
    "axiom",
    "conjecture",
    "exercise",
    "question",
    "solution",
    "quote",
    "note",
    "assumption",
    "fact",
    "observation",
    "justify",
    "subsubsection",
    "acknowledgements",
    "flushleft",
    "flushright",
]

# these envs will not cross columns, they always shows as a whole
one_column_envs = [
    "Table",
    "Caption",
    "Algorithm",
    "Footnote",
]
