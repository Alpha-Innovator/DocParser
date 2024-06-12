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
    "multline",
    "multline*",
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

table_of_contents = [
    "tableofcontents",
    "listoffigures",
    "listoftables",
    "listofalgorithms",
    "lstlistoflistings",
]

section_envs = [
    "chapter",
    "chapter*",
    "subsubsection",
    "subsubsection*",
    "subsection",
    "subsection*",
    "section*",
    "section",
]

table_envs = [
    "table",
    "table*",
    "wraptable",
]

tabular_envs = [
    "tabular",
    "tabular*",
    "tabularx",
    "tabulary",
    "tabu",
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
    "rotatebox",
    "rotatebox*",
]

algorithm_envs = [
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "program",
    "pseudocode",
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
] + footnote_envs

nonexpand_envs = [
    "thebibliography",
    "abstract",
]

text_envs = [
    "theorem",
    "observation",
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
    "acknowledgements",
    "flushleft",
    "flushright",
    "appendices",
    "IEEEproof",
    "widetext",
    "center",
    "quote",
]

# these envs will not cross columns, they always shows as a whole
one_column_envs = [
    "Table",
    "Caption",
    "Algorithm",
    "Footnote",
    "PaperTitle",
]

list_of_tables = [
    "tableofcontents",
    "listoffigures",
    "listoftables",
    "listofalgorithms",
]


# https://en.wikibooks.org/wiki/LaTeX/Labels_and_Cross-referencing
ref_commands = [
    "ref",
    "href",
    "eqref",
    "nameref",
    "autoref",
    "autoref*",
    "cref",
    "labelref",
    "pageref",
    "url",
    "hyperlink",
]
