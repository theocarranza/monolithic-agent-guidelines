# Dartz Task

Adapted and corrected from the supplied Dartz Task Agent Reference and Task Type
source. Source evidence is recorded in research/dartz-task-source.

## Laziness
Task<A> wraps a function producing Future<A>. Constructing a task does not call
that function. Each run() invokes it again; results are not memoized. A closure
that captures mutable external state is not automatically referentially pure.
Call run() at the application boundary.

## Composition
Use map for A → B and flatMap/bind for A → Task<B>. andThen sequences independent
effects while discarding the first value; product keeps both results sequentially.
replace keeps the effect but substitutes a value.

In the supplied source flatTap accepts a Task<B>, not a callback. For a dependent
effect that preserves its input, use:

```dart
source.flatMap((value) => effect(value).replace(value));
```

Do not assume static tupledN, parTupledN or mapN methods are available: they are
absent from the supplied Task class. Verify the pinned library before using them.

## Errors and resources
attempt() produces Task<Either<Object, A>>. Map the task's result and transform the
Either's left value with the project's verified API. handleErrorWith composes a
recovery Task. bracket/guarantee arrange finalization; finalizer failures can
replace the original error, so test the required behavior.

## Concurrency
both starts both tasks and uses Future.wait without eagerError=true in the
supplied implementation. It waits for all futures rather than failing immediately.
race uses Future.any and returns the first successful tagged result; earlier
errors do not necessarily win. Neither operation cancels losing work.
