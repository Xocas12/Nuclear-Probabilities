# NAPB-90 county table: report

Written by `scripts/napb90_assemble.py`.

- Pages: 158 (PDF pp. 135-292); county rows: 3142; matched to a FIPS code: 3136
- Cells where the two passes differ: 20 (none of them a figure)

| Highest risk band | Counties | 1985 population (NAPB) | Share |
|---|---|---|---|
| very high (>=10 psi) | 730 | 160,348,742 | 67.0% |
| high (5-10 psi) | 88 | 7,230,096 | 3.0% |
| medium (2-5 psi) | 245 | 14,985,846 | 6.3% |
| low (0.5-2 psi) | 666 | 24,395,356 | 10.2% |
| no (<0.5 psi) | 1411 | 32,213,229 | 13.5% |

## Checks

- column sum: 79
- split lines: 9
- census 1985 differs by a third or more: 5
- no census match: 4

Column sums that differ from a printed total, and the counties far from the census estimate, were read again by both passes on enlarged images: the figures are printed as transcribed, so they are slips in FEMA's tables (`checks.csv`).
