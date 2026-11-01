# Verification

## Define success
Turn the request into observable acceptance criteria. Reproduce bugs before
fixing them. Exercise invalid inputs, expected failure, absence and boundary
behavior as appropriate. Run the project's relevant tests and static checks.

## Evidence
Record the command, working directory, real exit code and what the check proves.
A passing whitespace check does not prove tests pass. A check that ran before a
later edit is stale. Report failed, skipped, unavailable or inconclusive checks
plainly. Never claim completion solely because a hook permitted a tool call.

## Project verification
Choose checks from the task's acceptance criteria and the project's existing
workflow. Report their actual commands, outcomes and limits. Follow explicit
project or development-harness verification requirements where provided.

The guidance plugin loads references; it does not register a completion hook,
run a verifier, demand a receipt, or require shell tools to write plugin state.
A read-only inspection command does not create a new testing requirement.
