from __future__ import annotations

import ast
import json
import re
from typing import Any


def strip_bom(text: str) -> str:
    return (text or "").lstrip("\ufeff").strip()


def strip_markdown_fence(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json|JSON)?\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text


def extract_largest_json_region(text: str) -> str:
    text = text.strip()
    object_candidate = _extract_balanced_region(text, "{", "}")
    array_candidate = _extract_balanced_region(text, "[", "]")

    if object_candidate and array_candidate:
        return object_candidate if len(object_candidate) >= len(array_candidate) else array_candidate
    if object_candidate:
        return object_candidate
    if array_candidate:
        return array_candidate
    return text


def _extract_balanced_region(text: str, open_char: str, close_char: str) -> str | None:
    best: str | None = None
    for start, char in enumerate(text):
        if char != open_char:
            continue

        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            current = text[index]
            if escaped:
                escaped = False
                continue
            if current == "\\":
                escaped = True
                continue
            if current == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if current == open_char:
                depth += 1
            elif current == close_char:
                depth -= 1
                if depth == 0:
                    candidate = text[start:index + 1]
                    if best is None or len(candidate) > len(best):
                        best = candidate
                    break
    return best


def remove_trailing_commas(text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def replace_python_literals(text: str) -> str:
    replacements = {"True": "true", "False": "false", "None": "null"}
    return _replace_identifiers_outside_strings(text, replacements)


def quote_unquoted_keys(text: str) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0

    while index < len(text):
        char = text[index]
        if escaped:
            result.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            result.append(char)
            escaped = True
            index += 1
            continue
        if char == '"':
            result.append(char)
            in_string = not in_string
            index += 1
            continue

        if not in_string and char in "{,":
            result.append(char)
            index += 1
            start = index
            while index < len(text) and text[index].isspace():
                result.append(text[index])
                index += 1

            key_start = index
            if index < len(text) and (text[index].isalpha() or text[index] == "_"):
                index += 1
                while index < len(text) and (text[index].isalnum() or text[index] == "_"):
                    index += 1
                key = text[key_start:index]
                whitespace_start = index
                while index < len(text) and text[index].isspace():
                    index += 1
                if index < len(text) and text[index] == ":":
                    result.append(f'"{key}"')
                    result.append(text[whitespace_start:index])
                    continue

            result.append(text[key_start:index])
            if index == start:
                continue
            continue

        result.append(char)
        index += 1

    return "".join(result)


def escape_control_chars_in_strings(text: str) -> str:
    repaired: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if escaped:
            repaired.append(char)
            escaped = False
            continue
        if char == "\\":
            repaired.append(char)
            escaped = True
            continue
        if char == '"':
            repaired.append(char)
            in_string = not in_string
            continue
        if in_string and char == "\n":
            repaired.append("\\n")
            continue
        if in_string and char == "\r":
            repaired.append("\\r")
            continue
        if in_string and char == "\t":
            repaired.append("\\t")
            continue
        repaired.append(char)
    return "".join(repaired)


def escape_raw_content_field(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        prefix = match.group(1)
        content = match.group(2)
        suffix = match.group(3)
        return f"{prefix}{json.dumps(content, ensure_ascii=False)}{suffix}"

    return re.sub(
        r'("content"\s*:\s*)"(.*)"(\s*,\s*"(?:overwrite|expected_replacements|line|old_text|new_text|path|trailing_newline)"\s*:)',
        replace,
        text,
        flags=re.DOTALL,
    )


def balance_trailing_delimiters(text: str) -> str:
    stack: list[str] = []
    in_string = False
    escaped = False
    for char in text:
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char in "{[":
            stack.append(char)
        elif char == "}" and stack and stack[-1] == "{":
            stack.pop()
        elif char == "]" and stack and stack[-1] == "[":
            stack.pop()

    if in_string or len(stack) > 3:
        return text

    closing = {"{": "}", "[": "]"}
    return text + "".join(closing[item] for item in reversed(stack))


def convert_single_quoted_values(text: str) -> str:
    """
    Convert Python-style single-quoted JSON tokens outside double-quoted strings.

    Local models often return mostly valid JSON but use single quotes for a few
    array items, for example:
    {"lines": ["a", 'b']}
    This keeps source-code apostrophes inside already-double-quoted JSON strings
    untouched, while repairing keys or values that are real JSON tokens.
    """
    repaired: list[str] = []
    in_double_string = False
    escaped = False
    index = 0

    while index < len(text):
        char = text[index]

        if escaped:
            repaired.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            repaired.append(char)
            escaped = True
            index += 1
            continue

        if char == '"':
            repaired.append(char)
            in_double_string = not in_double_string
            index += 1
            continue

        if char == "'" and not in_double_string:
            closing = _find_single_quote_end(text, index + 1)
            if closing is not None and _looks_like_json_single_quoted_token(text, index, closing):
                literal = text[index:closing + 1]
                try:
                    value = ast.literal_eval(literal)
                except Exception:
                    value = literal[1:-1]
                repaired.append(json.dumps(value, ensure_ascii=False))
                index = closing + 1
                continue

        repaired.append(char)
        index += 1

    return "".join(repaired)


def _find_single_quote_end(text: str, start: int) -> int | None:
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == "'":
            return index
    return None


def _looks_like_json_single_quoted_token(text: str, start: int, end: int) -> bool:
    previous_index = start - 1
    while previous_index >= 0 and text[previous_index].isspace():
        previous_index -= 1
    previous = text[previous_index] if previous_index >= 0 else ""

    next_index = end + 1
    while next_index < len(text) and text[next_index].isspace():
        next_index += 1
    next_char = text[next_index] if next_index < len(text) else ""

    return previous in "{[,:" or next_char == ":"


def light_json_repair(text: str, extract_region: bool = True) -> str:
    repaired = strip_bom(text)
    repaired = strip_markdown_fence(repaired)
    if extract_region:
        repaired = extract_largest_json_region(repaired)
    repaired = remove_trailing_commas(repaired)
    repaired = replace_python_literals(repaired)
    repaired = quote_unquoted_keys(repaired)
    repaired = escape_raw_content_field(repaired)
    repaired = escape_control_chars_in_strings(repaired)
    repaired = convert_single_quoted_values(repaired)
    repaired = balance_trailing_delimiters(repaired)
    return repaired.strip()


def try_literal_eval(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = ast.literal_eval(candidate)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _replace_identifiers_outside_strings(text: str, replacements: dict[str, str]) -> str:
    result: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if escaped:
            result.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\":
            result.append(char)
            escaped = True
            index += 1
            continue
        if char == '"':
            result.append(char)
            in_string = not in_string
            index += 1
            continue
        if not in_string and (char.isalpha() or char == "_"):
            start = index
            index += 1
            while index < len(text) and (text[index].isalnum() or text[index] == "_"):
                index += 1
            word = text[start:index]
            result.append(replacements.get(word, word))
            continue
        result.append(char)
        index += 1
    return "".join(result)
