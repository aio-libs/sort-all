import argparse
import ast
import warnings
from operator import attrgetter
from typing import List, Optional, Sequence, Union

from tokenize_rt import Offset, Token, src_to_tokens, tokens_to_src


def ast_parse(contents_text: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


class ValueVisitor(ast.NodeVisitor):
    def __init__(self, fname: str) -> None:
        self._fname = fname
        self._elts: List[Union[ast.Constant, ast.Str]] = []
        self._skip = False

    def _visit_elems(self, elts: List[ast.expr]) -> None:
        if self._skip:
            return
        if self._elts:
            self._skip = True
            self._elts = []
            print(
                f"{self._fname}:__all__ found "
                f"but it contains more than one list/set/tuple, skip sorting",
            )
            return
        new_elts: List[Union[ast.Constant, ast.Str]] = []
        for elt in elts:
            if not isinstance(elt, (ast.Constant, ast.Str)):
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
        self._elts = new_elts

    def visit_List(self, node: ast.List) -> None:
        self._visit_elems(node.elts)

    def visit_Tuple(self, node: ast.Tuple) -> None:
        self._visit_elems(node.elts)

    def visit_Set(self, node: ast.Set) -> None:
        self._visit_elems(node.elts)


class Visitor(ast.NodeVisitor):
    def __init__(self, fname: str) -> None:
        self._elts: List[Union[ast.Constant, ast.Str]] = []
        self._fname = fname
        self._skip = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        pass  # ignore nested assignments

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        pass  # ignore nested assignments

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        pass  # ignore nested assignments

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._skip:
            return
        found = False
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                found = True
                break
        if found:
            visitor = ValueVisitor(self._fname)
            visitor.visit(node.value)
            if self._elts:
                print(f"Multiple assignment to {self._fname}:__all__, skipping")
                self._skip = True
                self._elts = []
            self._elts = visitor._elts


def _fix_src(contents_text: str, fname: str) -> str:
    try:
        ast_obj = ast_parse(contents_text)
    except SyntaxError:
        return contents_text

    visitor = Visitor(fname)
    visitor.visit(ast_obj)
    elts = visitor._elts
    if not elts:
        return contents_text

    tokens = src_to_tokens(contents_text)

    start = Offset(elts[0].lineno, elts[0].col_offset)
    pre: List[Token] = []
    for tok in tokens:
        if tok.offset == start:
            break
        else:
            pre.append(tok)
    pre_txt = tokens_to_src(pre)

    end = Offset(elts[-1].end_lineno, elts[-1].end_col_offset)
    post: List[Token] = []
    for tok in reversed(tokens):
        post.append(tok)
        if tok.offset == end:
            post.reverse()
            break

    post_txt = tokens_to_src(post)

    if start.line == end.line:
        body_txt = ", ".join(
            f'"{elt.value}"' for elt in sorted(elts, key=attrgetter("value"))
        )
    else:
        body = tokens[len(pre) : -len(post)]
        for tok in body:
            if tok.name in ("INDENT", "UNIMPORTANT_WS"):
                indent = tok.src
                break
        else:
            indent = ""
        body_txt = ("\n" + indent).join(
            f'"{elt.value}",' for elt in sorted(elts, key=attrgetter("value"))
        )

    if body_txt.endswith(",") and post_txt.startswith(","):
        # drop double comma
        body_txt = body_txt[:-1]

    return pre_txt + body_txt + post_txt


def fix_file(filename: str) -> int:
    with open(filename, "rb") as f:
        contents_bytes = f.read()

    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f"{filename} is non-utf8 (not supported)")
        return 1

    new_content = _fix_src(contents_text, filename)
    if new_content != contents_text:
        print(f"Rewriting {filename}")
        with open(filename, "wb") as f:
            f.write(new_content.encode())
        return 1
    else:
        return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", nargs="*")
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= fix_file(filename)
    return retv


if __name__ == "__main__":
    exit(main())
