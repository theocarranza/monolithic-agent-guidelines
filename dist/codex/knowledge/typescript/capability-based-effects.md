# Capability-based effects in TypeScript

Adapted from the supplied Capability-Based Effects in TypeScript note.

## Rules
Separate decisions from external effects. Inject the smallest useful interface;
provide production implementations at the composition boundary and deterministic
fakes in tests. Keep error handling aligned with the surrounding contract.
A generic interpreter is useful when real implementations justify it, not merely
because one function reads a clock.

## Example
```ts
interface Clock { readonly now: () => Date }
const reportTime = (clock: Clock): string => clock.now().toISOString();
const fixedClock: Clock = { now: () => new Date("2026-01-01T00:00:00Z") };
```

This makes time access explicit and replaceable. The injected operation remains
an effect; its function signature alone is not proof of purity.
