# ProofLens AI

## Product Requirements Document (PRD) v0.2

**Document status:** Proposed engineering-ready baseline\
**Product type:** Evidence-first document intelligence application using
Retrieval-Augmented Generation (RAG)\
**Release target:** Free-tier-first MVP\
**Primary input format:** PDF\
**Prepared:** 12 October 2026

------------------------------------------------------------------------

## 1. Executive Summary

ProofLens AI is an evidence-first document intelligence platform that
allows users to ask questions across multiple PDF documents, inspect
page-level supporting evidence, compare claims between sources, extract
structured information, and identify when the available material is
insufficient to support an answer.

ProofLens AI is not intended to be a generic PDF chatbot. Its defining
principle is that answers should be traceable to retrieved source
passages. The system must preserve document and page provenance
throughout ingestion, retrieval, generation, and display. It must
clearly distinguish supported findings from partial support,
disagreement, and insufficient evidence.

The MVP will use a Retrieval-Augmented Generation (RAG) architecture and
be designed for free-tier constraints from the start. It must minimize
recurring infrastructure and model costs, provide graceful
quota-exhaustion behaviour, and never silently trigger paid usage.

## 2. Product Vision

Make complex documents easier to understand and compare while allowing
users to verify where every important answer came from.

### 2.1 Product principles

1.  **Evidence first:** retrieved source passages ground factual
    answers.
2.  **Verifiability:** citations resolve to actual documents, pages, and
    excerpts.
3.  **Honest uncertainty:** unsupported questions are not answered with
    fabricated facts.
4.  **Privacy and isolation:** documents are accessible only within the
    authorized user/workspace scope.
5.  **Measurable quality:** retrieval, citation support, abstention, and
    reliability are tested.
6.  **Free-tier by design:** avoid paid dependencies, wasteful repeated
    calls, and silent paid fallbacks.
7.  **Incremental delivery:** validate the core RAG pipeline before
    implementing advanced features.
8.  **Modular architecture:** components can be improved or replaced
    without rebuilding the entire application.

## 3. Goals and Success Outcomes

### 3.1 MVP goals

-   Upload and process multiple PDFs.
-   Extract text while preserving page-level provenance.
-   Chunk extracted text and generate embeddings.
-   Store searchable vectors and document metadata.
-   Retrieve relevant evidence for user questions.
-   Generate answers grounded in retrieved passages.
-   Validate citation references and display source excerpts.
-   Abstain or qualify answers when evidence is insufficient or
    conflicting.
-   Compare claims across selected documents.
-   Provide document summaries and suggested questions where quota
    permits.
-   Support a repeatable evaluation suite.
-   Provide clear processing, quota, and error states.
-   Run within selected free-tier limits without unapproved paid usage.

### 3.2 Success measures

The project will define and record baseline metrics before release: -
Retrieval recall/precision on a curated question-and-evidence dataset. -
Citation reference validity. - Claim-to-evidence support rate. - Correct
abstention rate on questions whose answers are absent from the corpus. -
Comparison finding support rate. - Ingestion success and failure
rates. - End-to-end latency and provider error rates. - API usage and
cost/quota consumption per operation. - Successful document deletion and
access-isolation test rates.

Numerical thresholds must be chosen after the initial evaluation dataset
and baseline are established. The project must not claim perfect
accuracy or treat a model's self-reported confidence as a calibrated
probability.

## 4. Scope

### 4.1 In scope for the MVP

-   PDF upload and document library.
-   Text extraction with page references.
-   Configurable chunking and embedding model settings.
-   Vector-based semantic retrieval.
-   Evidence-grounded question answering.
-   Citation validation and evidence inspection.
-   Insufficient-evidence and conflicting-evidence handling.
-   Multi-document question answering and basic comparison.
-   Document summaries and suggested questions, subject to quota.
-   Processing status, retry, and failure handling.
-   Saved question/answer history where persistence is enabled.
-   Basic evaluation tooling and curated demo dataset.
-   Security, privacy, deletion, and usage limits.
-   Responsive, accessible user interface.

### 4.2 Planned enhancements after the core MVP

-   Hybrid keyword-plus-vector retrieval if evaluation shows a benefit.
-   Reranking and query rewriting/decomposition when justified by test
    results.
-   Document version comparison and clause-level change detection.
-   Structured extraction into tables or JSON with citations.
-   Knowledge-gap suggestions.
-   Exportable evidence reports in Markdown/PDF.
-   Automatic topic/category suggestions with user review.
-   OCR for scanned PDFs.
-   Additional document formats.
-   More advanced collaboration and background processing.

### 4.3 Explicit non-goals for the MVP

-   Guaranteed truth detection or guaranteed factual correctness.
-   Web research or automatic browsing of external sources.
-   Multi-agent orchestration or autonomous agents.
-   Fine-tuning a foundation model.
-   Mandatory OCR for every scanned or image-only PDF.
-   Enterprise SSO, billing, and complex organization administration.
-   Universal support for every file type or language.
-   Replacement of professional review in legal, medical, financial, or
    other high-stakes decisions.
-   Unbounded uploads, unlimited queries, or unlimited free AI usage.

## 5. Users and Primary Use Cases

### 5.1 Intended users

-   Students and researchers reviewing papers and reports.
-   Professionals searching policies, manuals, and internal
    documentation.
-   Analysts comparing claims across reports.
-   Users reviewing multiple versions of a document.
-   Anyone who needs source-grounded answers from a bounded PDF
    collection.

### 5.2 Core use cases

1.  Upload several PDFs and ask a question across them.
2.  Open a citation and inspect the supporting passage in context.
3.  Ask for a document summary and suggested questions.
4.  Compare how multiple documents address the same topic.
5.  Identify agreements, contradictions, differences in scope, and
    evidence gaps.
6.  Extract specified fields, dates, amounts, obligations, or
    requirements with citations (planned enhancement).
7.  Save previous research questions and revisit their evidence.
8.  Export an evidence-backed report (planned enhancement).

## 6. Product Workflow

### 6.1 Indexing workflow

1.  User selects or creates a workspace and uploads PDF files.
2.  Backend validates file type, size, and configured limits.
3.  System registers each document and assigns a stable document ID and
    version.
4.  PDF parser extracts text by page and records extraction status.
5.  Text is cleaned conservatively and split into chunks with
    configurable size and overlap.
6.  Each chunk retains document ID, version, page number(s), chunk ID,
    text offsets where available, and relevant metadata.
7.  Embedding model converts chunks to vectors.
8.  Chunks, vectors, and metadata are stored in the configured database.
9.  Document status becomes indexed only after required steps succeed.
10. The interface displays success, partial success, or actionable
    failure details.

### 6.2 Question-answering workflow

1.  User enters a question and selects the permitted document/workspace
    scope.
2.  Backend authenticates and authorizes the request.
3.  System embeds the question using the compatible embedding model.
4.  Retrieval searches only within the authorized scope and applies
    configured filters.
5.  System selects candidate passages and records retrieval metadata for
    diagnostics.
6.  Evidence sufficiency is assessed using retrieval signals and
    application rules.
7.  If evidence is sufficient, the LLM receives the question and
    selected passages under instructions to answer only from supplied
    evidence.
8.  The response is parsed into a defined answer structure.
9.  Citation references are validated against stored source records.
10. Claims and citations are checked for support to the extent supported
    by the implementation and evaluation process.
11. The UI displays the answer, evidence status, source citations, and
    excerpts.
12. If evidence is insufficient, the system says so and may identify
    what is missing.
13. Usage and operational metrics are recorded without unnecessarily
    logging document contents.

### 6.3 Comparison workflow

1.  User selects two or more documents or a defined document set.
2.  System retrieves evidence for each document independently where
    appropriate.
3.  The system compares claims, definitions, dates, quantities, scope,
    and context.
4.  Findings are classified as agreement, contradiction, partial
    overlap, difference in scope, or insufficient evidence.
5.  Each finding includes source references from the relevant documents.
6.  The interface makes it clear when documents are not directly
    comparable.

## 7. Functional Requirements

### FR-01: Workspace and document library

-   Users can view documents, processing states, and relevant metadata.
-   The initial user model (single-user or authenticated multi-user)
    must be explicitly selected before implementation.
-   If multiple users are supported, every document and derived record
    must be scoped to an authorized workspace.
-   Search and citation endpoints must apply the same authorization
    rules as document endpoints.

### FR-02: PDF upload and validation

-   Accept PDF files only for the MVP.
-   Validate MIME/type signatures, size, and configured page/document
    limits.
-   Handle malformed, encrypted, empty, duplicate, and image-only PDFs
    with clear states.
-   Do not trust client-provided filenames or metadata.
-   File and page limits must be configurable to suit the selected
    hosting and storage free tiers.

### FR-03: Extraction and provenance

-   Extract text by page.
-   Preserve document ID, version, page number(s), and chunk provenance.
-   Report pages with no extractable text where detectable.
-   Preserve enough offsets or page metadata to display source excerpts
    reliably.
-   Extraction failures must not silently mark a document as fully
    indexed.

### FR-04: Chunking and embeddings

-   Chunking size and overlap must be configurable.
-   Chunk boundaries should preserve heading and paragraph context where
    feasible.
-   Record the embedding model/provider identifier and relevant vector
    dimensions.
-   Never mix vectors from incompatible embedding models in the same
    search index without explicit separation/migration.
-   Re-embedding must be possible when the embedding model changes.
-   Cache/reuse completed embeddings where safe and appropriate.

### FR-05: Vector storage and retrieval

-   Use PostgreSQL with pgvector if it fits the chosen free-tier plan;
    local PostgreSQL is an acceptable development fallback.
-   Retrieval must filter by authorized workspace and selected documents
    before returning evidence.
-   Configure top-k and retrieval thresholds; values must be evaluated
    rather than assumed optimal.
-   Record enough diagnostic metadata to evaluate retrieval quality.
-   Hybrid keyword/vector search and reranking are optional
    optimizations to add only when evaluation demonstrates benefit.

### FR-06: Evidence-grounded Q&A

-   The LLM receives retrieved passages and their source metadata as
    context.
-   Responses must not imply that a statement came from a source unless
    a supporting passage is provided.
-   The answer should distinguish direct evidence from inference.
-   If only part of the question is supported, answer the supported part
    and identify the unresolved part.
-   Instructions contained in PDFs must be treated as untrusted document
    content, not as system or developer instructions.

### FR-07: Citation contract and validation

-   Each citation must reference a real document ID/version and valid
    page or page range.
-   Displayed excerpts must match stored source text, allowing only
    documented normalization.
-   Invalid references must be rejected or omitted rather than
    fabricated.
-   Citation validity and claim support are separate checks.
-   The system must not label a claim as verified merely because a cited
    page exists.
-   The interface should let users inspect the relevant source passage
    and document context.

### FR-08: Abstention and conflicting evidence

-   If retrieved evidence is absent or insufficient, return an explicit
    insufficient-evidence response.
-   If sources disagree, present the disagreement and cite the relevant
    passages from each source.
-   If sources differ in scope, date, or definitions, surface those
    differences where identifiable.
-   Do not force a contradiction when sources are not directly
    comparable.
-   Evidence status labels may include Supported, Partially Supported,
    Conflicting Evidence, and Insufficient Evidence.
-   These labels describe evidence found by the system; they are not
    guarantees of truth.

### FR-09: Document summaries and suggested questions

-   Offer an optional concise summary and suggested questions after
    successful indexing.
-   Reuse cached outputs where the source version and model
    configuration match.
-   Summaries must be grounded in the document and cite key claims where
    practical.
-   If the AI quota is unavailable, document indexing must remain usable
    and summary generation can be deferred.

### FR-10: Cross-document comparison

-   Compare evidence for selected documents or topics.
-   Classify findings as agreement, contradiction, partial overlap,
    scope difference, or insufficient evidence.
-   Include citations for each finding and identify which document
    supports each side.
-   Do not silently merge incompatible dates, definitions, or units.

### FR-11: Document lifecycle, retry and deletion

-   Track statuses such as Uploaded, Queued, Processing, Indexed,
    Partially Processed, Failed, and Deleting/Deleted as appropriate to
    the implementation.
-   Allow safe retry of failed processing.
-   Retries must not create duplicate active chunks or vectors.
-   Re-upload/version behaviour must be defined: replacement or separate
    version.
-   Deletion must remove or invalidate source files, extracted text,
    chunks, embeddings, caches, summaries, and saved answer references
    according to the retention policy.
-   Clearly communicate any backup-retention limits that prevent
    immediate physical erasure from all backup media.

### FR-12: Saved history

-   Where persistence is enabled, users can revisit previous questions,
    answers, citations, and selected document scope.
-   Saved answers must identify the document versions and model
    configuration used.
-   Deleted or inaccessible documents must not remain available through
    cached answers or stale citations.

### FR-13: Search and filters

-   Provide document-library search and document selection for Q&A.
-   Add filters based on available metadata, such as document, page
    range, category, or date.
-   Semantic search must not be described as exact keyword search.
-   Exact keyword search or hybrid search may be added based on
    evaluation and implementation cost.

### FR-14: Usage and quota controls

-   Track generation and embedding usage separately where provider data
    permits.
-   Apply configurable per-request and per-user limits.
-   Handle rate limits, timeouts, unavailable models, and exhausted
    quotas with clear messages.
-   Do not silently switch to a paid service, paid model, or
    billing-enabled fallback.
-   Cache reusable results where safe; invalidate caches when source
    versions, permissions, or relevant model configuration changes.
-   The user must be able to operate the non-AI parts of the application
    when an AI quota is exhausted.

### FR-15: Evaluation

-   Include a curated demo dataset and questions with expected source
    passages.
-   Measure retrieval quality, citation validity, claim support,
    abstention, comparison support, latency, and error rates.
-   Run the same test suite against changes to chunking, embedding
    models, retrieval settings, prompts, or generation models.
-   Establish numerical release thresholds after measuring an initial
    baseline.
-   Report failures and regressions rather than hiding them behind an
    aggregate score.

### FR-16: Observability and error handling

-   Record request IDs, processing states, latency, error categories,
    and usage metadata where available.
-   Avoid logging raw document contents, secrets, or sensitive question
    text unless specifically necessary and protected.
-   Show actionable user-facing errors and keep detailed diagnostics in
    appropriately protected server logs.
-   Use bounded retries and timeouts to avoid runaway requests or
    duplicate work.

### FR-17: User interface and accessibility

-   Provide a responsive interface for document library, upload
    progress, Q&A, evidence inspection, comparison, and history.
-   Show processing, empty, partial-failure, quota-exhausted, and
    provider-unavailable states.
-   Support keyboard navigation, readable contrast, clear focus states,
    and accessible labels.
-   Keep evidence and citations easy to inspect without overwhelming the
    main answer.

## 8. Advanced Feature Backlog

These features are not required to complete the first MVP. Add them only
after the core pipeline and evaluation tests are reliable.

### 8.1 Retrieval improvements

-   Hybrid keyword-plus-vector search.
-   Reranking.
-   Query rewriting and query decomposition.
-   Context-aware or heading-aware chunking.
-   Retrieval diagnostics showing candidate passages and relevance
    signals.

### 8.2 Document intelligence

-   Version-to-version change detection and clause comparison.
-   Structured extraction of dates, amounts, obligations, requirements,
    entities, and other fields into tables or JSON.
-   Table-aware PDF extraction.
-   Knowledge-gap detection with suggestions for what information or
    document could answer an unresolved question.
-   Automatic document topic/category suggestions, subject to user
    review.
-   OCR for scanned/image-only PDFs.

### 8.3 Research workflow

-   Export evidence reports to Markdown and PDF.
-   Saved research collections and annotations.
-   Reusable question templates.
-   Batch question answering over selected documents.
-   Additional file formats after PDF workflows are stable.

### 8.4 Scale and collaboration

-   Background job queue where the deployment needs it.
-   Multi-user collaboration and role-based access beyond the initial
    scope.
-   More advanced audit trails and administration.
-   Additional deployment and storage options.

## 9. Technical Architecture

### 9.1 Proposed components

-   **Frontend:** Next.js.
-   **Backend API:** Python with FastAPI.
-   **Relational and vector data:** PostgreSQL with pgvector where
    available.
-   **PDF processing:** a suitable local PDF text extraction library.
-   **Embeddings:** hosted embedding API or local open-source embedding
    model.
-   **Generation:** hosted LLM API with an eligible free quota.
-   **Evaluation:** repeatable automated test suite and a curated
    dataset.

These are proposed choices, not guarantees that any particular
provider's free tier will meet all deployment needs. Provider limits,
model availability, data policies, and pricing must be checked before
implementation.

### 9.2 One-provider/one-key approach

Prefer a single AI provider and one API key for both embedding and
generation if the provider supports both endpoints for the chosen
account and models. Embedding and generation remain separate operations
and may use different models.

Requirements: - Keep model names/configuration separate. - Keep API keys
on the backend in environment variables or a suitable secret
mechanism. - Never expose keys in browser code, client bundles, logs, or
repository commits. - Track quota and errors per operation. - Ensure the
selected embedding model is consistent with the stored vector index. -
Do not silently fall back to a paid provider or model.

A local embedding model is an alternative if hosted embedding quotas are
too restrictive, provided the available hardware and latency are
acceptable.

### 9.3 Modular backend boundaries

Separate the implementation into modules for: 1. File validation and
document registration. 2. PDF extraction and provenance. 3. Chunking. 4.
Embedding generation. 5. Vector indexing and retrieval. 6. Evidence
sufficiency and context construction. 7. Answer generation. 8. Citation
validation. 9. Comparison. 10. Evaluation and observability.

Avoid introducing orchestration frameworks, agent systems, or complex
infrastructure without a demonstrated need.

## 10. Free-Tier-First Requirements

The MVP must be designed to operate within a selected set of free-tier
services or locally without requiring paid services for its normal demo
workflow.

### 10.1 Cost-control rules

-   No paid service is mandatory unless explicitly approved.
-   No silent paid fallback, automatic upgrade, or unbounded retry.
-   Configure file size, page count, document count, context size, query
    rate, and output length limits.
-   Cache embeddings and repeatable summaries where safe.
-   Limit the number of retrieved chunks sent to the LLM.
-   Track usage and show clear quota-exhaustion errors.
-   Support a local development mode that does not require always-on
    hosted infrastructure.
-   Keep provider-specific code behind small interfaces to ease
    replacement.

### 10.2 Free-tier uncertainty

Free quotas, availability, deployment sleep behaviour, storage limits,
and data-use terms can change. These are deployment decisions to verify
at implementation time, not permanent guarantees in this PRD.

## 11. Security, Privacy and Trust

-   Validate uploads and enforce size/type limits.
-   Store AI API keys only on the server.
-   Enforce workspace/document authorization in every backend operation.
-   Treat retrieved document text as untrusted input; defend against
    prompt injection and instruction-like content in documents.
-   Prevent unauthorized documents from appearing in retrieval,
    citations, cached answers, or exports.
-   Define data retention and deletion rules.
-   Avoid unnecessary document content in logs.
-   Document provider data handling and retention terms before using
    sensitive files.
-   Apply appropriate protections to stored files, database access, and
    secrets.
-   Make clear that ProofLens AI assists document review and does not
    guarantee truth or replace professional judgment.

For a local single-user demo, the security implementation may be
simpler, but secrets handling, upload validation, prompt-injection
defenses, and safe deletion remain relevant.

## 12. Non-Functional Requirements

### Reliability

-   Failures must be visible and recoverable where possible.
-   Retry operations must be bounded and idempotent.
-   Partial ingestion must not be reported as complete indexing.

### Performance

-   Set realistic file and request limits for the chosen environment.
-   Record extraction, embedding, retrieval, and generation latency
    separately where practical.
-   Define numerical latency targets after measuring the selected
    free-tier environment.

### Maintainability

-   Keep ingestion, retrieval, generation, validation, and evaluation
    separable.
-   Make chunking, retrieval settings, and model configuration
    adjustable without broad rewrites.
-   Document setup, environment variables, migrations, test commands,
    and troubleshooting.

### Accessibility and usability

-   Responsive layouts, keyboard access, focus visibility, accessible
    labels, and clear error messages.
-   Preserve source context so users can verify answers rather than
    trust a summary alone.

## 13. Data Model Requirements

At minimum, the data model should represent: - User or local profile, if
required by the chosen deployment mode. - Workspace or document
collection. - Document and document version. - Ingestion job/status and
failure details. - Page-level extracted text or page references. - Chunk
text and stable chunk identifiers. - Embedding vector and embedding
model identifier. - Source metadata, including page number(s) and
offsets where available. - Question and answer record, if history is
enabled. - Citations linked to document version and chunk/page. -
Evaluation cases and results. - Usage/operational metrics that do not
unnecessarily retain sensitive content.

The exact schema and migrations are implementation deliverables. Access
scope must be enforced consistently across all related records.

## 14. Acceptance Criteria

The MVP is acceptable for a demo/release candidate when:

1.  A user can upload multiple supported PDFs and view their processing
    status.
2.  Extracted text preserves page-level source provenance.
3.  Chunks and vectors are searchable within the permitted document
    scope.
4.  The system answers supported questions using retrieved evidence.
5.  Citations resolve to actual documents and valid pages/excerpts.
6.  The application does not present a citation as valid if its source
    reference is invalid.
7.  Questions with insufficient evidence trigger a clear abstention or
    qualification.
8.  Conflicting sources are shown with evidence from the relevant
    documents.
9.  Basic cross-document comparison returns evidence-backed findings.
10. Failed ingestion can be retried without duplicate active index
    entries.
11. Deletion removes or invalidates associated searchable data and
    cached outputs according to policy.
12. Provider failures and quota exhaustion produce controlled,
    understandable errors.
13. The configured free-tier policy prevents silent paid usage.
14. Automated tests cover retrieval, citations, abstention, access
    isolation, deletion, and failure recovery.
15. A repeatable evaluation dataset and baseline report are included.
16. No API keys or secrets are committed or exposed to the frontend.
17. Setup and troubleshooting documentation allows the project to be run
    reproducibly.
18. A demo dataset is provided with expected evidence and representative
    questions.

Numerical quality and latency thresholds must be finalized after a
baseline run. Passing functional tests does not imply guaranteed factual
accuracy.

## 15. Testing and Evaluation Plan

### Functional tests

-   Upload valid, malformed, encrypted, empty, oversized, and duplicate
    PDFs.
-   Verify extraction and page mapping.
-   Verify indexing and retry idempotency.
-   Verify document filtering and authorization.
-   Verify citation navigation and source excerpt matching.
-   Verify summaries, Q&A, comparison, and history where implemented.
-   Verify deletion and cache invalidation.

### RAG quality tests

-   Questions with explicit answers in one document.
-   Questions requiring evidence from multiple documents.
-   Paraphrased questions whose wording differs from the source.
-   Questions with no answer in the corpus.
-   Questions where documents disagree.
-   Questions where a superficially similar passage is irrelevant.
-   Questions requiring dates, quantities, or definitions to be kept
    distinct.

### Security tests

-   Prompt-injection-like instructions inside PDFs.
-   Attempts to retrieve documents outside the permitted scope.
-   Invalid citation/document/page IDs.
-   Secret exposure checks.
-   Attempts to access deleted content through cached history.

### Evaluation reporting

Report metrics and representative failures. Keep the dataset and
configuration stable enough to compare versions. Numerical pass
thresholds are a release decision based on observed baseline
performance.

## 16. Delivery Milestones

### Milestone 0 --- Repository discovery and plan

-   Inspect the existing repository, project instructions, dependency
    versions, and Git status.
-   Identify existing code and user changes.
-   Map the current implementation against this PRD.
-   Report architecture, gaps, risks, free-tier assumptions, and
    proposed file changes.
-   **Stop for approval before implementation.**

### Milestone 1 --- Application skeleton

-   Establish frontend/backend structure and local setup.
-   Configure environment variables and health checks.
-   Establish database migrations and basic tests.

### Milestone 2 --- PDF ingestion and provenance

-   Implement upload validation, extraction, page metadata, chunking,
    statuses, retry, and deletion.

### Milestone 3 --- Embeddings and retrieval

-   Implement the selected embedding strategy, vector index, scope
    filters, and retrieval tests.

### Milestone 4 --- Grounded Q&A and citation validation

-   Add generation, evidence sufficiency, abstention, structured
    response handling, and source inspection.

### Milestone 5 --- Comparison and core UX

-   Add cross-document comparison, summaries/suggested questions where
    feasible, saved history if in scope, and polished responsive states.

### Milestone 6 --- Evaluation, security and demo readiness

-   Run the quality and security test suite, measure baseline metrics,
    document known limitations, and provide demo materials.

### Later milestones

-   Add advanced retrieval, version intelligence, structured extraction,
    OCR, and report export based on user priorities and measured need.

## 17. Unresolved Decisions

These decisions must be recorded before the affected implementation
begins:

1.  **Deployment:** local-only, public online free-tier deployment, or
    both.
2.  **User model:** single-user initially or authenticated multi-user
    workspaces.
3.  **LLM provider and models:** confirm generation and embedding model
    availability, quotas, data policies, and one-key support.
4.  **Embedding strategy:** hosted API or local model.
5.  **Database:** hosted PostgreSQL/pgvector or local PostgreSQL for
    development.
6.  **Storage:** local files or an eligible hosted free-tier object
    store.
7.  **Limits:** maximum file size, page count, documents, chunks, and
    query frequency.
8.  **OCR:** explicitly excluded from MVP or included for a defined
    subset.
9.  **Retention:** data deletion, saved history, backup policy, and
    provider data handling.
10. **Quality thresholds:** set after the initial evaluation baseline.
11. **Target demo use cases:** choose representative documents and
    questions.

Do not assume an unresolved decision has been approved. Use conservative
defaults for local development and document any assumptions in the
implementation plan.

## 18. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Retrieval misses the relevant       Curate evaluation cases; tune
  passage                             chunking and retrieval; consider
                                      hybrid search only if useful

  LLM produces unsupported claims     Constrain answer context, validate
                                      citations, test claim support, and
                                      abstain when necessary

  Citation points to the wrong page   Preserve provenance from extraction
                                      through display and test page
                                      mappings

  Free quota is exhausted             Track usage, cache reusable work,
                                      limit calls, and show clear quota
                                      states

  Free hosting sleeps or imposes      Support local development and
  limits                              verify deployment constraints
                                      before choosing services

  Prompt injection in document text   Treat retrieved text as untrusted
                                      evidence and keep instructions
                                      separated

  Document is updated or deleted      Version sources, invalidate stale
                                      caches, and clean derived data

  Scope expands too far               Keep advanced features in the
                                      backlog and prioritize core RAG
                                      acceptance criteria
  -----------------------------------------------------------------------

## 19. Definition of Done

A feature is done only when: - Its requirements and failure states are
implemented. - Relevant automated tests pass. - Source provenance and
access controls are preserved. - Usage and free-tier implications are
understood. - Errors are handled clearly. - Documentation is updated. -
No secrets are exposed. - Existing working functionality and user
changes are preserved. - The implementation is evaluated against the
acceptance criteria.

## 20. Final Product Definition

**ProofLens AI is a free-tier-first, evidence-first RAG document
intelligence platform that helps users ask questions across multiple
PDFs, inspect page-level supporting evidence, compare claims between
sources, extract structured information, and identify when the available
documents are insufficient to support a conclusion.**

The MVP prioritizes reliable ingestion, provenance, retrieval, grounded
generation, citation validation, abstention, basic comparison,
evaluation, and safe free-tier operation. Advanced retrieval and
document intelligence features are added only after the core system is
measurable and reliable.
