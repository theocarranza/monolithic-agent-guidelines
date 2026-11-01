# Functional programming

Adapted from the supplied Functional Programming note. Follow language and project
rules when they impose stricter requirements than this general guidance.

## Principles
Make decisions from explicit inputs. Keep domain calculations deterministic and
put clock, random, network, database and filesystem access at visible boundaries.
Represent meaningful outcomes as typed values. Prefer immutable values and small,
named compositions. Inject narrow capabilities to make effects testable. Reuse
useful existing abstractions; introduce generic abstractions when real reuse or
clearer contracts justify them.

In projects that permit it, a local loop or mutation may be simpler. This does
not relax the strict Dart requirements in dart/guidelines.

## One behavior, one authoritative implementation
Keep a single processing and execution flow for the same behavior. Isolate
differences in data sources, storage and external services behind adapters with
a common contract. Pass those inputs or capabilities into the shared flow. Do
not create parallel implementations of the same business rules for different
sources, entry points or test environments.

Share behavior because its meaning is the same, not merely because code looks
similar. Legitimate decisions, success/failure outcomes and different business
strategies remain explicit. Determinism means the same input produces the same
output; it does not prevent duplicated implementations. Read
shared/canonical-behavior when designing or reviewing adapters, data sources,
entry points, workflows or test dependencies.

## Verification
Test observable behavior independently of external effects. For algebraic
structures, test the laws within the actual representation's limits. A deferred
Task or a Promise return type alone does not make an effectful computation pure.
