# Functional patterns research

Sources: supplied Functional Patterns From FP-TS and TypeScript Functional Style
Examples notes. The former records fp-ts commit c0a6472 as its research baseline.
These notes inform references; they do not prescribe dependencies or local APIs.

Useful patterns: typed outcomes, boundary validation, named predicates, explicit
nonempty collections, capability injection, lawful aggregation and exhaustive
handling. Generic abstractions should earn their place through useful contracts
and reuse. Promise and Task types alone do not establish purity. Choose effect
boundaries from behavior, not names such as check/assert/apply.

The original research mentions project helpers, Zod, framework errors and reports.
Those are contextual examples. This plugin does not import the original project's
identity, ownership, code paths, operational policy or undocumented assumptions.
