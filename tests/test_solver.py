from pathlib import Path
from solver.solver import load_base_words, solve_candidates


def test_solve_filters_and_longest_and_dedup():
    allowed = "aelnrst"
    mandatory = "e"
    candidates = [
        "entstellen",
        "entstellen",   # duplicate
        "stresstest",
        "ALLERERSTE",
        "falsch",       # has disallowed letters
        "rennen",       # allowed letters? contains 'r','e','n' -> yes but 'n' is allowed; good
        "rösten",       # non-ascii should be ignored
    ]

    res = solve_candidates(allowed, mandatory, candidates)

    assert "entstellen" in res["valid_words"]
    assert "stresstest" in res["valid_words"]
    assert "allererste" in res["valid_words"]
    assert "falsch" not in res["valid_words"]
    assert "rösten" not in res["valid_words"]

    # no duplicates
    assert res["valid_words"].count("entstellen") == 1

    # longest
    assert res["max_len"] == 10
    assert set(res["longest_words"]) == {"allererste", "entstellen", "stresstest"}


def test_pangram_exact_7_letters():
    allowed = "abcdefg"
    mandatory = "a"
    candidates = ["gfedcba", "aaaaaaa", "abcdefga"]  # only first is exact 7
    res = solve_candidates(allowed, mandatory, candidates)
    assert res["pangrams_7_exact"] == ["gfedcba"]


def test_invalid_inputs():
    try:
        solve_candidates("abc", "a", ["abc"])
        assert False, "expected ValueError"
    except ValueError:
        pass

    try:
        solve_candidates("abcdefg", "z", ["abcdefg"])
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_load_base_words_skips_count_strips_flags_dedups_and_ascii(tmp_path: Path):
    # latin-1 file with umlaut byte (ö = 0xF6), plus duplicates and flags
    dic_content = "5\nentstellen/A\nentstellen/B\nstresstest\nr\xf6sten\nabc-def\n"
    p = tmp_path / "de_DE_test.dic"
    p.write_bytes(dic_content.encode("latin-1"))

    words = load_base_words(p, encodings=["utf-8", "latin-1"])

    # umlaut word filtered out (non-ascii), hyphen word filtered out
    assert words == ["entstellen", "stresstest"]