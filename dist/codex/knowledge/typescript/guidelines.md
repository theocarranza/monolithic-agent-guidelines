# TypeScript guidelines

Adapted from the supplied TypeScript Functional Programming note. Its original
projects/functions scope is not a dependency requirement for other repositories.

## Domain and boundaries
Prefer pure domain calculations, readonly data, discriminated result unions and
exhaustive switches. Represent expected failure and absence explicitly using the
project's existing types. Validate unknown input at boundaries with the existing
validation library; use Zod when the project already uses it. Framework exceptions
belong at boundaries that require them.

## Composition
Name meaningful predicates and use type guards rather than casts that hide errors.
Inject narrow effect capabilities. Reuse existing sequencing/concurrency helpers
when available; mapWithConcurrency is a source-project example, not a standard API.
Local loops and mutation are acceptable only where the project's rules allow them
and they improve clarity. Do not apply this exception to strict Dart code.
Do not add fp-ts, higher-kinded type machinery or a new result abstraction merely
to reproduce these examples. Existing project architecture takes precedence.

## Routing
Read typescript/effects for external effects and deterministic testing,
typescript/monoids for structured aggregation, examples/typescript for a small
portable example and research/functional-patterns for background rationale.
