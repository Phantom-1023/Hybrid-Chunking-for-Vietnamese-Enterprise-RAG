# PPTX Build Notes - English Version

PowerPoint file: `CAPSTONE_OS/04_OUTPUT/slides/RAG_ENTERPRISE_REVIEW2_EN.pptx`

This is the English version required for school presentation. The Vietnamese deck is kept unchanged as a backup.

## Slide map

1. **Title** - Introduce the project as a demoable and measurable MVP, not a production system.
2. **Problem: Vietnamese Enterprise RAG** - Explain why LLM answers need source grounding.
3. **Research Question** - State the comparison of fixed, recursive, semantic, and paragraph chunking.
4. **Review 1 Response** - Show that the MVP responds to dataset, prototype, and pipeline feedback.
5. **Dataset: sailor2/Vietnamese_RAG** - Explain the public dataset and why it avoids enterprise data permission risk.
6. **System Architecture** - Walk through dataset, chunking, embedding, ChromaDB, query, and answer.
7. **Four Chunking Strategies** - Explain each strategy and mention semantic fallback honestly.
8. **Indexing Pipeline** - Explain four separate ChromaDB collections and metadata.
9. **Query Pipeline + Source Evidence** - Explain query embedding, retrieval, generation, and source chunks.
10. **Streamlit Demo** - Explain manual question, real dataset mode, benchmark tab, and source chunks.
11. **Evaluation-lite Benchmark** - Show real avg_score chart: fixed 0.3344, recursive 0.3410, semantic 0.3313, paragraph 0.8354.
12. **Result: Paragraph currently leads in MVP** - Explain paragraph is best only in the current evaluation-lite run.
13. **Limitations** - Clearly state no full RAGAS yet, small sample size, semantic fallback, `gemini-embedding-001` patch, and no production enterprise upload.
14. **Enterprise Roadmap** - Future work: full RAGAS, larger samples, enterprise upload, Hybrid Search, Reranking, GraphRAG / Agentic RAG.
15. **Conclusion + Next Steps** - Close with MVP status and next scientific/engineering tasks.

## Must-say warning

Say this sentence when presenting the benchmark:

"This is evaluation-lite on 5 samples, not full RAGAS. It is useful for checking MVP retrieval behavior, but it is not the final scientific conclusion."

## Do not say

- Do not say full RAGAS is completed.
- Do not say paragraph is generally the best strategy.
- Do not say the system is production-ready for enterprises.
- Do not say enterprise document upload is already implemented.
- Do not hide the temporary `gemini-embedding-001` execution patch.
