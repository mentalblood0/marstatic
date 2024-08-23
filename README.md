## Thesis Semantic Identifier

### Syntax

See `TsidParser.py` and `test_tsid_parser.py`

### Semantics

- `/` separates answer or negation of initial thesis

- `-` separates specific version of initial thesis

- `.` separates clarification or consequence of initial thesis

- number separates part of initial thesis

#### Example

`A2.b-c/D` identifies **answer from proponents of thesis `D`** to **version `c`** of **clarification `b`** of **part `2` of thesis `A`**

### Coloring

Colors for atoms are assigned by:

1. Obtaining all atoms used on page

2. Sorting them alphabetically

3. Assigning `(1 / N * n, S, V)` color in HSV color space to `n`-th of total of `N` of them, where `S` and `V` are constant

#### Atoms with numbers have the same color as without them:

`A`, `A1`, `A32` have the same color

#### Clarification decreases saturation:

- in `A.b`, `b` has the same color as `A` except it is less saturated,

- in `A.b.c`, `c` has the same color as `b` except it is less saturated

#### Version introduces separate color space:

- in `A-b`, `b` has own color which might coincide with color of `B`, for example

- if there are `A`, `K`, `L`, `F`, `A-b`, `A-c`, `A-d`, then colors of `b`, `c` and `d` got the same way as colors of `A`, `K`, `L`, `F`

#### Answer has no affect on color except rules above:

in `A/B` color of `B` is the same as in `B.1.2-c` for example

### Problems

#### Answer from version or version of answer?

How should `A0/R-r` be read?

- `A0/(R-r)`, i.e. answer of proponent of version `r` of thesis `R` to thesis `A0`

- `(A0/R)-r`, i.e. version `r` of answer of proponent of thesis `R` to thesis `A0`

#### Part of thesis from which is the answer of part of answer?

How should `A/R1` be read?

- `A/(R1)`, i.e. answer of proponent of part `1` of thesis `R` to thesis `A`

- `(A/R)1`, i.e. part 1 of answer of proponent of thesis `R` to thesis `A`
