# Dartz Either

New companion guidance for the supplied Task and Option notes. Verify signatures
against the project's pinned dartz source before extending these examples.

## Expected outcomes
Either<L, R> makes expected failure explicit. Use left(failure) and right(value),
with domain failure types rather than unstructured error strings where practical.
Use Option for ordinary absence; use Either when callers need the reason.

## Composition
Use map to transform success and flatMap to compose an Either-producing operation.
Use fold((failure) => ..., (value) => ...) to consume both alternatives as an
expression. Keep exceptions at external boundaries and translate them into typed
outcomes. Avoid throwing an expected domain failure through a successful branch.

## Deferred work
Use Task<Either<Failure, Value>> when both deferred execution and typed failure
are needed. A Task<Either> has two layers: distinguish Task execution errors from
an Either.Left produced successfully. Do not silently discard either error path.
Test both layers and preserve the original failure information needed by callers.
