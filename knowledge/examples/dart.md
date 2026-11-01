# Dart example

Illustrative strict functional composition; imports and domain types depend on
the consuming project. Validate against the pinned dartz version.

```dart
Option<String> normalizedName(String? raw) =>
    optionOf(raw).map((value) => value.trim()).filter((value) => value.isNotEmpty);
```

Test null, empty, whitespace and a nonempty name. Convert absence to an Either
only when the domain requires a failure reason. This example grants no exemption
from project validation or architecture rules.
