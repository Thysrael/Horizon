from src.setup.presets import match_domains, match_sources


def _presets(keyword: str, tag: str) -> dict:
    return {
        "domains": [
            {
                "id": "sample",
                "keywords": [keyword],
                "sources": [
                    {
                        "type": "rss",
                        "description": "",
                        "tags": [tag],
                        "config": {"url": "https://example.com/feed"},
                    }
                ],
            }
        ]
    }


def test_short_preset_terms_do_not_match_inside_unrelated_words():
    presets = _presets("ai", "ai")

    assert match_domains("chain", presets) == []
    assert match_sources("chain", presets) == []


def test_short_preset_terms_match_punctuated_abbreviations():
    ai_presets = _presets("ai", "ai")
    c_presets = _presets("c", "c")

    assert match_sources("AI/ML", ai_presets)
    assert match_sources("I use C++", c_presets)


def test_multilingual_tag_alias_still_matches_as_a_substring():
    assert match_sources("关注人工智能应用", _presets("ai", "ai"))
