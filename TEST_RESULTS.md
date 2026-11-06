# Test Results

Command: `python -m pytest -v`  ·  Run on 2026-11-03  ·  Python 3.13, in the build workspace.

**Environment caveats (honest notes)**
- Hugging Face returned 403 in this workspace, so tests ran with the **offline hashing embedder**, not Sentence Transformers.
- Official government sites were unreachable, so tests use tiny fixture PDFs/rows created in temporary folders. They prove the code
  works; they do **not** prove behaviour on the real CGWB files. Re-run the suite on your machine, then try your real downloads.
- LLM calls are mocked; no live LLM API was called.
- A separate smoke test loaded all 7 Streamlit pages (empty and with temporary fixtures) and ran one chat turn with no exceptions.

## Raw output
```
platform linux -- Python 3.13.18, pytest-9.1.1, pluggy-1.6.0 -- /usr/local/bin/python3
plugins: platformdirs-4.13.3, anyio-4.15.1, langsmith-0.14.17
tests/test_analytics.py::test_coverage_summary PASSED                    [  2%]
tests/test_analytics.py::test_state_summary_values PASSED                [  4%]
tests/test_analytics.py::test_filters PASSED                             [  7%]
tests/test_analytics.py::test_yearly_and_quarterly PASSED                [  9%]
tests/test_analytics.py::test_compare_years PASSED                       [ 11%]
tests/test_analytics.py::test_linear_trend PASSED                        [ 14%]
tests/test_analytics.py::test_charts_build PASSED                        [ 16%]
tests/test_data.py::test_valid_frame_ok PASSED                           [ 19%]
tests/test_data.py::test_missing_required_column PASSED                  [ 21%]
tests/test_data.py::test_empty_dataset PASSED                            [ 23%]
tests/test_data.py::test_duplicates_detected_and_removed PASSED          [ 26%]
tests/test_data.py::test_missing_values_reported_not_filled PASSED       [ 28%]
tests/test_data.py::test_bad_dates_flagged PASSED                        [ 30%]
tests/test_data.py::test_out_of_range_flagged_but_kept PASSED            [ 33%]
tests/test_data.py::test_unit_consistency PASSED                         [ 35%]
tests/test_data.py::test_load_dataset_with_aliases_and_register PASSED   [ 38%]
tests/test_data.py::test_load_dataset_errors PASSED                      [ 40%]
tests/test_rag.py::test_extract_text_and_page_numbers PASSED             [ 42%]
tests/test_rag.py::test_chunks_keep_document_and_page PASSED             [ 45%]
tests/test_rag.py::test_blank_pages_skipped_but_numbers_preserved PASSED [ 47%]
tests/test_rag.py::test_pdf_without_text_raises PASSED                   [ 50%]
tests/test_rag.py::test_corrupt_and_missing_pdf PASSED                   [ 52%]
tests/test_rag.py::test_clean_text PASSED                                [ 54%]
tests/test_rag.py::test_chunk_size_respected PASSED                      [ 57%]
tests/test_rag.py::test_embeddings_shape_norm_determinism PASSED         [ 59%]
tests/test_rag.py::test_similar_text_scores_higher PASSED                [ 61%]
tests/test_rag.py::test_retrieval_returns_correct_page PASSED            [ 64%]
tests/test_rag.py::test_vector_store_persists PASSED                     [ 66%]
tests/test_rag.py::test_keyword_search_and_delete PASSED                 [ 69%]
tests/test_rag.py::test_empty_store_search PASSED                        [ 71%]
tests/test_rag.py::test_answer_without_llm_is_extractive_and_cited PASSED [ 73%]
tests/test_rag.py::test_citations_only_reference_real_pages PASSED       [ 76%]
tests/test_rag.py::test_make_citations_deduplicates PASSED               [ 78%]
tests/test_rag.py::test_insufficient_evidence_is_honest PASSED           [ 80%]
tests/test_rag.py::test_empty_question_rejected PASSED                   [ 83%]
tests/test_rag.py::test_llm_mode_uses_retrieved_context PASSED           [ 85%]
tests/test_rag.py::test_llm_failure_falls_back_with_message PASSED       [ 88%]
tests/test_rag.py::test_chat_http_errors PASSED                          [ 90%]
tests/test_rag.py::test_ingest_failures_and_duplicates PASSED            [ 92%]
tests/test_rag.py::test_followup_is_condensed_and_retrieves PASSED       [ 95%]
tests/test_rag.py::test_standalone_question_not_changed PASSED           [ 97%]
tests/test_rag.py::test_clear_and_export PASSED                          [100%]
============================== 42 passed in 1.48s ==============================
```
