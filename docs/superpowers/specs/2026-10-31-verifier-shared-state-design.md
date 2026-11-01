# Verification shared-state patch (1.3.2)

User-approved scope: pass the exact hook state directory to explicit verification,
keep narrow sandbox write access subject to user approval, and verify the full
adapter lifecycle before publishing. No live user configuration/permissions edited.

Root cause: hooks can receive PLUGIN_DATA while shell tools do not. Commands in
1.3.1 passed only a session key and workspace; the verifier inferred another base,
then either could not write its lock or loaded an unrelated/empty session.

Implementation: --state-dir carries StateStore.directory. The hook includes an
absolute path and preserves quoting; an explicit directory overrides environmental
defaults. Legacy manual commands retain the optional environmental default. Both
verification transactions require an existing record (checked before and after
locking), and still validate workspace, generation, task epoch and check config.
Final directory symlinks remain rejected; argument normalization preserves them.

Write denial (EROFS/EACCES/EPERM) identifies the directory and advises requesting
access only there. The hook and setup may explain local codex --add-dir with that
exact path, but cannot grant it or change global settings. The grant belongs to
the launched session; it does not reconfigure an existing desktop process. Do not
recommend full-access mode or filesystem permission changes.

Tests: hook block/retry, command propagation without hook-only environment,
missing-record refusal without creating a new session, deleted-record race,
symlink refusal, configured check execution, failure evidence and final Stop.
Read-only and permission failures are injected at the lock open boundary, and
Stop stays blocked until successful verification. Independent review identified
that privilege dropping cannot use unmapped UID/GID values; the optional real
unprivileged permission test is skipped here because uid_map/gid_map expose only
root. Bubblewrap cannot create namespaces on this host, and Landlock is unavailable.
Consequently native Codex sandbox execution is explicitly unverified, not inferred
from the passing protocol tests. Native Codex 0.166.0 discovery still lists all six
hooks without errors. User-machine scoped access remains the final live test.
