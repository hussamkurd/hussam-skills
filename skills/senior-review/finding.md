# The finding

Every lane returns findings in this shape, and the main agent's decision step reads them as they are.

## Evidence

A claim that something works or breaks needs proof from this session: a command and its output lines, a `file:line` quote, or a screenshot path. Without proof the claim is **unverified**: say why, and name the check that would settle it. Unverified never counts as working.

## Shape

Write the title as the change itself, verb first, so the reader knows what will happen from the title alone.

```
Title:      Add a 5 second timeout to the payment call
Severity:   critical | code | trivial
Where:      src/payments/client.ts:42
Today:      fetch() has no timeout, so a slow provider holds the worker forever.
Change:     - const res = await fetch(url)
            + const res = await fetch(url, { signal: AbortSignal.timeout(5000) })
Why:        Stops one slow provider from blocking every checkout.
Evidence:   client.ts:42 quote, and the stub test: request still open after 60s.
Check:      the stub test with a 60s delay fails the request within 6s.
If skipped: Checkout hangs during any provider slowdown.
```

`Check` is a command, test name, or grep that passes once the change is in. It becomes the spec's "Done when".

A trivial finding needs only Title, Severity, Where and Change: its Where is the evidence. A code finding names the broken principle in Why.

## Severity

- **critical**: production breaks, loses data, hangs, leaks, is insecure, misses the requirement, cannot be rolled back, or fails wide.
- **code**: a principle the project follows is broken, the code is over-built, duplicated, or split up for no reason, or tests or logs are missing. A weak safety answer with a small blast radius lands here too.
- **trivial**: churn, dead code, ticket keys or narration in comments, agent and working files added to the change.

Keep a finding only when it fits one of these. Taste-level style and naming are not findings. A clean change with no findings is a fine result.
