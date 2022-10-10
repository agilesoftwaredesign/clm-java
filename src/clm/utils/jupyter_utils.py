# %%
import logging
import re
from typing import Any, TYPE_CHECKING, TypeAlias

from nbformat import NotebookNode

# %%
if TYPE_CHECKING:
    # Make PyCharm happy, since it doesn't understand the pytest extensions to doctests.
    def getfixture(_name: str) -> Any:
        ...


# %%
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

# %%
Cell: TypeAlias = NotebookNode


# %%
def get_cell_type(cell: Cell) -> str:
    """Return the type of `cell`.

    >>> nb = getfixture("test_notebook")
    >>> get_cell_type(nb.cells[0])
    'markdown'
    >>> get_cell_type(nb.cells[1])
    'markdown'
    >>> get_cell_type(nb.cells[2])
    'code'
    >>> get_cell_type(nb.cells[2])
    'code'
    """

    return cell["cell_type"]


# %%
def get_tags(cell: Cell) -> list[str]:
    """Return the tags for `cell`.

    >>> nb = getfixture("test_notebook")
    >>> get_tags(nb.cells[0])
    []
    >>> get_tags(nb.cells[1])
    ['slide', 'other_tag']
    >>> get_tags(nb.cells[2])
    []
    >>> get_tags(nb.cells[3])
    ['keep']
    """

    return cell["metadata"].get("tags", [])


def set_tags(cell: Cell, tags: list["str"]) -> None:
    """Set the tags for `cell`.

    >>> nb = getfixture("test_notebook")
    >>> get_tags(nb.cells[0])
    []
    >>> set_tags(nb.cells[0], ["tag1", "tag2"])
    >>> get_tags(nb.cells[0])
    ['tag1', 'tag2']
    >>> set_tags(nb.cells[0], [])
    >>> get_tags(nb.cells[0])
    []
    """

    if tags:
        cell["metadata"]["tags"] = tags
    elif cell["metadata"].get("tags") is not None:
        del cell["metadata"]["tags"]


# %%
def has_tag(cell: Cell, tag: str) -> bool:
    """Returns whether a cell has a specific tag.

    >>> nb = getfixture("test_notebook")
    >>> has_tag(nb.cells[0], "tag1")
    False
    >>> has_tag(nb.cells[1], "slide")
    True
    >>> has_tag(nb.cells[1], "other_tag")
    True
    >>> has_tag(nb.cells[1], "tag1")
    False
    """

    return tag in get_tags(cell)


# %%
def get_cell_language(cell) -> str:
    """Return the language code for a cell.

    An empty language code means the cell has no specified language.

    >>> nb = getfixture("test_notebook")
    >>> get_cell_language(nb.cells[0])
    ''
    >>> get_cell_language(nb.cells[1])
    'en'
    """

    return cell["metadata"].get("lang", "")


# %%
# Tags that control the behavior of this cell in a slideshow
_SLIDE_TAGS = {"slide", "subslide", "notes"}
# Tags that prevent this cell from being publicly visible
_PRIVATE_TAGS = {"notes", "private"}
# Tags that may appear in any kind of cell
_EXPECTED_GENERIC_TAGS = _SLIDE_TAGS | _PRIVATE_TAGS
# Tags that may appear in code cells (in addition to slide and private tags)
_EXPECTED_CODE_TAGS = {"keep", "alt", "del"} | _EXPECTED_GENERIC_TAGS
# Tags that may appear in markdown cells (in addition to slide and private tags)
_EXPECTED_MARKDOWN_TAGS = {"notes"} | _EXPECTED_GENERIC_TAGS


# %%
def is_deleted_cell(cell: Cell):
    """Return whether a cell has been deleted.

    >>> is_deleted_cell(getfixture("deleted_cell"))
    True
    >>> is_deleted_cell(getfixture("markdown_cell"))
    False
    >>> is_deleted_cell(getfixture("code_cell"))
    False
    """
    return "del" in get_tags(cell)


# %%
def is_private_cell(cell: Cell):
    """Return whether a cell is only visible in private documents.

    >>> is_private_cell(getfixture("markdown_notes_cell"))
    True
    >>> is_private_cell(getfixture("markdown_cell"))
    False
    """
    return bool(_PRIVATE_TAGS.intersection(get_tags(cell)))


# %%
def is_public_cell(cell: Cell):
    """Return whether a cell is visible in public documents.

    >>> is_public_cell(getfixture("markdown_cell"))
    True
    >>> is_public_cell(getfixture("code_cell"))
    True
    >>> is_public_cell(getfixture("markdown_notes_cell"))
    False
    """
    return not is_private_cell(cell)


# %%
def is_alternate_solution(cell: Cell):
    """Return whether a cell is an alternate solution.

    Alternate solutions should be present in completed notebooks, but their cells should
    be completely removed from codealongs (not included as empty cells).

    >>> is_alternate_solution(getfixture("alternate_cell"))
    True
    >>> is_alternate_solution(getfixture("code_cell"))
    False
    """
    return "alt" in get_tags(cell)


# %%
def get_slide_tag(cell: Cell) -> str | None:
    """Return the slide tag of cell or `None` if it doesn't have one.

    >>> get_slide_tag(getfixture("markdown_slide_cell"))
    'slide'
    >>> get_slide_tag(getfixture("markdown_subslide_cell"))
    'subslide'
    >>> get_slide_tag(getfixture("markdown_cell")) is None
    True
    """
    tags = get_tags(cell)
    slide_tags = _SLIDE_TAGS.intersection(tags)
    if slide_tags:
        if len(slide_tags) > 1:
            logging.warning(
                f"Found more than one slide tag: {slide_tags}. Picking one at random."
            )
        return slide_tags.pop()
    else:
        return None


# %%
def is_cell_contents_included_in_codealongs(cell: Cell):
    """Return whether a cell is retained in codealongs.

    >>> is_cell_contents_included_in_codealongs(getfixture("markdown_cell"))
    True
    >>> is_cell_contents_included_in_codealongs(getfixture("kept_cell"))
    True
    >>> is_cell_contents_included_in_codealongs(getfixture("code_cell"))
    False
    """
    return get_cell_type(cell) != "code" or "keep" in get_tags(cell)


# %%
def should_cell_be_retained_for_language(cell: Cell, lang: str):
    """Return whether a cell should be retained for a particular language.

    Cells without language metadata should be retained for all languages, cells with
    language metadata should obviously only be included in their language.

    >>> should_cell_be_retained_for_language(getfixture("english_markdown_cell"), "en")
    True
    >>> should_cell_be_retained_for_language(getfixture("german_markdown_cell"), "de")
    True
    >>> should_cell_be_retained_for_language(getfixture("markdown_cell"), "en")
    True
    >>> should_cell_be_retained_for_language(getfixture("english_markdown_cell"), "de")
    False
    >>> should_cell_be_retained_for_language(getfixture("german_markdown_cell"), "en")
    False
    """
    cell_lang = get_cell_language(cell)
    return not cell_lang or cell_lang == lang


# %%
def warn_on_invalid_code_tags(tags):
    for tag in tags:
        if tag not in _EXPECTED_CODE_TAGS:
            logging.warning(f"Unknown tag for code cell: {tag!r}.")


# %%
def warn_on_invalid_markdown_tags(tags):
    for tag in tags:
        if tag not in _EXPECTED_MARKDOWN_TAGS:
            logging.warning(f"Unknown tag for markdown cell: {tag!r}.")


# %%
_PARENS_TO_REPLACE = "{}[]"
_REPLACEMENT_PARENS = "()" * (len(_PARENS_TO_REPLACE) // 2)
_CHARS_TO_REPLACE = "/\\$!'\"#%&<>*?+`|"
_REPLACEMENT_CHARS = "_" * len(_CHARS_TO_REPLACE)
_CHARS_TO_DELETE = ":"
_STRING_TRANSLATION_TABLE = str.maketrans(
    _PARENS_TO_REPLACE + _CHARS_TO_REPLACE,
    _REPLACEMENT_PARENS + _REPLACEMENT_CHARS,
    _CHARS_TO_DELETE,
)


# %%
def sanitize_file_name(text: str):
    return text.strip().translate(_STRING_TRANSLATION_TABLE)


# %%
TITLE_REGEX = re.compile(
    r"{{\s*header\s*\(\s*[\"'](.*)[\"']\s*,\s*[\"'](.*)[\"']\s*\)\s*}}"
)


# %%
def find_notebook_titles(text: str, default: str = "unnamed") -> dict[str, str]:
    """Find the titles from the source text of a notebook.

    >>> find_notebook_titles('{{ header("Deutsch", "English") }}')
    {'en': 'English', 'de': 'Deutsch'}
    >>> find_notebook_titles('{{header ( "Deutsch" ,"English" )}}')
    {'en': 'English', 'de': 'Deutsch'}
    >>> find_notebook_titles('{{ header("See: <>?Here!%$", "{/a/b\\\\c?}") }}')
    {'en': '(_a_b_c_)', 'de': 'See ___Here___'}
    >>> find_notebook_titles("Notebook without header.")
    {'en': 'unnamed', 'de': 'unnamed'}
    """
    match = TITLE_REGEX.search(text)
    if match:
        return {"en": sanitize_file_name(match[2]), "de": sanitize_file_name(match[1])}
    else:
        return {"en": default, "de": default}
