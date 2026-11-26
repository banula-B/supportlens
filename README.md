# SupportLens

**A conversational support assistant with hybrid retrieval, source citations, and model-based claim verification.**

SupportLens answers questions from a small technical-support knowledge base. It combines BM25 and semantic search, generates answers with document citations, and checks answered drafts against their cited evidence before displaying them. It can ask for clarification or report insufficient evidence instead of guessing.

**Status:** working local prototype. Browser chat, FastAPI endpoints, bounded conversation memory, and citation verification are implemented. A larger evaluation set, real-document ingestion, and deployment remain future work.

## Example conversation

> **User:** I cannot access my account.  
> **SupportLens:** What error message do you see?  
> **User:** AUTH-423  
> **SupportLens:** Contact the workspace administrator to unlock the account. Resetting your password does not unlock it. [doc-005]  
> **User:** Will resetting my password fix it?  
> **SupportLens:** No. Resetting your password does not unlock an account with AUTH-423. [doc-005]

If asked whether AUTH-423 automatically clears after 15 minutes, the assistant reports that the supplied documents do not specify this. A colleague's claim in the conversation is not treated as documentary evidence.

The examples use fictional support documentation, not a real product's policies.

## Implemented features

- **Hybrid retrieval:** BM25 and dense semantic search combined with reciprocal rank fusion (RRF).
- **Local embeddings:** `sentence-transformers/all-MiniLM-L6-v2`, running on CPU.
- **Structured answer generation:** a hosted Groq model returns individual claims and their supporting document IDs. Python renders the inline citations.
- **Structural citation validation:** checks cited IDs against retrieved documents and checks that inline IDs match declared IDs.
- **Model-based claim verification:** checks answered drafts against cited passages; unsupported or uncertain drafts are withheld.
- **Three response statuses:** `answered`, `insufficient_evidence`, and `clarification_needed`.
- **Conversation context:** up to eight previous messages are used to resolve follow-up questions before retrieval.
- **Browser chat:** conversation bubbles, source details, a waiting indicator, and a New chat button.
- **FastAPI:** a local API with input validation, provider-error handling, and a single active-question limit.
- **Evaluation scripts:** retrieval comparisons, reranking experiments, verifier examples, and end-to-end development checks.

## How it works

1. Validate the current question and optional conversation history.
2. When history is present, use the hosted model to turn the message into a standalone question. Ask for clarification if its meaning remains ambiguous.
3. Retrieve candidate passages with BM25 and semantic search, then combine their rankings with RRF.
4. Generate a structured response using the retrieved evidence.
5. Render citations and validate their document IDs.
6. For an answered draft, run the claim-support verifier. Display the answer only when its verdict is `supported`.
7. Return the answer, verification status, and cited source metadata to the browser.

History supplies conversational context, not evidence. The generator and verifier receive retrieved documents as their evidence source.

### Conversation memory

The browser keeps the latest four successful exchanges, up to eight messages. It sends this context with the next question; the server does not maintain a persistent conversation session.

- New chat and page refresh clear memory.
- Withheld drafts and processing errors do not enter memory.
- History messages are limited to 4,000 characters; questions to 2,000 characters.
- Requests without history skip the question-resolution model call.
- Requests with history add one hosted model call before the normal answer pipeline.
- Existing CLI requests remain single-turn.

### Reranking experiment

A cross-encoder reranker was implemented and evaluated separately. On the small development set, it reduced top-1 retrieval hits from 12/12 to 11/12 and added latency. It is therefore **not enabled in the default chat pipeline**.

## Technology

| Component | Implementation |
|---|---|
| Backend | Python and FastAPI |
| Browser interface | HTML, CSS, JavaScript |
| Lexical search | BM25 |
| Semantic search | Sentence Transformers |
| Rank fusion | Reciprocal rank fusion |
| Experimental reranker | Cross-encoder |
| Hosted generation and verification | Groq; configured model `openai/gpt-oss-20b` |
| Structured validation | Pydantic |
| Configuration | Environment variables and python-dotenv |

No dedicated GPU, database, or Docker container is required for the local prototype. Hosted generation requires internet access and an API key. Provider model availability and quotas depend on the account.

## Local setup — Windows PowerShell

Clone this repository and open a terminal in its root directory.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, enable scripts for the current terminal session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_api_key_here
GROQ_MODEL=openai/gpt-oss-20b
```

Keep `.env` excluded from version control. Never commit a real API key.

Start the server:

```powershell
python -m uvicorn api:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
```

Open:

- Chat: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Local health check: http://127.0.0.1:8000/health

The first startup downloads the embedding model if it is not cached. Document embeddings are created at application startup. On a memory-constrained laptop, use one worker and avoid running the chat server and evaluation scripts simultaneously.

The health endpoint checks the local application; it does not verify the hosted model provider's availability.

## API example

`POST /ask` accepts a question and optional history:

```json
{
  "question": "Will resetting my password fix it?",
  "history": [
    {
      "role": "user",
      "content": "I cannot log in and see AUTH-423."
    },
    {
      "role": "assistant",
      "content": "Contact the workspace administrator to unlock the account. [doc-005]"
    }
  ]
}
```

A request containing only `question` is also valid.

Example successful response:

```json
{
  "withheld": false,
  "answer": {
    "status": "answered",
    "answer": "Resetting the password does not unlock an account with AUTH-423. [doc-005]",
    "citation_ids": ["doc-005"]
  },
  "verification_status": "supported",
  "sources": [
    {
      "id": "doc-005",
      "title": "Locked accounts",
      "source": "demo://account/locked"
    }
  ]
}
```

If claim verification rejects a draft, the service returns `withheld: true`, `answer: null`, and no displayable sources. Non-answer statuses use `verification_status: "not_checked"`. Processing errors return an HTTP error instead of a successful answer payload.

`demo://` source identifiers refer to local demonstration records, not public web pages.

## Evaluation so far

These are **development checks on a small, manually authored dataset**, not a held-out benchmark or an estimate of production accuracy.

### Retrieval

Seven demonstration documents cover password resets, account lockouts, background jobs, and upload restrictions. The retrieval set contains 14 questions: 12 have labeled relevant passages and two have no relevant passage.

| Retrieval method | Top-1 hits on 12 cases with relevant passages |
|---|---:|
| Keyword baseline | 11/12 |
| BM25 | 11/12 |
| Semantic search | 11/12 |
| Hybrid RRF | 12/12 |
| Hybrid plus experimental reranker | 11/12 |

Hybrid candidates contained a labeled relevant passage in 12/12 cases at a candidate depth of five. The two no-relevant-passage cases were inspected separately and excluded from the retrieval-hit denominator.

Some labels identify topical relevance rather than passages that fully answer the question. A retrieval hit therefore does not establish answerability, factual correctness, or successful abstention.

The observed mean reranking time was approximately 205 ms on the development laptop. This rough measurement included first inference and excluded model loading and hybrid retrieval.

### Claim verifier

Six manually constructed checks passed in the reported run:

- Correct statement accepted.
- Reversed meaning rejected.
- Invented duration rejected.
- Correct statement with the wrong citation rejected.
- Supported statement with an unsupported addition rejected.
- Correct paraphrase accepted.

Passing these examples does not prove that the verifier catches all unsupported claims.

### Browser conversation checks

The following behaviors were observed in manual testing:

| Scenario | Observed behavior |
|---|---|
| Vague account-access problem | Asked for clarification |
| Reply with AUTH-423 | Returned relevant cited guidance |
| Follow-up about resetting a password | Retained the account context |
| Switch to upload file types | Answered the new topic |
| New chat followed by an ambiguous question | Requested context again |
| Colleague claims a 15-minute automatic unlock | Reported insufficient evidence |

These are individual observed runs, not repeated reliability measurements. The conversation update also includes seven offline checks for context handling and validation; these do not test live model reasoning.

### Run development checks

Run each command separately from the project root:

```powershell
python src\compare_search.py
python src\evaluate_reranker.py
python src\test_verifier_manual.py
python -u src\evaluate_answers.py
```

The verifier and answer evaluations use hosted model requests and consume quota. Review the selected cases in `evaluate_answers.py` before running it; earlier development runs selected only a subset.

If the conversation update's test file has been copied into `tests/`, run its offline checks with:

```powershell
python -m unittest discover -s tests -p test_conversation.py -v
```

## Main files

| Path | Responsibility |
|---|---|
| `src/api.py` | HTTP endpoints, request validation, frontend serving |
| `src/service.py` | Retrieval, generation, and verification orchestration |
| `src/conversation.py` | Bounded history validation and follow-up resolution |
| `src/answer_generator.py` | Structured answer generation and citation rendering |
| `src/citations.py` | Structural citation validation |
| `src/verifier.py` | Model-based claim-support checks |
| `src/hybrid_search.py` | Combines lexical and semantic rankings |
| `src/bm25_search.py` | BM25 retrieval |
| `src/semantic_search.py` | Embedding-based retrieval |
| `src/reranker.py` | Experimental cross-encoder reranking |
| `src/chat.py` | Command-line chat |
| `src/web/index.html` | Browser layout and styling |
| `src/web/chat.js` | Chat requests, display, and browser-held history |
| `src/compare_search.py` | Retrieval comparison |
| `src/evaluate_answers.py` | End-to-end development checks |

## Limitations

- The knowledge base contains only seven fictional documents. Real-file ingestion, document chunking, and persistent embedding storage are not implemented.
- Evaluation examples have been used during development; reported scores should not be presented as unseen-test performance.
- The generator and verifier use the same configured model and can share blind spots.
- Citation-ID checks establish structural consistency, not semantic support.
- Model-based verification is fallible. It cannot guarantee that every displayed answer is correct.
- Non-answer messages bypass claim-support verification.
- Follow-up resolution can change intent incorrectly. The claim verifier checks evidence support, not whether the rewritten question matches the original intent.
- Prompt instructions treat history and documents as untrusted, but prompt-injection robustness has not been established through systematic testing.
- Hosted API rate limits, timeouts, and outages can interrupt responses.
- There is no authentication, durable chat storage, production monitoring, or public deployment. The API is intended for local use.

## Roadmap

The core local prototype is complete. The next goal is a reproducible, well-evaluated portfolio release.

- [ ] Create a separate conversation evaluation set covering follow-ups, topic changes, unsupported premises, and ambiguous references.
- [ ] Record status matches, supported-answer outcomes, incorrect answers, abstentions, processing errors, and latency separately.
- [ ] Add a larger realistic support corpus with clear provenance and usage permissions.
- [ ] Implement document ingestion, chunking, source metadata, and reusable embedding storage.
- [ ] Add API/service regression tests and automated checks in GitHub Actions.
- [ ] Add screenshots, a short demonstration video, and a reproducible evaluation report.
- [ ] Assess a hosted deployment after resource requirements and API usage are measured.

Optional later extensions include PDF/OCR ingestion, a human review queue, and more advanced retrieval routing. They are not required to finish the first portfolio release.
