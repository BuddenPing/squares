# PingYou Ltd: 145 finite rational certificate refinements

This external submission requests review and registration of 145 complete rational
square-packing certificates.
Each is strictly smaller than the strongest retrieved complete rational public
certificate in the dated comparison.
The claim includes reductions of certificate padding and tighter realizations of known
constructions.
It does not claim 145 new nominal packing designs, and it does not replace
known algebraic or unpadded nominal bounds.

The [claims](claims.json) give each exact side, upward decimal, archive members,
historical and current comparisons, and source credits.
The [comparison](comparison.json) accounts for all 149 audited candidates.
Counts 105, 146 and 261 are omitted from the request because the same certificate side
is already public. Count 154 is held back because
[a stronger pending report](https://github.com/jlevy/squares/issues/570) was found but
its linked certificate could not be retrieved.
The full audit of the historical bank and all 149 dispositions accompany the 145
requested certificates.
Earlier reports for 153, 207, 272 and 302 are linked in their claim rows; these are
certificate updates to those constructions.

## Source and custody

The versioned
[source release](https://github.com/BuddenPing/square-packing-certificates/releases/tag/data/pingyou-numerical-refinements-2026-10-13-v1)
is versioned `data/pingyou-numerical-refinements-2026-10-13-v1`. The
[HostedData manifest](../../../hosted/pingyou-numerical-refinements-2026-10-13.yaml)
records each asset’s location, byte size and SHA-256. The portable archive contains the
exact centre/half-angle certificates, current public comparison certificates, source
provenance, exact comparison and verification receipts.
The native archive contains complete rational-corner Witness/v2 encodings.
Downloaded bytes are checked at the external-data boundary; no program needs Git history
to reconstruct the geometry.

The unchanged upstream verification software retains its license in `native/upstream/`.
This submission asserts no new blanket license grant over the contributed geometry or
the retained source material.

## Reproduce

Use the repository’s pinned Python 3.14 environment.
From `packing/`, fetch the two assets with the maintained hosted-data tool:

```sh
uv run --frozen --all-extras --group dev python -m devtools.hosted_data fetch --manifest hosted/pingyou-numerical-refinements-2026-10-13.yaml
```

Extract both archives beneath `attic/pingyou-numerical-refinements-2026-10-13/` at the
repository root, retaining their internal paths.
The portable archive’s README documents the full standard-library replay:
`python VERIFY.py` from its `numerical-refinements/` directory checks all 145 submitted
certificates and their current comparison certificates with exact rational SAT and
polygon intersection, plus invalid containment and overlap controls.

For every requested row in `claims.json`, run both native routes on its `native_witness`
member. For example, from `packing/`:

```sh
uv run --frozen packing-witness verify ../attic/pingyou-numerical-refinements-2026-10-13/native/witnesses/pingyou-n153-rational.yaml --json
uv run --frozen python -m devtools.check_rational_witness_independent ../attic/pingyou-numerical-refinements-2026-10-13/native/witnesses/pingyou-n153-rational.yaml
```

The finite claim is one complete roster of `n` exact unit squares within the stated
square, with all `n(n-1)/2` unordered pairs checked.
Higher precision alone is not the validation criterion.
The converter uses exact rational arithmetic: for half-angle `t`, `c=(1-t*t)/(1+t*t)`
and `s=2*t/(1+t*t)` determine cyclic corners without changing the centre or the
enclosing side.

## Evidence and limits

The contributor’s full portable replay accepted all 149 candidates and all 149
historical baselines: 2,724,160 unordered pairs per implementation in each group.
Invalid containment and overlap controls were rejected.
Detailed contributor receipts and native replay results are in the source release; these
are evidence for review, not an assignment of the repository’s confirmation or
significance ratings.

Both unchanged native verifier implementations accepted all 145 requested witnesses,
covering 2,662,404 unordered pairs per implementation.
Native replay and conversion receipts are included in the native archive.

The SAT and polygon routes share rational source data and the standard-library fraction
type. They decide overlap by different geometric calculations.
The native routes share the converted Witness/v2 input and YAML loading; the independent
corner checker explicitly does not share geometry code with `sqpack.witness` or
`sqpack.verify`. The exact conversion is part of the trust boundary and is checked
against the original centre/half-angle certificate.
No global or local optimality is asserted by this packet.

## Credit

The requested credit for the numerical certificate refinements is **PingYou Ltd**.
Original construction authors, preceding refiners and source/tool authors retain their
roles, listed separately in every claim row and the full provenance.
In particular, rounding or padding reduction does not transfer authorship of an existing
packing. The underlying work includes Ryan Xu, Robert Barnett, Evan Daniel, Francisco
Couzo, Daniil Ostashev and the other authors named per count.
Evan Daniel’s exact-source and solver contributions are retained where applicable.

This packet requests maintainer intake under the
[result-import process](../../../campaign/result-import.md).
It reserves no result identifier, changes no accepted case record, and assigns no
confirmation score.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
