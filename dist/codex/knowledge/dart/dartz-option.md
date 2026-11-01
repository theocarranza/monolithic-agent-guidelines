# Dartz Option

Adapted from the supplied Dartz Option Agent Reference. Keep the portable surface
small; inspect the pinned version before using less common combinators.

## Presence and absence
Use Option<A> for optional presence that must compose. some(value) represents
presence, none<A>() absence and optionOf(nullable) adapts a nullable boundary.
Do not branch with isSome/isNone in new strict functional code.

## Composition and consumption
Use map for a pure value transformation and flatMap for an Option-producing
function. Use fold(() => fallback, (value) => use(value)) to consume both cases.
Use toEither(() => failure) when absence becomes a meaningful domain failure.
Keep nullable representations at framework or external boundaries where required.
Test both branches and ensure absence skips dependent effects.
