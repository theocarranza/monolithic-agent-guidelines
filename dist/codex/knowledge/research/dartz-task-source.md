# Dartz Task source evidence

Source: user-supplied Task Type.md, an unversioned implementation excerpt.
This is evidence for the attached implementation, not a claim about all releases.

Observed signatures and behavior:

- Task stores Function0<Future<A>>; run() calls that function.
- flatTap<B>(Task<B> that) delegates to productL(that).
- both calls Future.wait([_run(), that._run()]) without eagerError=true.
- race calls Future.any on tagged successful results.
- guarantee uses Future.whenComplete; bracket composes acquire/use/release.
- Static tupledN/parTupledN/mapN methods are absent from the supplied class.

The adapted Task reference corrects callback-style flatTap, fail-fast both,
first-completion race and blanket referential transparency claims. Read the
installed project's actual dartz source before expanding this API surface.
