# Netherlands, census of 31 May 1960: withdrawn

`towns_nl_1960.csv` (220 municipalities of 10,000+ inhabitants) was removed by the nineteenth amendment
(`configs/protocol_amendment_19.yaml`). Its figures were transcribed from CBS, *13e Algemene Volkstelling, 31 mei 1960*,
Deel 2, Tabel 1, in the DANS dataset doi:10.17026/DANS-XSC-VKWS (CC-BY-4.0). The volume was fetched from
`https://ssh.datastations.nl/api/access/datafile/290666`, a path that host's robots.txt disallows to every agent
(`User-agent: *`, `Disallow: /`). The DOI resolver, which allows it, was checked instead, so the robots table passed it.

No copy on a host that allows it was found: www.cbs.nl does not hold the 1960 volumes, and historisch.cbs.nl,
volkstellingen.nl, www.delpher.nl and dataverse.nl refuse automated agents. The held files were removed from
`data/raw/`, and the Netherlands from region `wp_west_1965` and from the 1965 map. Rows of the Warsaw Pact lists that name
Dutch places stay in the label files as transcribed and link to no town. The table is in git history before the
amendment's refit.
