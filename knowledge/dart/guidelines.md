# Dart guidelines

## Architecture and style
Use Clean Architecture and develop behavior through failing tests first. Keep
pure domain decisions separate from infrastructure. Use dartz Task, Either and
Option to model deferred effects, expected failures and optional presence.
Use expressions, folds and pattern matching; do not introduce if/else, loops or
mutable state in new Dart code. Preserve project approval and deletion gates.

## Routing
Read dart/task for asynchronous effects, dart/option for optional values and
dart/either for expected failure. Confirm the project's pinned dartz version and
source signatures. Do not assume fpdart TaskEither APIs exist in dartz. Adapt at
framework boundaries without weakening domain contracts.

## Verification
Test lazy execution, both success/failure paths, both presence/absence paths,
sequencing and effect boundaries. Use deterministic fakes for external effects.
Run the project's configured Dart analysis and tests before claiming completion.
