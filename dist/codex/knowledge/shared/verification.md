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

## Hook completion gate
For guarded changes, run the bundled enforcement/verify.py command supplied by
the hook. Project .monolithic-guidelines.json may define verification_commands as
a nonempty list of argument arrays. The runner executes only on explicit request,
without a shell, and records actual outcomes for the current change generation.
The git-project fallback is git diff --check, which checks whitespace only.
Configure meaningful project checks; do not weaken an existing check to get a
passing receipt. A repeated Stop hook permits a blocked-status response to avoid
an endless continuation loop; it does not turn missing evidence into success.
