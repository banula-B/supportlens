from service import SupportLensService


def main():
    service = SupportLensService()

    try:
        print("\nSupportLens is ready. Type 'exit' to quit.")

        while True:
            question = input("\nQuestion: ").strip()

            if question.lower() == "exit":
                break

            if not question:
                print("Please enter a question.")
                continue

            try:
                result = service.ask(question)

            except Exception as error:
                print(
                    f"\nRequest failed: {type(error).__name__}. "
                    "No answer was displayed."
                )
                continue

            if result.withheld:
                print("\nStatus: verification_failed")
                print(
                    "The draft did not pass the evidence check "
                    "and has been withheld."
                )
                print(
                    f"Check result: {result.verification.verdict}"
                )
                continue

            answer = result.answer

            if answer is None:
                print("No displayable answer was returned.")
                continue

            print(f"\nStatus: {answer.status}")
            print(answer.answer)

            if result.sources:
                print("\nCited sources:")

                for source in result.sources:
                    print(
                        f"[{source['id']}] "
                        f"{source['title']} — {source['source']}"
                    )

            if result.verification is not None:
                print("\nModel-based claim-support check: passed.")
                print("This check can still make mistakes.")
            else:
                print(
                    "\nCitation IDs checked. Semantic verification "
                    "was skipped for this non-answer status."
                )

    finally:
        service.close()


if __name__ == "__main__":
    main()