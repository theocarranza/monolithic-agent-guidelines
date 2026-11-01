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

## Verification
Test observable behavior independently of external effects. For algebraic
structures, test the laws within the actual representation's limits. A deferred
Task or a Promise return type alone does not make an effectful computation pure.
