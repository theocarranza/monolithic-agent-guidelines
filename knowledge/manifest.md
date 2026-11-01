# Monolithic Agent Guidelines knowledge

Machine version and schema: [manifest.json](manifest.json). Routing:
[catalog.tsv](catalog.tsv). Sources are bundled with this release; retrieval never
needs a network connection. Catalog provenance distinguishes original principles,
user-provided notes adapted for portability, and new guidance composed for this
plugin. No project identity or ownership information is imported from the example
knowledge store.

The four principles are preserved from the original skill. Functional references
are decision support for goal-driven execution. Existing project requirements,
permissions and explicit approval gates prevail. Specific language requirements
prevail over permissive shared examples. Do not infer a library dependency or a
project helper from these references.

Dartz references use the supplied Task implementation as evidence, with minimal
Option/Either guidance. Check the project's pinned library source before using
APIs beyond those shown. Examples are illustrative, not compiled compatibility
tests against every version of Dart or TypeScript.

The store adapts the user's catalog → find → fetch example. Runtime retrieval is
read-only. Every fetch returns provenance, version, document hash and content
hash, including section fetches. This metadata establishes the retrieved artifact;
it does not certify all upstream claims or replace project tests.
