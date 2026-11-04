from src.ai.utils import parse_json_response


def test_skips_brace_text_before_the_json_object():
    response = 'Scores use the scale {0-10}. Result:\n{"score": 7, "reason": "solid"}'

    assert parse_json_response(response) == {"score": 7, "reason": "solid"}


def test_ignores_braces_inside_json_strings():
    response = (
        'Here is the result: {"summary": "closes the } in parse()", "score": 4}\n'
        "Template used: {title}"
    )

    assert parse_json_response(response) == {
        "summary": "closes the } in parse()",
        "score": 4,
    }


def test_extracts_object_after_prose():
    assert parse_json_response('Sure! {"duplicates": []} Done.') == {"duplicates": []}
