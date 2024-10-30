import argparse
import ast
import sys
import warnings
from collections.abc import Sequence
from operator import attrgetter
from typing import Optional

from tokenize_rt import Offset, Token, src_to_tokens, tokens_to_src


def ast_parse(contents_text: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


class BaseVisitor:
    def visit(self, root: ast.AST) -> None:
        nodes: Sequence[ast.AST]
        if isinstance(root, ast.Module):
            nodes = root.body
        else:
            nodes = [root]
        for node in nodes:
            method = "visit_" + node.__class__.__name__
            visitor = getattr(self, method, None)
            if visitor is not None:
                visitor(node)


class ValueVisitor(BaseVisitor):
    def __init__(self, fname: str) -> None:
        self._fname = fname
        self._elts: list[list[ast.Constant]] = []

    def _visit_elems(self, elts: list[ast.expr]) -> None:
        new_elts: list[ast.Constant] = []
        for elt in elts:
            if not isinstance(elt, ast.Constant):
                print(
                    f"{self._fname}:__all__ found "
                    f"but it has non-const element {ast.dump(elt)}, skip sorting",
                )
                return
            elif not isinstance(elt.value, str):
                # `__all__` has non-constant element in the container
                # Cannot process it
                print(
                    f"{self._fname}:__all__ found "
                    f"but it has non-string element {elt.value!r}, skip sorting",
                )
                return
            else:
                new_elts.append(elt)
        self._elts.append(new_elts)

    def visit_List(self, node: ast.List) -> None:
        self._visit_elems(node.elts)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self._visit_elems(node.elts)

    def visit_Set(self, node: ast.Set) -> None:
        self._visit_elems(node.elts)


class Visitor(BaseVisitor):
    def __init__(self, fname: str) -> None:
        self._elts: list[list[ast.Constant]] = []
        self._fname = fname

    def visit_ass(self, value: ast.AST, targets: list[ast.expr]) -> None:
        found = False
        for tgt in targets:
            if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                found = True
                break
        if found:
            visitor = ValueVisitor(self._fname)
            visitor.visit(value)
            self._elts.extend(visitor._elts)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit_ass(node.value, node.targets)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit_ass(node.value, [node.target])

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit_ass(node.value, [node.target])


def consume(tokens: list[Token], start: int, pos: Offset) -> tuple[str, int]:
    toks: list[Token] = []
    for idx, tok in enumerate(tokens[start:]):
        if tok.offset == pos:
            break
        else:
            toks.append(tok)
    return tokens_to_src(toks), start + idx


def scan(tokens: list[Token], start: int, pos: Offset) -> int:
    for idx, tok in enumerate(tokens[start:]):
        if tok.offset == pos:
            break
    return start + idx


def _fix_src(contents_text: str, fname: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = Visitor(fname)
    visitor.visit(ast_obj)
    if not visitor._elts:
        return contents_text

    tokens = src_to_tokens(contents_text)
    chunks = []
    idx = 0

    for elts in visitor._elts:
        if not elts:
            continue

        start = Offset(elts[0].lineno, elts[0].col_offset)
        chunk, idx = consume(tokens, idx, start)
        chunks.append(chunk)

        end = Offset(elts[-1].end_lineno, elts[-1].end_col_offset)
        idx2 = scan(tokens, idx, end)

        if start.line == end.line:
            chunk = ", ".join(
                f'"{elt.value}"' for elt in sorted(elts, key=attrgetter("value"))
            )
        else:
            for tok in tokens[idx:idx2]:
                if tok.name in ("INDENT", "UNIMPORTANT_WS"):
                    indent = tok.src
                    break
            else:
                indent = ""
            chunk = ("\n" + indent).join(
                f'"{elt.value}",' for elt in sorted(elts, key=attrgetter("value"))
            )

        if chunk.endswith(",") and tokens[idx2].src.startswith(","):
            # drop double comma
            chunk = chunk[:-1]

        chunks.append(chunk)
        idx = idx2

    chunk, idx = consume(tokens, idx, Offset(sys.maxsize, 0))
    chunks.append(chunk)
    return "".join(chunks)


def fix_file(filename: str, write: bool = True, error_on_fix: bool = True) -> int:
    with open(filename, "rb") as f:
        contents_bytes = f.read()

    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f"{filename} is non-utf8 (not supported)")
        return 1

    new_content = _fix_src(contents_text, filename)
    if new_content == contents_text:
        return 0

    retv = 1 if error_on_fix else 0

    if not write:
        print(f"Found unsorted {filename}")
        return retv

    print(f"Rewriting {filename}")
    with open(filename, "wb") as f:
        f.write(new_content.encode())

    return retv


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sort __all__ records alphabetically.")
    # add --check flag
    parser.add_argument(
        "--check",
        action="store_true",
        help="check the file for unsorted / unformatted imports and "
        "print them to the command line without modifying the file; "
        "return 0 when nothing would change and "
        "return 1 when the file would be reformatted.",
    )
    parser.add_argument(
        "--no-error-on-fix",
        action="store_true",
        help="return 0 even if errors are occurred during processing files",
    )
    parser.add_argument("filenames", nargs="*", help="Files to process")
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        if not filename.endswith((".py", ".pyx", ".pyi", ".pyd")):
            continue
        retv |= fix_file(
            filename,
            write=not args.check,
            error_on_fix=not args.no_error_on_fix,
        )
    return retv


if __name__ == "__main__":
    exit(main())
