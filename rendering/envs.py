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
]

inline_math_envs = ["$", "math"]

section_envs = ["section", "subsection", "section*", "subsection*"]
table_envs = ["table", "table*", "wraptable"]
tabular_envs = ["tabular", "tabularx", "tabulary", "longtable"]
figure_envs = ["figure", "minipage"]
graphic_envs = ["centerline", "includegraphics", "subfigure"]
algorithm_envs = [
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "algorithm2e",
]
list_envs = ["itemize", "enumerate", "description"]
reference_envs = ["bibliography"]
caption_envs = ["caption", "caption*"]
footnote_envs = ["footnote", "footnote*", "footnote**"]
code_envs = ["verbatim", "verbatim*", "lstlisting", "lstinputlisting"]
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
    "Code",
    "Text",
    "Title",
    "Caption",
    "Footnote",
]


# these envs or commands will not be parsed
ignore_envs = ["cite", "eqref", "ref", "emph", "textbf", "textit"]


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
    "abstract",
]
