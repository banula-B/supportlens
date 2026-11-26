import re

def check_citation_ids(answer, results):
    allowed_ids = {
        result["document"]["id"] for result in results
    }

    declared_ids = set(answer.citation_ids)

    inline_ids = set(
        re.findall(r"\[(doc-[^\]\s]+)\]", answer.answer)
    )

    unknown_ids = (declared_ids | inline_ids) - allowed_ids

    if unknown_ids:
        raise ValueError(
            "Answer cites documents that were not retrieved: "
            f"{sorted(unknown_ids)}"
        )

    if inline_ids != declared_ids:
        missing_from_list = inline_ids - declared_ids
        missing_from_text = declared_ids - inline_ids

        raise ValueError(
            "Inline citations and citation_ids do not match.\n"
            f"Inline IDs detected: {sorted(inline_ids)}\n"
            f"Declared IDs: {sorted(declared_ids)}\n"
            f"Missing from citation_ids: {sorted(missing_from_list)}\n"
            f"Missing from answer text: {sorted(missing_from_text)}\n"
            f"Rejected draft: {answer.answer!r}"
        )

    if answer.status == "answered" and not declared_ids:
        raise ValueError(
            "An answered response must include a citation."
        )