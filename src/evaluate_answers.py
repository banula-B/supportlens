import os

from answer_generator import AnswerGenerator
from citations import check_citation_ids
from hybrid_search import HybridSearch
from main import DOCUMENTS_PATH, load_documents
from verifier import CitationVerifier


CASES = [
    {
        "question": "Will resetting my password resolve AUTH-423?",
        "expected_status": "answered",
    },
    {
        "question": "Can I upload a file larger than 10 MB?",
        "expected_status": "answered",
    },
    {
        "question": "Does the password reset link expire after 15 minutes?",
        "expected_status": "insufficient_evidence",
    },
    {
        "question": "I lost access to my account",
        "expected_status": "clarification_needed",
    },
    {
        "question": "Tell me about elephants",
        "expected_status": "insufficient_evidence",
    },
]


def main():
    # Use CASES to run all five tests once this single case works.
    selected_cases = CASES[3:4]

    generator = AnswerGenerator()

    attempted = 0
    generated = 0
    status_matches = 0
    citation_checks_passed = 0
    verification_attempted = 0
    verification_completed = 0
    supported_drafts = 0
    withheld = 0
    displayed = 0
    errors = 0

    try:
        print(f"Using model: {generator.model}", flush=True)

        documents = load_documents(DOCUMENTS_PATH)
        searcher = HybridSearch(documents)
        verifier = CitationVerifier(
            generator.client,
            generator.model,
        )

        print(
            f"\nSelected cases: {len(selected_cases)}",
            flush=True,
        )

        for case in selected_cases:
            attempted += 1
            question = case["question"]

            print(f"\nQuestion: {question}", flush=True)
            print(
                f"Expected status: {case['expected_status']}",
                flush=True,
            )

            try:
                print(
                    "Stage 1: retrieving passages...",
                    flush=True,
                )
                results = searcher.search(question, top_k=3)

                print(
                    "Stage 2: requesting generated answer...",
                    flush=True,
                )
                answer = generator.generate(question, results)
                generated += 1

                print("Generation completed.", flush=True)

                status_match = (
                    answer.status == case["expected_status"]
                )
                status_matches += int(status_match)

                print(
                    f"Generated status: {answer.status}",
                    flush=True,
                )
                print(
                    f"Status match: {status_match}",
                    flush=True,
                )

                print("Checking citation IDs...", flush=True)
                check_citation_ids(answer, results)
                citation_checks_passed += 1

                print(
                    "Structural citation check: passed.",
                    flush=True,
                )

                if answer.status == "answered":
                    verification_attempted += 1

                    print(
                        "Stage 3: verifying answer...",
                        flush=True,
                    )
                    verification = verifier.verify(answer, results)
                    verification_completed += 1

                    print(
                        f"Verification: {verification.verdict}",
                        flush=True,
                    )
                    print(
                        f"Reason: {verification.reason}",
                        flush=True,
                    )

                    if verification.verdict != "supported":
                        withheld += 1

                        print(
                            "Display decision: WITHHOLD "
                            "(verifier did not approve)",
                            flush=True,
                        )
                        continue

                    supported_drafts += 1

                else:
                    print(
                        "Verification: skipped for non-answer status",
                        flush=True,
                    )

                displayed += 1

                print("Display decision: SHOW", flush=True)
                print(f"Response: {answer.answer}", flush=True)

                if answer.citation_ids:
                    print("Cited sources:", flush=True)
                    cited_ids = set(answer.citation_ids)

                    for result in results:
                        document = result["document"]

                        if document["id"] in cited_ids:
                            print(
                                f"  [{document['id']}] "
                                f"{document['title']} — "
                                f"{document['source']}",
                                flush=True,
                            )

            except Exception as error:
                errors += 1

                message = str(error)

                for variable in (
                    "GROQ_API_KEY",
                    "GEMINI_API_KEY",
                ):
                    api_key = os.getenv(variable)

                    if api_key:
                        message = message.replace(
                            api_key,
                            "[REDACTED]",
                        )

                print(
                    "Display decision: WITHHOLD "
                    "(processing error)",
                    flush=True,
                )
                print(
                    f"Error type: {type(error).__name__}",
                    flush=True,
                )
                print(
                    f"Details: {message[:1500]}",
                    flush=True,
                )
                print(
                    "Stopping evaluation after this error.",
                    flush=True,
                )
                break

        print("\nEnd-to-end development checks")
        print("-" * 45)
        print(f"Selected cases: {len(selected_cases)}")
        print(f"Attempted cases: {attempted}")
        print(f"Generated responses: {generated}")

        if generated:
            print(
                f"Status matches: {status_matches}/{generated}"
            )
            print(
                "Structural citation checks passed: "
                f"{citation_checks_passed}/{generated}"
            )
        else:
            print("Status matches: not evaluated")
            print("Structural citation checks: not evaluated")

        print(
            f"Verification attempts: {verification_attempted}"
        )
        print(
            f"Completed verifications: {verification_completed}"
        )

        if verification_completed:
            print(
                "Drafts accepted by verifier: "
                f"{supported_drafts}/{verification_completed}"
            )
        else:
            print("Claim-support verification: not evaluated")

        print(f"Drafts withheld by verifier: {withheld}")
        print(f"Responses displayed: {displayed}")
        print(f"Processing errors: {errors}")
        print("Non-answer responses bypass semantic verification.")
        print("These checks do not measure overall answer accuracy.")

    finally:
        generator.close()


if __name__ == "__main__":
    main()