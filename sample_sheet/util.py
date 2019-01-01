# pylint: disable=E0401
from typing import Any

__all__ = ['is_ipython_interpreter', 'maybe_render_markdown']


def is_ipython_interpreter() -> bool:  # pragma: no cover
    """Return if we are in an IPython interpreter or not."""
    import __main__ as main  # type: ignore

    return hasattr(main, '__IPYTHON__')


def maybe_render_markdown(string: str) -> Any:
    """Render a string as Markdown only if in an IPython interpreter."""
    if is_ipython_interpreter():  # pragma: no cover
        from IPython.display import Markdown  # type: ignore # noqa: E501

        return Markdown(string)
    else:
        return string
