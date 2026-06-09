from scripts.tts.pronunciation import apply_lexicon, _match_case

LEX = {"begere": "begére", "begeren": "begéren"}


def test_basic_replacement():
    assert apply_lexicon("ik begere rust", LEX) == "ik begére rust"


def test_only_whole_words():
    # 'begeren' mag niet door de 'begere'-regel half vervangen worden
    assert apply_lexicon("zij begeren brood", LEX) == "zij begéren brood"


def test_substring_not_touched():
    # een woord dat 'begere' als deel bevat maar geen lexicon-entry is
    assert apply_lexicon("onbegerelijk", LEX) == "onbegerelijk"


def test_capitalized_first_letter_preserved():
    assert apply_lexicon("Begere ik dit?", LEX) == "Begére ik dit?"


def test_all_caps_preserved():
    assert apply_lexicon("BEGERE", LEX) == "BEGÉRE"


def test_punctuation_adjacent():
    assert apply_lexicon("hij begere, en rust.", LEX) == "hij begére, en rust."


def test_empty_lexicon_is_noop():
    assert apply_lexicon("ik begere rust", {}) == "ik begere rust"


def test_match_case_helper():
    assert _match_case("begere", "begére") == "begére"
    assert _match_case("Begere", "begére") == "Begére"
    assert _match_case("BEGERE", "begére") == "BEGÉRE"
