# Guzhou0806’s Continuous-Pose Kernel: s(40) > 1340000/199529 on wand125’s Density

Guzhou0806’s comment of 2026-10-10T14:50:00Z on
[issue #485](https://github.com/jlevy/squares/issues/485#issuecomment-6098734391) reports a
lower bound for $n = 40$, unrestricted rotations, from
[Guzhou0806/n40-square-packing](https://github.com/Guzhou0806/n40-square-packing/tree/71c97d07553d7d5ff5c5c82f0c9d1c75a150a4e3)
at `71c97d07553d7d5ff5c5c82f0c9d1c75a150a4e3` (tree
`11280a385872af75e7f5a181a89580e977282a6f`, committed 2026-10-10T14:30:28Z), which the
release tag `n40-continuous-1340000-199529-20261010` names.
The commit descends from `e5abeb4d`, the pin of the
[clipped-corner packet](../guzhou-n40-clipped-corner-2026-10-10/README.md) that retains
`T-133`’s $s(40) > 335427/50000$.

| Bound | Exact form | What it rests on |
| --- | --- | --- |
| $s(40) > 1340000/199529 = 6.715815746082023\ldots$ | strict | every side-$B$ square in $K$ captures at least $\tau$: the continuous kernel over 43 slabs for $t \in [10^{-6}, 83/200]$ and the axis kernel at side $A$ for $t \in [0, 10^{-6}]$; then $40\tau - M = 1/500$ |

Here $K = [0, 67/10]^2$, $B = 199529/200000$, $\tau = 4999/5000$, $M = 3999/100$,
$A = 997643/1000000$ and $t = \tan(\theta/2)$.
The bound raises `T-133`’s by exactly $72586117/9976450000$.
The density is wand125’s `rect_n40_L67`, the one the
[2026-10-01 rectangle packet](../wand125-rectangle-certificates-2026-10-01/README.md)
retains for `T-068`’s $s(40) \ge 67/10$; the source’s copy is byte for byte the same
(SHA-256 `71011d0356dd179c6e7e6e02c9a064ff30f6f13844016ce3b97463bf7ef53dc0`), so this is
a second extension of a certificate the record already holds, not a new density.
The argument is in the source’s `PROOF.md`; the mathematical review is
[review-2026-10-10-guzhou-n40-continuous-pose-bound.md](../../../../docs/project/reviews/review-2026-10-10-guzhou-n40-continuous-pose-bound.md),
which found no blocking defect and wrote the replay contract this packet’s receipts
answer.

The release `n40-continuous-1340000-199529-20261010` was published 2026-10-10T14:49:22Z
with one archive, `n40-continuous-1340000-199529.zip`, 129,976 bytes, SHA-256
`78d693ae5bd08cc3065348c6593c2bec36412bebe48eb2f744786dc115bba26f`, the comment’s, and
its digest file `n40-continuous-1340000-199529.zip.sha256`.
The sources were retrieved at 2026-10-10T17:25Z.

## Retained Here

`devtools.acquire_source` wrote [`source/`](source) from a full clone checked out at the
pin, from the declaration in [acquisition/declaration.json](acquisition/declaration.json);
every file is bound to its Git blob at the pin.
[acquisition/sources.json](acquisition/sources.json) is the acquisition record and
[acquisition/upstream-subtree.sha256](acquisition/upstream-subtree.sha256) the manifest
of all 28 files of the tree (487,953 bytes).
The source’s own `SHA256SUMS` holds for every one of its 27 lines in the tree and in the
ZIP.

Twenty-seven files are retained (155,106 bytes):

| Upstream path | Git blob | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `.gitattributes` | `1f9683ba325ebf468c324187e140a55c0eb25523` | 58 | `2d5c072f5cbe11a4c74660a6e47beffcf246fc3546a5aaa534b21c724fe2f9fc` |
| `.github/workflows/verify.yml` | `616194be8ca8d5a3dd6fb1080d7fde01c277d84e` | 1346 | `9c209614911a6adc4f1e7f496fa62b5a91255f0034efd8c314aaa8a1f674907a` |
| `.gitignore` | `5ef9f3a66a0b531e7d6dc905a2e9e482d19473f5` | 37 | `85e9e61c0a8dee51b98253a262d7a2f3f8fe29badf2d145a68b510bdd330b7f5` |
| `LICENSE` | `654ff03eb31bc71611c2a709767d2044d88af0cf` | 1067 | `94be33291ae276999b6f49d7ebc3ed2d35e11e61e2fcd443f810178c09a2fad9` |
| `PROOF.md` | `c7cecc853c70eb7e67095ea275dbb53117962490` | 21961 | `6fc34dff6ccd9bd8a3aa1703baf200f2cde75f3151759f8c76186fe4214e5856` |
| `README.md` | `e4b2e4e97d8cffe7bd0b7e97551d0244249c6a79` | 2289 | `49b16634ff28668272fb8201667c4a1d635ea3391c30e417286385446891fc21` |
| `REPRODUCIBILITY.md` | `4eed62523a57dbe681d0d0b3eee0896ee3d4c5b3` | 3542 | `99abb5ff99a3575badb752fe971950264ddbf9e93497edee07e3f3c9c39f6b04` |
| `SHA256SUMS` | `6aa67c983c0ba0091d664a71e5bf5586879e2ffc` | 2334 | `33441e09c3eca25817cdbdb727aa25a54cc092292a207645dc5d0e0524172d14` |
| `SOURCES.md` | `9880a2959a733f40f4f654d061802e063abfc7f7` | 3887 | `76d52c1c9957d1993d3d891fa94f17b137595582b684ce506fc9915ef2792cb3` |
| `VERIFICATION.md` | `7ffd8d5e952c2282e8d84be28fdd40a999e4d74b` | 3849 | `f4372132f34829fe1e167fe03add00f03a60fa30a28d4e598fffddabc0edda71` |
| `certificate/parameters.json` | `5370d34381975bc5c8dd28e50abf76d34e513a5b` | 795 | `4d153cb377a84e52333cbd76facb7a7a48ee586ea2567b5ac5d397ab7d9407c5` |
| `licenses/jlevy-squares.txt` | `239dffb892be26bfe17991b8396ae78ad9235cee` | 21153 | `7428341239cf4ee78c4b951b7fd8a2284b24835aeb0ede82f032b2e95e92cc00` |
| `licenses/tokoharu.txt` | `3b9a49cd1e449395373f48106c357e63cc2ed683` | 1065 | `8dc3364f10709e043998e74d0de02774a7f6c9b08dde3a8a58336948d9ed8ad8` |
| `licenses/wand125.txt` | `bbfbff131ef8ccbba5ed8b8b395f2c457eb8922c` | 1064 | `c0dd43e7892932c81335f74a2fdbf1a98f5977bab14c0c4c30e3abcc97c34904` |
| `results/axis.json` | `711e44909020c565f336bc065b5eced29a7d54cf` | 718 | `041ac9d9f1f2cbae17b642f41f67beaddb4974247dcd93d083c99a38ad1e7b9c` |
| `results/slabs.jsonl` | `19a78691652afba55d600ed4398f211692a591db` | 33429 | `4fb7708313eebe540d7674c62d3352e5e1be0b1ea777067346b117dfe4b123f0` |
| `results/verification.json` | `e49a341c6f7373ebad8a27e7258f991636a786cf` | 10288 | `e465f7656f53779cfaece7b14ea148b0a1a83ba05c6b8a529b70db71940b97f7` |
| `tests/kernel_harness.cpp` | `20082196d8721819d007c2c2bf5e6a2ed8e3c19f` | 888 | `4ee681bced642c708eda7d71845836d3ea18d61c350ff49ef26e199fb9ee6e40` |
| `tests/oracle.py` | `3e36d5811b35c772dfc875c6bc1ddccbf51b869c` | 1073 | `395fa622bec60607798a3da4103162313833fe9c139a40ca2023cd00c14d581e` |
| `tests/rounding_harness.cpp` | `c43913a913d546d3a2d78ad4f385675d70bb1f81` | 1161 | `96bd022242b4c0e44ff3eb27a8294d3d359bc74263f898e350768eeb78fdfc9f` |
| `tests/test_admission.py` | `cbc969e093cfc1647e7cfbe3ee66d82f11516e13` | 3146 | `797689e9f891e59d6f8caea9d691cfb81606378e401e8489881fde19f13f632c` |
| `tests/test_kernel.py` | `21db83602b9e69c8a9d784099e6929d95c6dbbed` | 3475 | `6963d2ef8b0d16f1aa41b31f9091b2185be8630c03994bf66ac97105d7299aa5` |
| `verifier/audit.py` | `ed448328c0103d337c2fbc6c244acffb7f846b39` | 7129 | `9ecbabfc483b181d21dc2a298d5c35b228218176eba97dcf856113238348281e` |
| `verifier/axis_integer_grid.cpp` | `37701463136ba902486b1834f4e6ebfb8b1b1635` | 4143 | `f5bc3f60065aaea3d14ffb8465865750fca22cf8bbc6bd8739b5120200b6277d` |
| `verifier/continuous_pose.cpp` | `c4e351b3e245429912519eec259ea54c2af55fac` | 11075 | `da06206b8e83a57b8a710ba62e743c6d3a1959e9160ff32ae89ede583841c73c` |
| `verifier/exact.py` | `a92be31b718e40c3c9faaa8893ffc0e662385daa` | 7151 | `3e2aa3ca8e324a39e018ccb28267606344a9de585d72f43d79d80663b7c312cf` |
| `verifier/run.py` | `27830a226941fa653d987d86d9b05aaa46439936` | 6983 | `3387697cfba17021242b06e06d11df7975c72f5cca97a276cf758fea7e187ba6` |

One file is pinned by digest and not copied: `certificate/certified_candidate.json`
(332,847 bytes) is wand125’s density, the bytes of the 2026-10-01 packet’s
`wand125-rectangles/certificates/rect_n40_L67/certified_candidate.json.gz`, which
`acquire_source --check` compares.
The two kernels’ sources are the digests the release names as frozen: `da06206b…` for
`verifier/continuous_pose.cpp` and `f5bc3f60…` for `verifier/axis_integer_grid.cpp`.
The `results/` the tree holds are the producer’s local run (GC-3 of the review).

## The Release ZIP and Its CI Receipt

The ZIP holds the 28 files of the tree, of which 24 are byte-identical
([release-ci/zip-entries.sha256](release-ci/zip-entries.sha256) digests every entry).
The other four are its three `results/` files and the `SHA256SUMS` whose three lines name
them: the ZIP carries the receipt of GitHub Actions run
[38059878931](https://github.com/Guzhou0806/n40-square-packing/actions/runs/38059878931)
(`success` on `71c97d07`, 2026-10-10T14:30:32Z to 14:47:05Z) in place of the tree’s.
Both are kept and named for what they are:

| Receipt | Where | `verification.json` | `slabs.jsonl` | `axis.json` | `source_commit` | Pose binary | Axis binary | Compiler | Python | Wall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| producer’s local run | `source/results/` | `e465f765…` | `4fb77083…` | `041ac9d9…` | null | `a5dcfa3e…` | `051e306d…` | GCC 15.2.0 | 3.14.4 | 510.96 s |
| CI run 38059878931 | `release-ci/results/` | `575a5860…` | `24d16b52…` | `3ace101e…` | `71c97d07…` | `69bc9e64…` | `cccecb9a…` | GCC 13.3.0 | 3.12.3 | 983.95 s |

Both report four workers, 43 of 43 slabs `verified`, 61,860,927 nodes, 30,930,485
leaves, 14,096,668 angle bisections, the least leaf bound
$2251349454150741/2^{51} = 0.99980000019017\ldots$, the axis minimum
$249950896232809301864786207/(25 \cdot 10^{25})$ over $2213^2 = 4{,}897{,}369$
vertices, and the derived inputs `ccf7b68a…` (pose) and `d57e8bb2…` (axis); every
non-timing field of their 43 slab outputs and their axis output is identical.
[release-ci/](release-ci) also keeps the ZIP’s `SHA256SUMS` (`ac8bd643…`), the
release’s own digest file, and the GitHub API records of the release and of the run
(metadata only; the run’s log was not read).

## Credit and Licence

The new material is Guzhou0806’s under the MIT licence (`LICENSE`, copyright 2026
Guzhou0806). `SOURCES.md` credits the density to wand125, “the rectangle-density method
and original translation-derivative verification structure” to Tokoharu, prior measure
and unavoidable-set work to Stromquist, Burns and Massaccesi, and says the concave-section
bound “is informed by the Rust implementation in Joshua Levy’s Squares Project”, pinned
at `ef79288a4`, and that the new C++ kernel “is not an unchanged replay of that Rust
program”. It gives Guzhou0806’s contribution as “the continuous-pose extension,
smaller-square coverage, near-axis patch, exact composition and associated
implementation/testing”, from “AI-assisted research”.
The density’s MIT licence is retained in `licenses/wand125.txt`, Tokoharu’s in
`licenses/tokoharu.txt` and this repository’s in `licenses/jlevy-squares.txt`.
The comment’s AI-assistance statement: “AI assisted mathematical exploration, proof
drafting, implementation, regression tests, packaging and this update under my
direction.”
The comment asks the record to “credit the continuous-pose extension, smaller-square
coverage, near-axis patch and resulting improvement to Guzhou0806, AI-assisted,
retaining wand125 for the original density, Tokoharu for the rectangle-density method
and translation-derivative structure, and Joshua Levy / the Squares Project for the
concave-section inspiration”.

## Commands

From `packing/`, each after `uv run --frozen --all-extras --group dev`:

```sh
python -m devtools.acquire_source guzhou-n40-continuous-pose-2026-10-10 --check
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
