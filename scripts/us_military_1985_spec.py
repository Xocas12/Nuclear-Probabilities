# ruff: noqa: E702, E741
"""Row specification for data/curated/features/us_military_sites_1985.csv (built by scripts/us_military_1985_build.py)."""
# Each r(...) call:
# (site, role, unit, state, town, page, from_year, until_year, in_role_1985, decision, note, check_regex)
# from/until are the years of the ROLE at the site (until blank = still in that role after 1991 or today).
SACL = 'List of Strategic Air Command bases'

R = []
def r(site, role, unit, state, town, page, fr, un, inr, dec, note, chk, extra=None, coord=None):
    R.append(dict(site=site, role=role, unit=unit, state=state, town=town, page=page, from_year=fr, until_year=un,
                  in_role_1985=inr, decision=dec, note=note, chk=chk, extra=extra or [], coord=coord))

# ---------------- SAC bomber bases ----------------
r('Barksdale AFB', 'sac_bomber', '2nd Bomb Wing (B-52G); Eighth Air Force HQ', 'LA', 'Bossier City', 'Barksdale Air Force Base', 1949, '', True, '',
  'SAC host since 1949 (301st BW, 4238th SW, 2nd BW from 1963); 8th AF HQ 1975-; KC-10s of the 32nd ARS from 1981.', r'2d Bomb Wing|KC-10', [SACL])
r('Blytheville AFB', 'sac_bomber', '97th Bomb Wing (B-52G)', 'AR', 'Blytheville', 'Eaker Air Force Base', 1959, 1992, True, '',
  'Renamed Eaker AFB in 1988; closed 1992.', r'97th Bomb|1988', [SACL])
r('Carswell AFB', 'sac_bomber', '7th Bomb Wing (B-52H); 19th Air Division', 'TX', 'Fort Worth', 'Carswell Air Force Base', 1948, 1993, True, '',
  '7th BW 1948-1993; ALCM from 1985.', r'ALCM|7th Bomb', [SACL])
r('Castle AFB', 'sac_bomber', '93rd Bomb Wing (B-52G/H, KC-135 crew training)', 'CA', 'Atwater', 'Castle Air Force Base', 1947, 1995, True, '',
  'SAC B-52 and KC-135 combat crew training base.', r'93', [SACL])
r('Dyess AFB', 'sac_bomber', '96th Bomb Wing (B-52H; first B-1B June 1985, on alert Oct 1986)', 'TX', 'Abilene', 'Dyess Air Force Base', 1956, '', True, '',
  'First B-1B arrived June 1985; B-1B nuclear alert from October 1986. B-52 role continued through 1985.', r'June 1985', [SACL])
r('Ellsworth AFB', 'sac_bomber', '28th Bomb Wing (B-52H; B-1B from 1987)', 'SD', 'Rapid City', 'Ellsworth Air Force Base', 1947, '', True, '',
  'B-1B from 1987.', r'1987|B-1B', [SACL])
r('Fairchild AFB', 'sac_bomber', '92nd Bomb Wing (B-52G, B-52H from 1985); 47th Air Division', 'WA', 'Spokane', 'Fairchild Air Force Base', 1947, 1994, True, '',
  'B-52s left 1994 (base became a tanker base).', r'In 1985, Fairchild', [SACL])
r('Grand Forks AFB', 'sac_bomber', '319th Bomb Wing (B-52G/H; B-1B from 1987)', 'ND', 'Grand Forks', 'Grand Forks Air Force Base', 1960, 1994, True, '',
  'B-52s from 1960 (4133rd SW, 319th BW 1963); B-1B 1987-1994.', r'319th', [SACL])
r('Griffiss AFB', 'sac_bomber', '416th Bomb Wing (B-52G)', 'NY', 'Rome', 'Griffiss Air Force Base', 1959, 1995, True, '',
  'SAC bombers from 1959 (4039th SW), 416th BW 1963-1995.', r'416th', [SACL])
r('K. I. Sawyer AFB', 'sac_bomber', '410th Bomb Wing (B-52H)', 'MI', 'Gwinn', 'K. I. Sawyer Air Force Base', 1961, 1995, True, '',
  'SAC bombers from 1961 (4042nd SW), 410th BW 1963-1995.', r'410th|B-52H', [SACL])
r('Loring AFB', 'sac_bomber', '42nd Bomb Wing (B-52G)', 'ME', 'Limestone', 'Loring Air Force Base', 1953, 1994, True, '',
  'Closed 1994.', r'42nd Bomb|42d Bomb', [SACL])
r('Mather AFB', 'sac_bomber', '320th Bomb Wing (B-52G), tenant', 'CA', 'Rancho Cordova', 'Mather Air Force Base', 1958, 1989, True, '',
  'SAC tenant at an ATC navigator-training base; 320th BW 1963-1989.', r'1963 to 1989', [SACL])
r('Minot AFB', 'sac_bomber', '5th Bomb Wing (B-52H); 57th Air Division', 'ND', 'Minot', 'Minot Air Force Base', 1961, '', True, '',
  'B-52 since 1961 (450th BW, 5th BW from 1968).', r'5th Bomb', [SACL])
r('Plattsburgh AFB', 'sac_bomber', '380th Bomb Wing (FB-111A)', 'NY', 'Plattsburgh', 'Plattsburgh Air Force Base', 1955, 1991, True, '',
  'FB-111A 1971-1991 (B-47 and B-52 earlier); closed 1995.', r'FB-111|380th', [SACL])
r('Pease AFB', 'sac_bomber', '509th Bomb Wing (FB-111A); 45th Air Division', 'NH', 'Portsmouth', 'Pease Air National Guard Base', 1956, 1990, True, '',
  'FB-111A 1970-1990; base closed 1991.', r'FB-111|509th', [SACL])
r('Wurtsmith AFB', 'sac_bomber', '379th Bomb Wing (B-52G); 40th Air Division', 'MI', 'Oscoda', 'Wurtsmith Air Force Base', 1961, 1993, True, '',
  '', r'379th Bombardment Wing\]\], 9 January 1961', [SACL])
r('Robins AFB (19th Bomb Wing)', 'sac_bomber', '19th Bomb Wing (B-52G)', 'GA', 'Warner Robins', 'Robins Air Force Base', 1959, 1983, False,
  'B-52s left 1983: the 19th BW was redesignated 19th Air Refueling Wing on 1 Oct 1983', '', r'Redesignated: 19th Air Refueling Wing', [SACL])
r('March AFB (22nd Bomb Wing)', 'sac_bomber', '22nd Bomb Wing (B-52D)', 'CA', 'Riverside', 'March Air Reserve Base', 1949, 1982, False,
  'B-52D retired 1982; wing became 22nd Air Refueling Wing (KC-10)', '', r'retirement of the B-52D in 1982', [SACL])
r('Seymour Johnson AFB (68th Bomb Wing)', 'sac_bomber', '68th Bomb Wing (B-52G)', 'NC', 'Goldsboro', 'Seymour Johnson Air Force Base', 1958, 1982, False,
  '68th Bomb Wing ended 1982 (List of SAC bases); SAC kept tankers there', '', r'1961 Goldsboro', [SACL])
r('Dyess AFB (B-1B)', 'sac_bomber_b1b', '96th Bomb Wing B-1B Lancer', 'TX', 'Abilene', 'Dyess Air Force Base', 1985, '', False,
  'First B-1B delivered June 1985, nuclear alert only from Oct 1986: not yet in role at mid-1985 (the B-52 row covers Dyess)', 'Same site as the Dyess bomber row; kept so the B-1B dates are explicit.', r'June 1985', [SACL])
r('Ellsworth AFB (B-1B)', 'sac_bomber_b1b', '28th Bomb Wing B-1B Lancer', 'SD', 'Rapid City', 'Ellsworth Air Force Base', 1987, '', False,
  'B-1B arrived 1987', '', r'1987', [SACL])
r('Grand Forks AFB (B-1B)', 'sac_bomber_b1b', '319th Bomb Wing B-1B Lancer', 'ND', 'Grand Forks', 'Grand Forks Air Force Base', 1987, 1994, False,
  'B-1B arrived 1987', 'Year from general knowledge of the 319th BW; the Grand Forks article does not date it explicitly.', r'B-1', [SACL])
r('McConnell AFB (B-1B)', 'sac_bomber_b1b', '384th Bomb Wing B-1B Lancer', 'KS', 'Wichita', 'McConnell Air Force Base', 1987, 1994, False,
  '384th ARW became 384th Bomb Wing (B-1B) in 1987', '', r'384', [SACL])

# ---------------- SAC tanker / reconnaissance ----------------
r('Grissom AFB', 'sac_tanker', '305th Air Refueling Wing (KC-135)', 'IN', 'Peru', 'Grissom Air Reserve Base', 1970, 1994, True, '',
  'B-58 base until 1970; tanker wing 1970-1994.', r'305th Air Refueling Wing \(305 ARW\) on 1 January 1970', [SACL])
r('McConnell AFB', 'sac_tanker', '384th Air Refueling Wing (KC-135)', 'KS', 'Wichita', 'McConnell Air Force Base', 1972, '', True, '',
  'Tanker wing 1972-1987, then B-1B wing; also host of the 381st SMW (Titan II).', r'384', [SACL])
r('March AFB', 'sac_tanker', '22nd Air Refueling Wing (KC-10); Fifteenth Air Force HQ', 'CA', 'Riverside', 'March Air Reserve Base', 1982, 1994, True, '',
  '15th AF HQ 1949-1992.', r'22d Air Refueling Wing', [SACL])
r('Robins AFB', 'sac_tanker', '19th Air Refueling Wing (KC-135); Warner Robins Air Logistics Center', 'GA', 'Warner Robins', 'Robins Air Force Base', 1983, 1996, True, '',
  'Also AFLC depot (Warner Robins ALC).', r'Redesignated: 19th Air Refueling Wing', [SACL])
r('Seymour Johnson AFB (SAC tankers)', 'sac_tanker', '911th Air Refueling Squadron / 68th Air Refueling Group (KC-10)', 'NC', 'Goldsboro', 'Seymour Johnson Air Force Base', 1958, 1991, True,
  'SAC tankers stayed after the 68th BW ended in 1982 (911th ARW/ARS 1958-1986, 68th ARW 1986-1991 in List of SAC bases)',
  'The intermediate 68th Air Refueling Group designation is from general knowledge, not the cited pages.', r'Goldsboro', [SACL])
r('Altus AFB (SAC tankers)', 'sac_tanker', '340th Air Refueling Wing/Group (KC-135), tenant', 'OK', 'Altus', 'Altus Air Force Base', 1977, 1992, True, '',
  'SAC tenant on a MAC training base; List of SAC bases gives 1984-1992, the Altus article 1 July 1977 - 1 Oct 1992.', r'340th', [SACL])
r('Beale AFB', 'sac_reconnaissance', '9th Strategic Reconnaissance Wing (SR-71, U-2/TR-1, KC-135Q); 14th Air Division', 'CA', 'Marysville', 'Beale Air Force Base', 1966, '', True, '',
  'B-52s 1959-1975 (4126th SW, 456th BW); 100th ARW until 1983.', r'9th Strategic Reconnaissance Wing', [SACL])
r('Offutt AFB (55th SRW)', 'sac_reconnaissance', '55th Strategic Reconnaissance Wing (RC-135, EC-135 Looking Glass)', 'NE', 'Bellevue', 'Offutt Air Force Base', 1966, '', True, '',
  'Also flew the airborne command post (Looking Glass); SAC HQ listed as its own command_centre row.', r'55th Strategic Reconnaissance Wing', [SACL])
r('Eielson AFB (6th Strategic Wing)', 'sac_reconnaissance', '6th Strategic Wing (RC-135S support; Alaskan Tanker Task Force)', 'AK', 'Fairbanks', 'Eielson Air Force Base', 1967, 1992, True, '',
  'Host was Alaskan Air Command (343rd Composite Wing); SAC 6th SW 1967-1988, 6th SRW 1988-1992.', r'6th Strategic Wing', [SACL])
r('Shemya AFB', 'sac_reconnaissance', 'RC-135 Cobra Ball forward base; Cobra Dane radar (AAC host)', 'AK', 'Shemya', 'Eareckson Air Station', 1977, '', True, '',
  'Years are Cobra Dane\'s (1977-); SAC RC-135s flew from Shemya earlier. Host was Alaskan Air Command.', r'Cobra Dane was declared operational')

# ---------------- ICBM wings (host base rows) ----------------
r('Ellsworth AFB (44th SMW)', 'icbm_wing', '44th Strategic Missile Wing, 150 Minuteman II (66th/67th/68th SMS)', 'SD', 'Rapid City', 'Ellsworth Air Force Base', 1962, 1994, True, '',
  'Minuteman II stood down from 1991, wing inactivated 1994.', r'44th', [SACL, '44th Missile Wing'])
r('F. E. Warren AFB (90th SMW Minuteman)', 'icbm_wing', '90th Strategic Missile Wing, Minuteman III (319th/320th/321st/400th SMS)', 'WY', 'Cheyenne', 'Francis E. Warren Air Force Base', 1963, '', True, '',
  '200 Minuteman (Minuteman III from 1973-75); the 400th SMS converted to Peacekeeper 1986-88. Also 4th Air Division HQ.', r'1 July 1963', [SACL, '90th Missile Wing'])
r('F. E. Warren AFB (Peacekeeper)', 'icbm_wing_peacekeeper', '90th SMW / 400th SMS, 50 LGM-118 Peacekeeper', 'WY', 'Cheyenne', 'Francis E. Warren Air Force Base', 1986, 2005, False,
  'Peacekeeper construction from 1984 and training from June 1985, but first missiles on alert Oct 1986, fully operational 30 Dec 1986',
  '', r'30 December 1986', ['90th Missile Wing', 'LGM-118 Peacekeeper'])
r('Minot AFB (91st SMW)', 'icbm_wing', '91st Strategic Missile Wing, 150 Minuteman III (740th/741st/742nd SMS)', 'ND', 'Minot', 'Minot Air Force Base', 1962, '', True, '',
  '455th SMW 1962-1968, redesignated 91st SMW 1968.', r'91st', [SACL, '91st Missile Wing'])
r('Grand Forks AFB (321st SMW)', 'icbm_wing', '321st Strategic Missile Wing, 150 Minuteman III (446th/447th/448th SMS)', 'ND', 'Grand Forks', 'Grand Forks Air Force Base', 1964, 1998, True, '',
  'Inactivated 1998 after BRAC 1995.', r'321st', [SACL, '321st Missile Group'])
r('Malmstrom AFB (341st SMW)', 'icbm_wing', '341st Strategic Missile Wing, 200 Minuteman II/III (10th/12th/490th/564th SMS)', 'MT', 'Great Falls', 'Malmstrom Air Force Base', 1961, '', True, '',
  'Largest field (23,500 sq mi).', r'23500', [SACL, '341st Missile Wing'])
r('Whiteman AFB (351st SMW)', 'icbm_wing', '351st Strategic Missile Wing, 150 Minuteman II (508th/509th/510th SMS)', 'MO', 'Knob Noster', 'Whiteman Air Force Base', 1963, 1995, True, '',
  'Inactivated 1995; Whiteman became the B-2 base.', r'launch control centers', [SACL, '351st Missile Wing'])
r('Little Rock AFB (308th SMW)', 'icbm_wing_titan', '308th Strategic Missile Wing, 18 Titan II (373rd/374th SMS)', 'AR', 'Jacksonville', 'Little Rock Air Force Base', 1962, 1987, True,
  'Titan II deactivation under way: 15 of 18 complexes still in service on 30 Jun 1985 by the dates in the squadron articles (374-7 lost in 1980); wing inactivated 18 Aug 1987',
  'Titan II article: last missile (373-8 near Judsonia) deactivated 5 May 1987; the 373rd SMS article dates 373-8 to 20 Oct 1986 - the squadron dates may be off-alert or deactivation dates. 374-7 destroyed in the Damascus accident of Sept 1980.', r'18 August 1987', [SACL, '308th Strategic Missile Wing', 'LGM-25C Titan II'])
r('McConnell AFB (381st SMW)', 'icbm_wing_titan', '381st Strategic Missile Wing, 18 Titan II (532nd/533rd SMS)', 'KS', 'Wichita', 'McConnell Air Force Base', 1962, 1986, True,
  'Titan II deactivation under way: 9 of 18 complexes still in service on 30 Jun 1985 by the dates in the squadron articles; wing inactivated 8 Aug 1986 - kept as in role, at half strength',
  '', r'8 August 1986', [SACL, '381st Strategic Missile Wing'])
r('Davis-Monthan AFB (390th SMW)', 'icbm_wing_titan', '390th Strategic Missile Wing, 18 Titan II (570th/571st SMS)', 'AZ', 'Tucson', 'Davis–Monthan Air Force Base', 1962, 1984, False,
  'Last Titan II off alert May 1984; wing inactivated end of July 1984',
  'Site 571-7 is now the Titan Missile Museum.', r'inactivated the 390th', [SACL, '390th Strategic Missile Wing'])
r('Vandenberg AFB', 'icbm_test_base', '1st Strategic Aerospace Division (ICBM test and training launches)', 'CA', 'Lompoc', 'Vandenberg Space Force Base', 1958, '', True, '',
  'SAC ICBM operational test launches; also space launches (SLC-6 shuttle complex, never used).', r'1st Strategic Aerospace Division|Strategic Air Command', [SACL])

# ---------------- missile fields (rows built from launch-site lists in build.py) ----------------
FIELDS = [
  # wing, host, list/pages, states, from, until, in85, decision
  ('44th SMW missile field', '44th Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1962, 1994, True, ''),
  ('90th SMW missile field', '90th Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1963, '', True,
   'Includes the 400th SMS flights P-T, whose 50 silos took Peacekeeper from 1986'),
  ('91st SMW missile field', '91st Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1962, '', True, ''),
  ('321st SMW missile field', '321st Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1964, 1998, True, ''),
  ('341st SMW missile field', '341st Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1961, '', True, ''),
  ('351st SMW missile field', '351st Missile Wing LGM-30 Minuteman Missile Launch Sites', 'list', 1963, 1995, True, ''),
  ('308th SMW missile field (Titan II)', ['373d Strategic Missile Squadron', '374th Strategic Missile Squadron'], 'titan', 1962, 1987, True, ''),
  ('381st SMW missile field (Titan II)', ['532d Strategic Missile Squadron', '533d Strategic Missile Squadron'], 'titan', 1962, 1986, True, ''),
  ('390th SMW missile field (Titan II)', ['570th Strategic Missile Squadron', '571st Strategic Missile Squadron'], 'titan', 1962, 1984, False,
   'All 18 sites off alert by May 1984'),
]

# ---------------- SSBN bases ----------------
r('Naval Submarine Base Bangor', 'ssbn_base', 'Trident SSBN base: Submarine Group 9, Strategic Weapons Facility Pacific (Ohio-class from 1982)', 'WA', 'Silverdale', 'Naval Base Kitsap', 1977, '', True, '',
  'Trident base from 1977; USS Ohio arrived Aug 1982. Earlier Naval Ammunition Depot / Polaris Missile Facility Pacific (1964). Now part of Naval Base Kitsap.', r'Ohio|Trident')
r('Naval Submarine Base Kings Bay', 'ssbn_base', 'Submarine Squadron 16 (Poseidon/Trident I SSBNs, refit site)', 'GA', 'St. Marys', 'Naval Submarine Base Kings Bay', 1979, '', True, '',
  'SubRon 16 moved from Rota, Spain, in 1979; Ohio-class from 1989; SWFLANT moved here later.', r'1979|Rota')
r('Charleston Naval Base', 'ssbn_base', 'Submarine Squadron 18 (SSBN refit), Charleston Naval Shipyard; Polaris Missile Facility Atlantic at NWS Charleston', 'SC', 'North Charleston', 'Charleston Naval Base', 1901, 1996, True, '',
  'Major Atlantic Fleet homeport and SSBN refit site; closed 1996.', r'Submarine|ballistic')
r('Naval Weapons Station Charleston', 'ssbn_base', 'Polaris/Poseidon Missile Facility Atlantic (SSBN missile handling)', 'SC', 'Goose Creek', 'Naval Weapons Station Charleston', 1960, '', True, '',
  'Now part of Joint Base Charleston (Naval Support Activity Charleston).', r'Polaris|missile|Submarine')
r('Naval Submarine Base New London', 'ssbn_base', 'Submarine Group 2; SSBN crews and Submarine School', 'CT', 'Groton', 'Naval Submarine Base New London', 1915, '', True, '',
  'Home of Atlantic SSBN crews and support; SSBNs deployed from forward sites (Holy Loch, Rota, Charleston, Kings Bay).', r'ballistic|SSBN|Submarine School')
r('Electric Boat, Groton', 'naval_shipyard', 'General Dynamics Electric Boat: builder of Ohio-class SSBNs', 'CT', 'Groton', 'Electric Boat', 1899, '', True, '',
  'Private yard; built all US SSBNs\' lead classes (Ohio class 1976-1997).', r'Ohio')
r('Newport News Shipbuilding', 'naval_shipyard', 'Builder of nuclear carriers and submarines', 'VA', 'Newport News', 'Newport News Shipbuilding', 1886, '', True, '',
  'Private yard; only builder of nuclear aircraft carriers.', r'aircraft carrier')

# ---------------- fleet headquarters and naval bases ----------------
r('Naval Station Norfolk', 'naval_base', 'Largest naval base; homeport of Atlantic Fleet carriers', 'VA', 'Norfolk', 'Naval Station Norfolk', 1917, '', True, '', '', r'largest')
r('Atlantic Fleet HQ (Norfolk)', 'fleet_hq', 'CINCLANTFLT, USCINCLANT and NATO SACLANT HQ; Second Fleet', 'VA', 'Norfolk', 'United States Fleet Forces Command', 1948, '', True, '',
  'HQ on the Naval Support Activity Hampton Roads compound next to NS Norfolk; coordinates are NS Norfolk\'s (the command article has none).', r'Atlantic Fleet', [], 'Naval Station Norfolk')
r('Pearl Harbor', 'naval_base', 'Naval Station Pearl Harbor and Naval Shipyard', 'HI', 'Honolulu', 'Naval Station Pearl Harbor', 1908, '', True, '',
  'Coordinates are the joint base\'s.', r'Pearl Harbor')
r('Pacific Fleet HQ (Makalapa, Pearl Harbor)', 'fleet_hq', 'CINCPACFLT; Third Fleet (Ford Island, to 1991)', 'HI', 'Honolulu', 'United States Pacific Fleet', 1941, '', True, '',
  'HQ at Makalapa above Pearl Harbor; coordinates are the Pearl Harbor joint base\'s.', r'Pearl Harbor', [], 'Naval Station Pearl Harbor')
r('Camp H. M. Smith', 'fleet_hq', 'USCINCPAC (Pacific Command) HQ; FMFPAC HQ', 'HI', 'Aiea', 'Camp H. M. Smith', 1957, '', True, '',
  'Unified-command HQ rather than a fleet HQ.', r'Pacific Command|Indo-Pacific Command')
r('Naval Station San Diego', 'naval_base', 'Pacific Fleet principal homeport (32nd Street)', 'CA', 'San Diego', 'Naval Base San Diego', 1922, '', True, '', '', r'1922')
r('NAS North Island', 'naval_base', 'Carrier homeport; Naval Air Forces Pacific HQ', 'CA', 'Coronado', 'Naval Air Station North Island', 1917, '', True, '', '', r'carrier')
r('Naval Submarine Base San Diego (Point Loma)', 'naval_base', 'Submarine Group 5 / Pacific attack submarines', 'CA', 'San Diego', 'Naval Base Point Loma', 1963, '', True, '', '', r'Submarine')
r('Naval Station Mayport', 'naval_base', 'Carrier and surface homeport', 'FL', 'Jacksonville', 'Naval Station Mayport', 1942, '', True, '', '', r'1942')
r('NAS Jacksonville', 'naval_base', 'Naval air station (P-3, ASW)', 'FL', 'Jacksonville', 'Naval Air Station Jacksonville', 1940, '', True, '', '', r'1940')
r('Naval Station Long Beach', 'naval_base', 'Naval Station and Naval Shipyard Long Beach (battleship homeport)', 'CA', 'Long Beach', 'Naval Station Long Beach', 1940, 1997, True, '',
  'Coordinates are the shipyard\'s (same Terminal Island complex).', r'1997|closed')
r('Puget Sound Naval Shipyard', 'naval_shipyard', 'Nuclear-capable shipyard; carrier homeport', 'WA', 'Bremerton', 'Puget Sound Naval Shipyard', 1891, '', True, '',
  'The article has no coordinates; the town\'s (Bremerton) are used, within about 2 km.', r'1891', [], 'Bremerton, Washington')
r('Naval Station Everett', 'naval_base', 'New carrier homeport', 'WA', 'Everett', 'Naval Station Everett', 1987, '', False,
  'Selected 1984 but construction began 1987 and the station opened 1994', '', r'1987|1994')
r('NAS Whidbey Island', 'naval_base', 'Naval air station (A-6, EA-6B)', 'WA', 'Oak Harbor', 'Naval Air Station Whidbey Island', 1942, '', True, '', '', r'1942')
r('Mare Island Naval Shipyard', 'naval_shipyard', 'Nuclear submarine overhaul yard', 'CA', 'Vallejo', 'Mare Island Naval Shipyard', 1854, 1996, True, '', '', r'1854|1996')
r('NAS Alameda', 'naval_base', 'Carrier homeport and naval air station', 'CA', 'Alameda', 'Naval Air Station Alameda', 1940, 1997, True, '', '', r'1997')
r('NAS Lemoore', 'naval_base', 'Master jet base, Pacific light attack', 'CA', 'Lemoore', 'Naval Air Station Lemoore', 1961, '', True, '', '', r'1961')
r('NAS Miramar', 'naval_base', 'Master jet base, Pacific fighters (F-14, TOPGUN)', 'CA', 'San Diego', 'Marine Corps Air Station Miramar', 1947, 1997, True, '',
  'Navy air station until 1997, then MCAS Miramar.', r'1997')
r('NAS Oceana', 'naval_base', 'Master jet base, Atlantic fighters and attack', 'VA', 'Virginia Beach', 'Naval Air Station Oceana', 1943, '', True, '', '', r'1943')
r('Naval Amphibious Base Little Creek', 'naval_base', 'Atlantic amphibious forces', 'VA', 'Virginia Beach', 'Naval Amphibious Base Little Creek', 1945, '', True, '', '', r'amphibious')
r('Norfolk Naval Shipyard', 'naval_shipyard', 'Nuclear-capable shipyard', 'VA', 'Portsmouth', 'Norfolk Naval Shipyard', 1767, '', True, '', '', r'1767')
r('Naval Weapons Station Yorktown', 'naval_base', 'Atlantic Fleet ammunition and weapons station', 'VA', 'Yorktown', 'Naval Weapons Station Yorktown', 1918, '', True, '', '', r'1918')
r('Portsmouth Naval Shipyard', 'naval_shipyard', 'Nuclear submarine overhaul yard', 'ME', 'Kittery', 'Portsmouth Naval Shipyard', 1800, '', True, '', '', r'1800')
r('NAS Brunswick', 'naval_base', 'Atlantic P-3 maritime patrol base', 'ME', 'Brunswick', 'Naval Air Station Brunswick', 1951, 2011, True, '', '', r'2011')
r('Naval Station Newport', 'naval_base', 'Naval War College; Naval Education and Training Center', 'RI', 'Newport', 'Naval Station Newport', 1883, '', True, '', '', r'War College')
r('NAS Pensacola', 'naval_base', 'Naval aviation training', 'FL', 'Pensacola', 'Naval Air Station Pensacola', 1914, '', True, '', '', r'1914')
r('NAS Adak', 'naval_base', 'ASW patrol base and naval facility, Aleutians', 'AK', 'Adak', 'Naval Air Station Adak', 1942, 1997, True, '', '', r'1997|1942')
r('Philadelphia Naval Shipyard', 'naval_shipyard', 'Conventional carrier overhaul yard (SLEP)', 'PA', 'Philadelphia', 'Philadelphia Naval Shipyard', 1871, 1995, True, '', '', r'1995')
r('Naval Station Great Lakes', 'naval_base', 'Navy recruit training center', 'IL', 'North Chicago', 'Naval Station Great Lakes', 1911, '', True, '', '', r'recruit')
r('NAS Moffett Field', 'naval_base', 'Pacific P-3 maritime patrol base', 'CA', 'Mountain View', 'Moffett Federal Airfield', 1933, 1994, True, '', '', r'1994')
r('NAS Patuxent River', 'naval_base', 'Naval Air Test Center; TACAMO squadrons', 'MD', 'Lexington Park', 'Naval Air Station Patuxent River', 1943, '', True, '',
  'TACAMO (SSBN communications relay) squadron VQ-4 based here.', r'1943')

# ---------------- command centres ----------------
r('Cheyenne Mountain Complex', 'command_centre', 'NORAD Cheyenne Mountain Complex', 'CO', 'Colorado Springs', 'Cheyenne Mountain Complex', 1966, '', True, '', '', r'1966')
r('Peterson AFB', 'command_centre', 'NORAD and US Space Command HQ (Space Command from Sept 1985); Air Force Space Command HQ', 'CO', 'Colorado Springs', 'Peterson Space Force Base', 1975, '', True, '',
  'NORAD/ADCOM HQ moved here from Ent AFB in 1975; Air Force Space Command formed 1982.', r'Space Command')
r('Offutt AFB (SAC HQ)', 'command_centre', 'Strategic Air Command HQ and underground command post; Looking Glass', 'NE', 'Bellevue', 'Offutt Air Force Base', 1948, 1992, True, '',
  'SAC HQ 1948-1992 (then US Strategic Command).', r'Strategic Air Command', [SACL])
r('The Pentagon', 'command_centre', 'Department of Defense HQ; National Military Command Center', 'VA', 'Arlington', 'The Pentagon', 1943, '', True, '', '', r'1943')
r('Raven Rock Mountain Complex', 'command_centre', 'Site R, Alternate Joint Communications Center (alternate Pentagon)', 'PA', 'Blue Ridge Summit', 'Raven Rock Mountain Complex', 1953, '', True, '', '', r'1953')
r('Fort Ritchie', 'command_centre', 'Army post supporting Site R', 'MD', 'Cascade', 'Fort Ritchie', 1926, 1998, True, '',
  'Support post for Raven Rock; closed 1998.', r'Raven Rock|Site R')
r('Mount Weather', 'command_centre', 'Mount Weather Emergency Operations Center (FEMA, continuity of government)', 'VA', 'Bluemont', 'Mount Weather Emergency Operations Center', 1959, '', True, '', 'Civilian (FEMA) site.', r'FEMA')
r('Project Greek Island (Greenbrier)', 'command_centre', 'Congressional relocation bunker', 'WV', 'White Sulphur Springs', 'Project Greek Island', 1962, 1995, True, '',
  'Civilian (Congress) continuity site, secret until 1992.', r'1962|1995')
r('Falcon AFS', 'command_centre', 'Consolidated Space Operations Center (2nd Space Wing)', 'CO', 'Colorado Springs', 'Schriever Space Force Base', 1985, '', False,
  'Built 1983-85; the 2nd Space Wing moved in only in September 1985 and took over satellite control from October 1987', '', r'September 1985')

# ---------------- nuclear weapons complex ----------------
r('Pantex Plant', 'nuclear_weapons_complex', 'Final weapons assembly and disassembly (DOE)', 'TX', 'Amarillo', 'Pantex Plant', 1951, '', True, '', '', r'assembl')
r('Rocky Flats Plant', 'nuclear_weapons_complex', 'Plutonium pit production (DOE)', 'CO', 'Arvada', 'Rocky Flats Plant', 1952, 1992, True, '',
  'Production halted by the 1989 FBI raid, ended 1992.', r'1952|1989')
r('Y-12 Plant', 'nuclear_weapons_complex', 'Uranium components, secondaries (DOE)', 'TN', 'Oak Ridge', 'Y-12 National Security Complex', 1943, '', True, '', '', r'1943')
r('Oak Ridge National Laboratory', 'nuclear_weapons_complex', 'National laboratory (DOE)', 'TN', 'Oak Ridge', 'Oak Ridge National Laboratory', 1943, '', True, '', '', r'1943')
r('K-25 (Oak Ridge Gaseous Diffusion Plant)', 'nuclear_weapons_complex', 'Uranium enrichment', 'TN', 'Oak Ridge', 'K-25', 1945, 1985, True,
  'Gaseous diffusion ceased on 27 Aug 1985, so the plant was still enriching at mid-1985', '', r'27 August 1985')
r('Savannah River Plant', 'nuclear_weapons_complex', 'Plutonium and tritium production reactors, reprocessing (DOE)', 'SC', 'Aiken', 'Savannah River Site', 1952, '', True, '',
  'Coordinates from the rendered article (Wikidata via the coordinates template).', r'tritium', [], (33.25, -81.65))
r('Hanford Site', 'nuclear_weapons_complex', 'Plutonium production (N Reactor to 1987, PUREX restarted 1983) (DOE)', 'WA', 'Richland', 'Hanford Site', 1943, 1989, True, '',
  'Production ended 1987-89; cleanup since.', r'PUREX|N Reactor')
r('Los Alamos National Laboratory', 'nuclear_weapons_complex', 'Weapons design laboratory (DOE)', 'NM', 'Los Alamos', 'Los Alamos National Laboratory', 1943, '', True, '', '', r'1943')
r('Sandia National Laboratories', 'nuclear_weapons_complex', 'Weapons engineering laboratory (DOE), on Kirtland AFB; branch at Livermore', 'NM', 'Albuquerque', 'Sandia National Laboratories', 1949, '', True, '', '', r'1949')
r('Lawrence Livermore National Laboratory', 'nuclear_weapons_complex', 'Weapons design laboratory (DOE)', 'CA', 'Livermore', 'Lawrence Livermore National Laboratory', 1952, '', True, '', '', r'1952')
r('Kansas City Plant', 'nuclear_weapons_complex', 'Non-nuclear components (Bendix, DOE)', 'MO', 'Kansas City', 'Kansas City Plant', 1949, 2014, True, '',
  'Bannister Federal Complex until 2014.', r'Bendix|1949')
r('Mound Laboratory', 'nuclear_weapons_complex', 'Detonators, tritium, Po/Pu heat sources (DOE)', 'OH', 'Miamisburg', 'Mound Laboratories', 1948, 2003, True, '', '', r'1948')
r('Pinellas Plant', 'nuclear_weapons_complex', 'Neutron generators (DOE)', 'FL', 'Largo', 'Pinellas Plant', 1957, 1994, True, '', 'GE operated it for the AEC/DOE 1957-1992; closure announced 1992, sold 1995.', r'1957')
r('Feed Materials Production Center', 'nuclear_weapons_complex', 'Uranium metal production (DOE)', 'OH', 'Fernald', 'Fernald Feed Materials Production Center', 1951, 1989, True, '', '', r'1989')
r('Paducah Gaseous Diffusion Plant', 'nuclear_weapons_complex', 'Uranium enrichment (DOE)', 'KY', 'Paducah', 'Paducah Gaseous Diffusion Plant', 1952, 2013, True, '', '', r'1952')
r('Portsmouth Gaseous Diffusion Plant', 'nuclear_weapons_complex', 'Uranium enrichment, HEU (DOE)', 'OH', 'Piketon', 'Portsmouth Gaseous Diffusion Plant', 1954, 2001, True, '', '', r'1954')
r('Idaho National Engineering Laboratory', 'nuclear_weapons_complex', 'Reactor testing, naval fuel reprocessing (ICPP) (DOE)', 'ID', 'Idaho Falls', 'Idaho National Laboratory', 1949, '', True, '',
  'Coordinates are the article\'s (central reservation).', r'1949')
r('Nevada Test Site', 'nuclear_weapons_complex', 'Nuclear test site (DOE)', 'NV', 'Mercury', 'Nevada Test Site', 1951, '', True, '',
  'Underground tests through 1992.', r'1951')

# ---------------- Army ----------------
A = 'army_corps_division_hq'; P = 'army_major_post'
r('Fort Lewis', A, 'I Corps; 9th Infantry Division (Motorized)', 'WA', 'Tacoma', 'Fort Lewis (Washington)', 1917, '', True, '', 'I Corps at Fort Lewis from 1981.', r'I Corps|9th Infantry')
r('Fort Hood', A, 'III Corps; 1st Cavalry Division; 2nd Armored Division', 'TX', 'Killeen', 'Fort Hood', 1942, '', True, '', 'Renamed Fort Cavazos 2023.', r'III Corps')
r('Fort Bragg', A, 'XVIII Airborne Corps; 82nd Airborne Division; JSOC', 'NC', 'Fayetteville', 'Fort Bragg', 1918, '', True, '', '', r'XVIII Airborne')
r('Fort Campbell', A, '101st Airborne Division (Air Assault)', 'KY', 'Fort Campbell', 'Fort Campbell', 1942, '', True, '', 'Straddles the Kentucky-Tennessee line.', r'101st')
r('Fort Stewart', A, '24th Infantry Division (Mechanized)', 'GA', 'Hinesville', 'Fort Stewart', 1940, '', True, '', '24th ID HQ activated here Oct 1974; to 1996.', r'24th Infantry Division was activated')
r('Fort Carson', A, '4th Infantry Division (Mechanized)', 'CO', 'Colorado Springs', 'Fort Carson', 1942, '', True, '', '4th ID 1970-1995.', r'4th Infantry')
r('Fort Riley', A, '1st Infantry Division (Mechanized)', 'KS', 'Junction City', 'Fort Riley', 1853, '', True, '', '1st ID 1970-1996 (one brigade in Germany).', r'1st Infantry')
r('Fort Polk', A, '5th Infantry Division (Mechanized)', 'LA', 'Leesville', 'Fort Polk', 1941, '', True, '', '5th ID 1975-1992.', r'5th Infantry')
r('Fort Ord', A, '7th Infantry Division (Light)', 'CA', 'Marina', 'Fort Ord', 1917, 1994, True, '', '7th ID 1974-1993; converted to light division 1985.', r'7th Infantry')
r('Fort Drum', A, '10th Mountain Division (Light)', 'NY', 'Watertown', 'Fort Drum', 1985, '', True,
  '10th Mountain Division reactivated 13 Feb 1985 at Fort Drum - in role by mid-1985, though still building up', '', r'1985')
r('Schofield Barracks', A, '25th Infantry Division', 'HI', 'Wahiawa', 'Schofield Barracks', 1908, '', True, '', '', r'25th Infantry')
r('Fort Richardson', P, '172nd Infantry Brigade (Alaska); US Army Alaska (6th ID (Light) from 1986)', 'AK', 'Anchorage', 'Fort Richardson (Alaska)', 1940, '', True, '',
  'HQ of the 6th Infantry Division (Light) 1986-1994.', r'6th Infantry')
r('Fort Benning', P, 'Infantry Center and School; 197th Infantry Brigade', 'GA', 'Columbus', 'Fort Benning', 1918, '', True, '', 'Renamed Fort Moore 2023, Fort Benning 2025.', r'Infantry')
r('Fort Bliss', P, 'Air Defense Artillery Center; 3rd Armored Cavalry Regiment', 'TX', 'El Paso', 'Fort Bliss', 1848, '', True, '', '', r'Air Defense')
r('Fort Knox', P, 'Armor Center and School; Bullion Depository', 'KY', 'Fort Knox', 'Fort Knox', 1918, '', True, '', '', r'Armor')
r('Fort Sill', P, 'Field Artillery Center and School; III Corps Artillery', 'OK', 'Lawton', 'Fort Sill', 1869, '', True, '', '', r'Artillery')
r('Fort Leavenworth', P, 'Combined Arms Center; Command and General Staff College', 'KS', 'Leavenworth', 'Fort Leavenworth', 1827, '', True, '', '', r'Command and General Staff')
r('Fort Sam Houston', P, 'Fifth US Army HQ; Health Services Command', 'TX', 'San Antonio', 'Fort Sam Houston', 1876, '', True, '', '', r'Fifth')
r('Fort Sheridan', P, 'Fourth US Army HQ', 'IL', 'Highland Park', 'Fort Sheridan, Illinois', 1887, 1993, True, '', '', r'Fourth|1993')
r('Fort George G. Meade', P, 'First US Army HQ; NSA HQ', 'MD', 'Odenton', 'Fort George G. Meade', 1917, '', True, '', '', r'First|National Security Agency')
r('Presidio of San Francisco', P, 'Sixth US Army HQ', 'CA', 'San Francisco', 'Presidio of San Francisco', 1846, 1994, True, '', '', r'Sixth')
r('Fort McPherson', P, 'US Army Forces Command (FORSCOM) and Third Army HQ', 'GA', 'Atlanta', 'Fort McPherson', 1885, 2011, True, '', '', r'Forces Command')
r('Fort Monroe', P, 'Training and Doctrine Command (TRADOC) HQ', 'VA', 'Hampton', 'Fort Monroe', 1823, 2011, True, '', '', r'TRADOC|Training and Doctrine')
r('Fort Jackson', P, 'Army Training Center (basic training)', 'SC', 'Columbia', 'Fort Jackson (South Carolina)', 1917, '', True, '', '', r'training')
r('Fort Leonard Wood', P, 'Engineer Center and Training Center', 'MO', 'Waynesville', 'Fort Leonard Wood (military base)', 1940, '', True, '', '', r'Engineer')
r('Fort Irwin', P, 'National Training Center', 'CA', 'Barstow', 'Fort Irwin National Training Center', 1981, '', True, '', 'NTC since 1981.', r'1981')
r('Redstone Arsenal', P, 'Army Missile Command; Marshall Space Flight Center', 'AL', 'Huntsville', 'Redstone Arsenal', 1941, '', True, '', '', r'Missile Command|MICOM')
r('Fort Dix', P, 'Army Training Center', 'NJ', 'Wrightstown', 'Fort Dix', 1917, '', True, '', '', r'training')

# ---------------- Air Force: TAC, MAC and other major bases ----------------
T = 'usaf_tac'; M = 'usaf_mac'; O = 'usaf_other'
r('Langley AFB', T, 'Tactical Air Command HQ; 1st Tactical Fighter Wing (F-15)', 'VA', 'Hampton', 'Langley Air Force Base', 1946, 1992, True, '', 'TAC HQ 1946-1992.', r'Tactical Air Command')
r('Nellis AFB', T, 'Tactical Fighter Weapons Center; 57th Fighter Weapons Wing; Red Flag', 'NV', 'Las Vegas', 'Nellis Air Force Base', 1949, '', True, '', '', r'Red Flag|Weapons')
r('Seymour Johnson AFB', T, '4th Tactical Fighter Wing (F-4E)', 'NC', 'Goldsboro', 'Seymour Johnson Air Force Base', 1957, '', True, '', '', r'4th')
r('Shaw AFB', T, '363rd Tactical Fighter Wing (F-16); Ninth Air Force HQ', 'SC', 'Sumter', 'Shaw Air Force Base', 1946, '', True, '', '', r'363')
r('Moody AFB', T, '347th Tactical Fighter Wing (F-4E)', 'GA', 'Valdosta', 'Moody Air Force Base', 1975, '', True, '', '', r'347')
r('Myrtle Beach AFB', T, '354th Tactical Fighter Wing (A-10)', 'SC', 'Myrtle Beach', 'Myrtle Beach Air Force Base', 1956, 1993, True, '', '', r'354')
r('England AFB', T, '23rd Tactical Fighter Wing (A-10)', 'LA', 'Alexandria', 'England Air Force Base', 1955, 1992, True, '', '', r'23d|23rd')
r('MacDill AFB', T, '56th Tactical Training Wing (F-16); US Central Command and Readiness Command HQ', 'FL', 'Tampa', 'MacDill Air Force Base', 1962, '', True, '',
  'SAC bomber base until 1962; USCENTCOM from 1983.', r'Central Command')
r('Eglin AFB', T, '33rd Tactical Fighter Wing (F-15); AFSC Armament Division', 'FL', 'Valparaiso', 'Eglin Air Force Base', 1935, '', True, '', '', r'33')
r('Tyndall AFB', T, '325th Tactical Training Wing (F-15); First Air Force / ADTAC (air defense)', 'FL', 'Panama City', 'Tyndall Air Force Base', 1941, '', True, '', '', r'325')
r('Homestead AFB', T, '31st Tactical Fighter Wing (F-4D, F-16 from 1985)', 'FL', 'Homestead', 'Homestead Air Reserve Base', 1955, 1992, True, '',
  'Destroyed by Hurricane Andrew 1992; now an Air Reserve base.', r'31st')
r('Mountain Home AFB', T, '366th Tactical Fighter Wing (F-111A, EF-111A)', 'ID', 'Mountain Home', 'Mountain Home Air Force Base', 1966, '', True, '', '', r'366')
r('Luke AFB', T, '405th and 58th Tactical Training Wings (F-15, F-16)', 'AZ', 'Glendale', 'Luke Air Force Base', 1941, '', True, '', '', r'58th|405th')
r('Davis-Monthan AFB', T, '355th Tactical Training Wing (A-10); MASDC aircraft storage', 'AZ', 'Tucson', 'Davis–Monthan Air Force Base', 1976, '', True, '',
  'SAC host until 1976 (390th SMW tenant to 1984).', r'355')
r('Holloman AFB', T, '49th Tactical Fighter Wing (F-15)', 'NM', 'Alamogordo', 'Holloman Air Force Base', 1968, '', True, '', '', r'49th')
r('Cannon AFB', T, '27th Tactical Fighter Wing (F-111D)', 'NM', 'Clovis', 'Cannon Air Force Base', 1959, '', True, '', '', r'27th')
r('Bergstrom AFB', T, '67th Tactical Reconnaissance Wing (RF-4C); Twelfth Air Force HQ', 'TX', 'Austin', 'Bergstrom Air Force Base', 1966, 1993, True, '',
  'SAC base until 1966.', r'67th|Twelfth')
r('George AFB', T, '35th and 37th Tactical Fighter Wings (F-4E, F-4G Wild Weasel)', 'CA', 'Victorville', 'George Air Force Base', 1950, 1992, True, '', '', r'Wild Weasel|35th')
r('Hill AFB', T, '388th Tactical Fighter Wing (F-16); Ogden Air Logistics Center (ICBM depot)', 'UT', 'Ogden', 'Hill Air Force Base', 1940, '', True, '',
  'AFLC depot responsible for Minuteman maintenance.', r'388')
r('Tinker AFB', T, '552nd AWAC Wing (E-3); Oklahoma City Air Logistics Center', 'OK', 'Oklahoma City', 'Tinker Air Force Base', 1977, '', True, '',
  'Years are the AWACS wing\'s; base dates from 1942.', r'552|AWACS|E-3')
r('Scott AFB', M, 'Military Airlift Command HQ; 375th Aeromedical Airlift Wing', 'IL', 'Belleville', 'Scott Air Force Base', 1957, '', True, '', 'MAC HQ 1957-1992; USTRANSCOM from 1987.', r'Military Airlift Command')
r('Travis AFB', M, '60th Military Airlift Wing (C-5, C-141); Twenty-Second Air Force', 'CA', 'Fairfield', 'Travis Air Force Base', 1966, '', True, '', 'SAC base until 1968.', r'60th')
r('McChord AFB', M, '62nd Military Airlift Wing (C-141); 25th NORAD Region', 'WA', 'Tacoma', 'McChord Field', 1947, '', True, '', '', r'62')
r('Charleston AFB', M, '437th Military Airlift Wing (C-141)', 'SC', 'North Charleston', 'Joint Base Charleston', 1953, '', True, '', '', r'437')
r('Dover AFB', M, '436th Military Airlift Wing (C-5)', 'DE', 'Dover', 'Dover Air Force Base', 1952, '', True, '', '', r'436')
r('McGuire AFB', M, '438th Military Airlift Wing (C-141); Twenty-First Air Force', 'NJ', 'Wrightstown', 'McGuire Air Force Base', 1954, '', True, '', '', r'438')
r('Norton AFB', M, '63rd Military Airlift Wing (C-141); Ballistic Missile Office', 'CA', 'San Bernardino', 'Norton Air Force Base', 1966, 1994, True, '', '', r'63')
r('Altus AFB', M, '443rd Military Airlift Wing (C-5/C-141 training)', 'OK', 'Altus', 'Altus Air Force Base', 1969, '', True, '', '', r'443')
r('Pope AFB', M, '317th Tactical Airlift Wing (C-130)', 'NC', 'Fayetteville', 'Pope Field', 1974, '', True, '', '', r'317')
r('Little Rock AFB', M, '314th Tactical Airlift Wing (C-130)', 'AR', 'Jacksonville', 'Little Rock Air Force Base', 1970, '', True, '', '', r'314')
r('Andrews AFB', M, '89th Military Airlift Wing (presidential airlift)', 'MD', 'Camp Springs', 'Andrews Field', 1966, '', True, '', 'Air Force One base; AFSC HQ also here.', r'89th')
r('Hurlburt Field', M, '1st Special Operations Wing; Twenty-Third Air Force', 'FL', 'Mary Esther', 'Hurlburt Field', 1983, '', True, '', 'MAC from 1983 (TAC earlier).', r'1st Special Operations')
r('Wright-Patterson AFB', O, 'Air Force Logistics Command HQ; Aeronautical Systems Division (AFSC)', 'OH', 'Dayton', 'Wright-Patterson Air Force Base', 1948, '', True, '', '', r'Logistics Command')
r('Kirtland AFB', O, 'Air Force Weapons Laboratory; Defense Nuclear Agency Field Command; Manzano weapons storage', 'NM', 'Albuquerque', 'Kirtland Air Force Base', 1947, '', True, '',
  'Hosts Sandia National Laboratories.', r'Manzano|Weapons Laboratory')
r('Elmendorf AFB', O, 'Alaskan Air Command HQ; 21st Tactical Fighter Wing (F-15)', 'AK', 'Anchorage', 'Elmendorf Air Force Base', 1951, '', True, '', '', r'Alaskan Air Command')
r('Hickam AFB', O, 'Pacific Air Forces HQ', 'HI', 'Honolulu', 'Hickam Air Force Base', 1957, '', True, '', '', r'Pacific Air Forces')
r('Eielson AFB', O, '343rd Composite Wing (A-10, O-2)', 'AK', 'Fairbanks', 'Eielson Air Force Base', 1981, '', True, '', '', r'343')

# ---------------- Marine Corps ----------------
U = 'marine_corps_base'
r('Camp Lejeune', U, '2nd Marine Division; II Marine Amphibious Force', 'NC', 'Jacksonville', 'Camp Lejeune', 1941, '', True, '', '', r'2nd Marine Division|II Marine')
r('Camp Pendleton', U, '1st Marine Division; I Marine Amphibious Force', 'CA', 'Oceanside', 'Marine Corps Base Camp Pendleton', 1942, '', True, '', '', r'1st Marine Division|I Marine')
r('MCAS Cherry Point', U, '2nd Marine Aircraft Wing', 'NC', 'Havelock', 'Marine Corps Air Station Cherry Point', 1942, '', True, '', '', r'2nd Marine Aircraft Wing')
r('MCAS El Toro', U, '3rd Marine Aircraft Wing', 'CA', 'Irvine', 'Marine Corps Air Station El Toro', 1943, 1999, True, '', '', r'3rd Marine Aircraft Wing')
r('MCAGCC Twentynine Palms', U, 'Marine Corps Air Ground Combat Center; 7th Marine Amphibious Brigade', 'CA', 'Twentynine Palms', 'Marine Corps Air Ground Combat Center Twentynine Palms', 1952, '', True, '', '', r'1952|Combat Center')
r('MCB Quantico', U, 'Marine Corps Development and Education Command', 'VA', 'Quantico', 'Marine Corps Base Quantico', 1917, '', True, '', '', r'1917')
r('MCRD Parris Island', U, 'Recruit Depot (East)', 'SC', 'Beaufort', 'Marine Corps Recruit Depot Parris Island', 1915, '', True, '', '', r'recruit')
r('MCRD San Diego', U, 'Recruit Depot (West)', 'CA', 'San Diego', 'Marine Corps Recruit Depot San Diego', 1921, '', True, '', '', r'recruit')
r('MCAS Kaneohe Bay', U, '1st Marine Amphibious Brigade', 'HI', 'Kaneohe', 'Marine Corps Air Station Kaneohe Bay', 1952, '', True, '', 'Unit from general knowledge (the article names the 1st Marine Aircraft Wing elements).', r'Marine')
r('MCAS Beaufort', U, 'Marine Aircraft Group 31 (F-4, F/A-18)', 'SC', 'Beaufort', 'Marine Corps Air Station Beaufort', 1960, '', True, '', '', r'Marine Aircraft Group 31|MAG-31')
r('MCAS Yuma', U, 'Marine Aircraft Group 13 (AV-8)', 'AZ', 'Yuma', 'Marine Corps Air Station Yuma', 1959, '', True, '', '', r'1959')
r('MCAS New River', U, 'Marine helicopter groups (2nd MAW)', 'NC', 'Jacksonville', 'Marine Corps Air Station New River', 1951, '', True, '', '', r'helicopter')
r('MCAS Tustin', U, 'Marine helicopter groups (3rd MAW)', 'CA', 'Tustin', 'Marine Corps Air Station Tustin', 1942, 1999, True, '', '', r'helicopter|1999')
