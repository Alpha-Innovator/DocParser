math_envs = ["equation", "align", "equation*", "align*", "$$", "displaymath"]


section_envs = ["section", "subsection", "section*", "subsection*"]
table_envs = ["table", "table*"]
figure_envs = ["figure", "minipage"]
graphic_envs = ["centerline", "includegraphics", "subfigure"]
algorithm_envs = [
    "algorithm",
    "algorithm*",
    "algorithmic",
    "algorithmic*",
    "algorithm2e",
]
list_envs = ["itemize", "enumerate"]
reference_envs = ["bibliography"]
caption_envs = table_envs + figure_envs + algorithm_envs
footnote_envs = ["footnote", "footnote*", "footnote**"]
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
