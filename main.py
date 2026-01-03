#!/usr/bin/env python3
import os
import re
import sys
import subprocess
from pathlib import Path
from collections import Counter

ASCII_RE = re.compile(r"^[a-z]+$")


def load_dotenv(dotenv_path: Path = Path(".env")) -> None:
    if not dotenv_path.exists():
        return
    for raw_line in dotenv_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def parse_list_env(name: str, default: str) -> list[str]:
    raw = os.environ.get(name, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def env_bool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def env_int(name: str, default: int) -> int:
    v = os.environ.get(name)
    if v is None:
        return default
    try:
        return int(v)
    except ValueError:
        return default


def resolve_dic_aff(hunspell_dir: Path, candidates: list[str]) -> tuple[Path, Path, str]:
    """
    Returns (dic_path, aff_path, dict_base_name) where dict_base_name is for hunspell -d <name>.
    """
    for base in candidates:
        if base.endswith(".dic"):
            dic = hunspell_dir / base
            dict_base = Path(base).with_suffix("").name
        else:
            dic = hunspell_dir / f"{base}.dic"
            dict_base = base

        aff = dic.with_suffix(".aff")
        if dic.exists() and aff.exists():
            return dic, aff, dict_base

    raise RuntimeError(
        "No Hunspell dictionary found. Check .env (HUNSPELL_DIR / HUNSPELL_DICT_CANDIDATES)."
    )


def load_base_words(dic_path: Path, encodings: list[str]) -> list[str]:
    """
    Loads base entries from a Hunspell .dic file (deduped, ascii-only).
    """
    lines: list[str] | None = None
    for enc in encodings:
        try:
            with dic_path.open("r", encoding=enc) as f:
                first = f.readline()
                rest = f.readlines()
            all_lines = rest if first.strip().isdigit() else [first] + rest
            lines = all_lines
            break
        except UnicodeDecodeError:
            continue

    if lines is None:
        with dic_path.open("r", encoding=encodings[-1], errors="replace") as f:
            lines = f.readlines()

    words: set[str] = set()
    for line in lines:
        w = line.split("/", 1)[0].strip().lower()
        if ASCII_RE.fullmatch(w):
            words.add(w)

    return sorted(words)


def load_blacklist(path: str | None) -> set[str]:
    if not path:
        return set()
    p = Path(path)
    if not p.exists():
        return set()
    out: set[str] = set()
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        w = line.strip().lower()
        if w and not w.startswith("#") and ASCII_RE.fullmatch(w):
            out.add(w)
    return out


def looks_reasonable(word: str, *, min_len: int) -> bool:
    """
    Heuristic filter. It's optional because it can exclude legit words.
    - min length
    - reject triple repeated letters (often noise)
    - reject simple "abab" doubling for short words (e.g., 'effeff') if it matches this pattern
    """
    if len(word) < min_len:
        return False

    if re.search(r"(.)\1\1", word):  # aaa, eee, etc.
        return False

    # Reject exact doubling for short even-length words: abab, effeff, etc.
    if len(word) <= 8 and len(word) % 2 == 0:
        half = len(word) // 2
        if word[:half] == word[half:]:
            return False

    return True


def hunspell_filter_valid(words: list[str], *, dict_base: str, dic_dir: str) -> set[str]:
    """
    Robust batch validation:
    - send all words at once to 'hunspell -a'
    - parse one result line per word (ignoring header lines starting with '@')
    """
    if not words:
        return set()

    env = os.environ.copy()
    env["DICPATH"] = dic_dir

    # Send all words at once; hunspell reads stdin and outputs results.
    inp = ("\n".join(words) + "\n").encode("utf-8")

    p = subprocess.run(
        ["hunspell", "-a", "-d", dict_base, "-i", "UTF-8"],
        input=inp,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )

    out = p.stdout.decode("utf-8", errors="ignore").splitlines()

    # keep only result lines (not headers)
    result_lines = [line.strip() for line in out if line.strip() and not line.startswith("@")]

    # hunspell -a should output one result line per input word, in order.
    # If there are fewer lines than words, something went wrong; be conservative.
    accepted: set[str] = set()
    n = min(len(words), len(result_lines))

    for i in range(n):
        if result_lines[i].startswith("*"):
            accepted.add(words[i])

    return accepted


def solve(
    allowed: str,
    mandatory: str,
    base_words: list[str],
    *,
    dict_base: str,
    dic_dir: str,
    min_len: int,
    enable_reasonable_filter: bool,
    blacklist: set[str],
) -> None:
    allowed = allowed.lower().strip()
    mandatory = mandatory.lower().strip()

    if len(allowed) != 7 or len(set(allowed)) != 7 or not ASCII_RE.fullmatch(allowed):
        sys.exit("ERROR: allowed must be exactly 7 distinct letters (a-z)")
    if len(mandatory) != 1 or not ASCII_RE.fullmatch(mandatory):
        sys.exit("ERROR: mandatory must be exactly one a-z letter")
    if mandatory not in allowed:
        sys.exit("ERROR: mandatory letter must be among the allowed letters")

    allowed_set = set(allowed)
    allowed_counter = Counter(allowed)

    # Pre-filter cheaply (letters + mandatory + optional heuristics/blacklist)
    candidates: list[str] = []
    for w in base_words:
        if w in blacklist:
            continue
        if mandatory not in w:
            continue
        if set(w) - allowed_set:
            continue
        if enable_reasonable_filter and not looks_reasonable(w, min_len=min_len):
            continue
        if not enable_reasonable_filter and len(w) < min_len:
            continue
        candidates.append(w)

    print(f"Prefiltered candidates: {len(candidates)} (from {len(base_words)} base words)")
    print("Validating with hunspell...")

    accepted = hunspell_filter_valid(candidates, dict_base=dict_base, dic_dir=dic_dir)

    valid = [w for w in candidates if w in accepted]
    valid = sorted(set(valid), key=lambda x: (-len(x), x))

    pangrams = [w for w in valid if len(w) == 7 and Counter(w) == allowed_counter]
    pangrams = sorted(set(pangrams))

    print(f"\nAllowed letters : {allowed}")
    print(f"Mandatory letter: {mandatory}")
    print(f"Valid words     : {len(valid)}")

    print("\nExact 7-letter pangrams:")
    for w in pangrams:
        print(" ", w)

    if valid:
        max_len = len(valid[0])
        longest = [w for w in valid if len(w) == max_len]
        print(f"\nLongest word length: {max_len}")
        print("Longest word(s):")
        for w in longest:
            print(" ", w)

    print("\nTop 30 words:")
    for w in valid[:30]:
        print(f"  {w} ({len(w)})")


def main() -> None:
    load_dotenv(Path(os.environ.get("DOTENV_PATH", ".env")))

    hunspell_dir = Path(os.environ.get("HUNSPELL_DIR", str(Path.home() / "Library" / "Spelling")))
    dict_candidates = parse_list_env("HUNSPELL_DICT_CANDIDATES", "de_DE_frami,de_DE_neu,de_DE")
    encodings = parse_list_env("HUNSPELL_DIC_ENCODINGS", "utf-8,latin-1,cp1252")

    # Filters
    min_len = env_int("MINLEN", 4)
    enable_reasonable_filter = env_bool("FILTER_REASONABLE", True)
    blacklist_path = os.environ.get("BLACKLIST_PATH", "")
    blacklist = load_blacklist(blacklist_path)

    dic_path, _aff_path, dict_base = resolve_dic_aff(hunspell_dir, dict_candidates)

    if len(sys.argv) != 3:
        print("Usage: python main.py <7letters> <mandatory>")
        print("Example: python main.py aelnrst e")
        sys.exit(1)

    allowed_letters = sys.argv[1]
    mandatory_letter = sys.argv[2]

    base_words = load_base_words(dic_path, encodings)

    solve(
        allowed_letters,
        mandatory_letter,
        base_words,
        dict_base=dict_base,
        dic_dir=str(hunspell_dir),
        min_len=min_len,
        enable_reasonable_filter=enable_reasonable_filter,
        blacklist=blacklist,
    )


if __name__ == "__main__":
    main()