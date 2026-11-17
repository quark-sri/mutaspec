"""Rule Mutants found with text rules."""

from mutaspec import mutants


def rules(line: str) -> list[str]:
    return [(m.rule) for m in mutants.find_in_text("x.java", line)]


def test_ac3_operators_with_spaces_are_swapped():
    assert rules("if (a < b && c >= d) {\n") == ["< -> <=", "&& -> ||", ">= -> >"]
    assert rules("    return a + b * c;\n") == ["+ -> -", "* -> /"]
    assert rules("ok = x == 1 or y != 2\n") == ["== -> !=", "or -> and", "!= -> =="]


def test_ac3_boolean_words_are_swapped():
    assert rules("return true;\n") == ["true -> false"]
    assert rules("    return False\n") == ["False -> True"]


def test_ac3_generics_lambdas_and_compound_operators_are_not_changed():
    assert rules("List<String> xs = items.stream().map(x -> x).toList();\n") == []
    assert rules("i += 1; j -= 2; k = -1;\n") == []


def test_ac3_strings_and_comments_are_not_changed():
    assert rules('msg = "a < b and true"  # x < y\n') == []
    assert rules("int z = a - b; // a + b\n") == ["- -> +"]


def test_ac3_plus_on_a_line_with_text_is_skipped():
    assert rules('return "id " + id + " x";\n') == []
    assert rules('ok = a == "x" and n - 1\n') == ["== -> !=", "and -> or", "- -> +"]


def test_ac3_imports_annotations_and_logging_are_skipped():
    assert rules("import a.b.C;\n") == []
    assert rules("@Min(1 + 1)\n") == []
    assert rules('log.info("x {}", a + b);\n') == []
    assert rules("    print(a + b)\n") == []


def test_mutant_changes_one_place_and_has_a_stable_id(tmp_path):
    (tmp_path / "a.py").write_text("x = 1\ny = a + b + c\n")

    first = mutants.find(tmp_path, ["a.py"])
    again = mutants.find(tmp_path, ["a.py"])

    assert [m.id for m in first] == [m.id for m in again]
    assert len({m.id for m in first}) == 2
    assert [m.after for m in first] == ["y = a - b + c\n", "y = a + b - c\n"]
    assert first[0].line == 2


def test_apply_and_restore_keep_line_endings(tmp_path):
    path = tmp_path / "a.py"
    path.write_bytes(b"x = 1\r\ny = a + b\r\n")
    mutant = mutants.find(tmp_path, ["a.py"])[0]

    original = mutants.apply(mutant, tmp_path)
    assert path.read_bytes() == b"x = 1\r\ny = a - b\r\n"

    mutants.restore(mutant, tmp_path, original)
    assert path.read_bytes() == b"x = 1\r\ny = a + b\r\n"


def test_ac4_sample_is_repeatable_and_limited(tmp_path):
    (tmp_path / "a.py").write_text("".join(f"v{i} = a + b\n" for i in range(50)))
    found = mutants.find(tmp_path, ["a.py"])

    picked = mutants.sample(found, 10)

    assert len(picked) == 10
    assert picked == mutants.sample(found, 10)
    assert mutants.sample(found, 100) == found


def test_missing_and_binary_files_are_skipped(tmp_path):
    (tmp_path / "b.bin").write_bytes(b"\xff\xfe a + b")

    assert mutants.find(tmp_path, ["b.bin", "gone.py"]) == []


def all_rules(text: str) -> list[tuple[int, str]]:
    return [(m.line, m.rule) for m in mutants.find_in_text("x", text)]


def test_ac3_python_docstrings_are_not_changed():
    text = 'def f(x, y):\n    """\n    True when x < y and z.\n    """\n    return x < y\n'
    assert all_rules(text) == [(5, "< -> <=")]


def test_ac3_block_comments_over_several_lines_are_not_changed():
    text = "/*\n  total = a + b\n  if x < y\n*/\nint z = 1; /* a + b */ int w = c - d;\n"
    assert all_rules(text) == [(5, "- -> +")]


def test_ac3_java_text_blocks_and_js_templates_are_not_changed():
    java = 'String s = """\n    a + b < c\n    """;\nint n = a * b;\n'
    js = "const t = `\n  ${a} - ${b} > 1\n`;\nconst n = a * b;\n"
    assert all_rules(java) == [(4, "* -> /")]
    assert all_rules(js) == [(4, "* -> /")]


def test_ac3_annotations_and_logging_over_several_lines_are_skipped():
    text = "@Size(\n    max = 10 * 2)\nlog.info(\n    a - b,\n    c < d);\nint n = a * b;\n"
    assert all_rules(text) == [(6, "* -> /")]


def test_ac3_code_after_a_leading_block_comment_is_still_mutated():
    assert all_rules("/* note */ int q = a + b;\n") == [(1, "+ -> -")]
