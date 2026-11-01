# TypeScript example

Portable adaptation of the supplied TypeScript Functional Style Examples.

```ts
type Result<E, A> =
  | { readonly ok: true; readonly value: A }
  | { readonly ok: false; readonly error: E };

const nonempty = (text: string): Result<string, string> =>
  text.trim().length === 0
    ? { ok: false, error: "Name is required" }
    : { ok: true, value: text.trim() };
```

Reuse an existing project result type instead of duplicating this one. Test both
outcomes. Keep validation pure and perform persistence only at an explicit boundary.
The supplied source's project paths and framework-specific transaction examples
are not universal requirements.
