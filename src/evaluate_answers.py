from answer_generator import AnswerGenerator
from chat import check_citation_ids
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
    generator = AnswerGenerator()

    status_matches = 0
    citation_checks_passed = 0
    answered_drafts = 0
    supported_drafts = 0
    withheld = 0
    errors = 0

    try:
        documents = load_documents(DOCUMENTS_PATH)
        searcher = HybridSearch(documents)
        verifier = CitationVerifier(generator.client, generator.model)

        for case in CASES:
            question = case["question"]

            print(f"\nQuestion: {question}")
            print(f"Expected status: {case['expected_status']}")

            try:
                results = searcher.search(question, top_k=3)
                answer = generator.generate(question, results)

                status_match = answer.status == case["expected_status"]
                status_matches += int(status_match)

                print(f"Generated status: {answer.status}")
                print(f"Status match: {status_match}")

                check_citation_ids(answer, results)
                citation_checks_passed += 1

                if answer.status == "answered":
                    answered_drafts += 1
                    verification = verifier.verify(answer, results)

                    print(f"Verification: {verification.verdict}")
                    print(f"Reason: {verification.reason}")

                    if verification.verdict != "supported":
                        withheld += 1
                        print("Display decision: WITHHOLD")
                        continue

                    supported_drafts += 1
                else:
                    print("Verification: skipped for non-answer status")

                print("Display decision: SHOW")
                print(f"Response: {answer.answer}")

            except Exception as error:
                errors += 1
                print(f"Display decision: WITHHOLD — {type(error).__name__}")

        print("\nEnd-to-end development checks")
        print("-" * 45)
        print(f"Status matches: {status_matches}/{len(CASES)}")
        print(
            f"Structural citation checks passed: "
            f"{citation_checks_passed}/{len(CASES)}"
        )
        print(
            f"Answered drafts accepted by verifier: "
            f"{supported_drafts}/{answered_drafts}"
        )
        print(f"Drafts withheld by verifier: {withheld}")
        print(f"Requests with processing errors: {errors}")
        print("These checks do not measure overall answer accuracy.")

    finally:
        generator.close()


if __name__ == "__main__":
    main()