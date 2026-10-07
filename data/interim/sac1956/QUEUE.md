# Transcription queue (orchestrator notes)

Concurrency target: 10 background agents. Prompt: read INSTRUCTIONS.md; chunk file; pass dir;
"run the completeness check first and skip pages already OK".
Pass A = default model -> data/interim/sac1956/passA
Pass B = model "sonnet" -> data/interim/sac1956/passB  (trial: 72/72 data lines identical to default model)

18:50 UTC: all 10 agents killed by the account usage limit (reset 19:10). Pages are written one at
a time, so only in-flight pages were lost. 19:35 UTC relaunch:
  pass B resume: 07 05 09 10 03 11      pass A: 15(resume) 16 17 18
Pass A complete chunks: 01-26. Remaining A: 27 28 (running), 29. Note: C219, C247 skewed (merged rows).
Pass B complete chunks: 01 03-19. Remaining B: 02 20 21 22 23 24 25 26 (running), 27-29.
Policy: favour pass B (slower). When a slot frees: pass B next of 02,12,13,...; pass A next of 19-29.
Check progress: .venv/bin/python scripts/sac1956_chunks.py check passA  (and passB)
Interim agreement (20:50 UTC, pages in both passes): 7045/7127 data lines = 98.85%; airfield chunks 01-02 lowest (89-94%), city chunks 97-100%.
