# Monoids in TypeScript

Adapted and corrected from the supplied Monoids in Functional TypeScript note.

## Laws
A monoid combines values associatively and has an identity. Check
concat(concat(a,b),c) = concat(a,concat(b,c)) and concat(empty,a) = a = concat(a,empty).
Use reduce from the identity for possibly empty collections. Combine record fields
only when every field's operation makes sense for the domain.

## Representation limits
JavaScript number addition is not generally associative because of floating-point
rounding. Integer sums are safe only while all intermediate values remain exactly
representable. Use bounded exact domains or bigint where appropriate, and test the
actual representation. Do not assume durations with fractions obey exact laws.

## Reuse
Reuse structMonoid and concatAll only if the repository actually provides them.
Do not add a functional library solely for a short reduction. Rightmost-provided
configuration overrides are lawful only when absence and precedence are explicit.
