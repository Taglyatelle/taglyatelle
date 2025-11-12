"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()

pkg = "taglyatelle"

for path in sorted(Path(pkg).glob("**/*.py")):
    if path.name == "__init__.py":
        continue
        
    module_path = path.relative_to(pkg).with_suffix("")
    doc_path = path.relative_to(pkg).with_suffix(".md")
    full_doc_path = Path("references", doc_path)

    parts = list(module_path.parts)
    parts[-1] = f"{parts[-1]}.py"
    nav[parts] = doc_path

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = (
            pkg
            + "."
            + (".".join(module_path.parts))
        )
        print("::: " + ident, file=fd)

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("references/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
