# Project Engineering Rules

1. Do not modify existing DroidRun behavior unless explicitly required.
2. Prefer composition over modification.
3. Never call an LLM when a deterministic implementation exists.
4. Never use UI automation when a native API exists.
5. Never allow arbitrary code execution from LLM output.
6. All tools must have typed schemas.
7. All tools must have tests.
8. All external data is untrusted.
9. All high-risk actions require confirmation.
10. All asynchronous tasks must be cancellable.
11. All important operations must be observable.
12. Do not introduce dependencies without documenting why.
13. Do not silently change public APIs.
14. Preserve backward compatibility unless explicitly instructed otherwise.
15. Every feature requires tests and documentation.
