# Release 004: Physics Research for the Ball Flight Model Audit

**Release:** Ball flight laws instructor tool (analysis/004-ball-flight-laws, site/ball-flight).
**Purpose:** Audit the launch model (launch.py), the flight model (flight.py) and ADR 0004 against published physics. This file follows the citation style of 004_Source_Log.md: numbered sources, link, retrieval date, what was read, and a verdict per topic. Nothing here changes code.
**Retrieval date for every source below:** 2026-09-29.
**Researcher:** Claude (WebSearch, WebFetch, and raw page and PDF reads through curl into a scratch folder).

## Read codes

Each fact below carries the way it was obtained.

- **RAW:** page HTML or PDF text layer, read as published.
- **API:** title, authors or abstract read from Crossref, Semantic Scholar or OpenAlex JSON.
- **SNIPPET:** a line from a WebSearch result. Snippets are leads. No snippet number is used as a value in this file.
- **DERIVED:** geometry or arithmetic done for this file from inputs that are stated next to it. Derived numbers are not published numbers.
- **COMPUTED:** output of the repo's own launch.py and flight.py, run for this file with the shipped parameters (TrackMan 2023 presets, default aero). Inputs are given so a reader can repeat the run.

Pages that refused a fetch were not worked around: MDPI (Access Denied), IOP Science (Radware captcha), Canadian Science Publishing, Springer, Taylor and Francis, Academia.edu and ScienceDirect (Cloudflare challenge), ResearchGate (access restricted), GolfWRX (Cloudflare block), Golf Digest (Access Denied), the TrackMan support center (Cloudflare challenge), Yumpu (page holds a table of contents and no text). The Internet Archive CDX index was offline at the time of the last query.

## Status of the model against this audit

The verdicts in the table below are as written on 2026-09-29, before any code changed. Since then:

- Topics 1 and 13 (face-to-loft coupling, loft follows attack angle): implemented 2026-09-29 (ADR 0004 addenda 3 and 4).
- Topic 5 (attack angle moves the path): the lab's path-follows-attack switch, on by default, holds the swing direction on a per-club swing plane (ADR 0004 addendum 5, source log Anchor 12), after a reviewer made the point that a vertical change in the attack angle tilts the arc and shifts the horizontal path.
- Topic 6 (lie at impact): a `lie_deg` input, an exact rotation of the face normal about the target line (addendum 5, Anchor 14).
- Topic 7 (strike location): `strike_toe_mm` and `strike_up_mm` inputs with the horizontal gear effect from Tuxen's four rows, the vertical gear effect at Tutelman's ratio on the driver and fairway woods, TrackMan's bulge and roll numbers, and a modeled smash loss (addendum 5, Anchor 13).
- Topic 8 (measurement references): named in the lab's footer and the article's Conventions note (addendum 5).
- Topics 2 (draw against fade distance) followed from topic 1. Topics 9 (extreme spin loft) and 11 (bounce and roll) are still as the table says.

## Summary of findings

| # | Topic | Best evidence found | Model captures it? |
|---|---|---|---|
| 1 | Face angle and effective loft coupling | TrackMan says open or closed face to path changes dynamic loft (no coefficient). Geometry gives 0 to about 0.6 degree of loft per degree of face rotation. | No. Face angle and dynamic loft are independent inputs. |
| 2 | Draw versus fade distance | TrackMan blog example: draw 10.5 deg dynamic loft, 2643 rpm, 28.8 deg landing, about 20 yd more run. | No. Draw and fade are exact mirror images (COMPUTED). |
| 3 | D-plane and spin axis | Tuxen 2009: launch lies in the D-plane, spin axis is 90 deg to it, D-plane angle is spin loft. Rules of thumb: axis is 4 times face-to-path for a driver, 2 times for a 6 iron. | Yes. |
| 4 | Start direction share | Tuxen 85 percent face rule. Dewhurst (as quoted by PING) 87, 75, 70 percent for driver, 7 iron, wedge. PING measured 83, 81, 72. | Yes. |
| 5 | Attack angle, swing direction, path | Tuxen 2009 worked examples confirm path equals swing direction minus attack angle times cot of the vertical swing plane. | Partly. Helper exists (hold swing direction toggle). Sliders are otherwise independent. |
| 6 | Lie angle at impact | Derived: face aim changes by tan(loft) per degree of lie. Secondary sources agree on direction and on the order of clubs. | No. |
| 7 | Impact location | Tuxen 2009 gives a table for driver and 6 iron. TrackMan gives bulge and roll numbers. | No. spin_trim is one preset scalar. |
| 8 | Center face versus CoG references | TrackMan Club Data Definitions: driver path 3 deg more outside-in at center face, attack angle 1 deg higher. | A labeling issue. |
| 9 | Spin loft, smash, spin, oblique impact | TrackMan and Tuxen relations agree with the fitted quadratics. A rolling-contact derivation reproduces the start direction shares. | Yes for smash and spin. Partly for extreme spin loft. |
| 10 | Aerodynamics and curvature per degree | 0.7 to 0.75 percent of carry per degree of spin axis (TrackMan). Spin decay near 4 percent per second (TrackMan, via Tutelman). | Yes. |
| 11 | Bounce and roll | TrackMan: landing speed, angle and spin set the run. Bristol and R&A bounce data. Penner's model not readable. | Partly. One empirical formula fitted to driver rows. |
| 12 | Teaching caveats | Higher lofts curve less, hitting down does not add spin by itself, curvature is a near constant share of carry. | Yes for these three. |
| 13 | Irons and wedges: attack angle, dynamic loft, compression | Arc geometry gives 1.0 degree of dynamic loft per degree of attack angle (TrackMan rule). A Foresight 7 iron chart implies about 1.4. Higher attack angle then costs carry at 90 mph and above. | No. Attack angle and dynamic loft are independent sliders. |

---

## Sources

**S1. TrackMan News #4, January 2009, "The Secret of the Straight Shot" (Fredrik Tuxen interview).** Original URL trackman.dk/getmedia/55e8af48-81db-4fee-9fa0-0e763e9ac9a5/TMNewsJan2009.aspx is dead. Read from the Internet Archive snapshot of 2013-08-03: [web.archive.org copy](http://web.archive.org/web/20130803015048/http://trackman.dk:80/getmedia/55e8af48-81db-4fee-9fa0-0e763e9ac9a5/TMNewsJan2009.aspx). Read: RAW (PDF text, 13 pages). Primary. Tuxen is TrackMan's inventor and CTO.

**S2. TrackMan News #5, July 2009, "The Secret of the Straight Shot II" (Tuxen).** [web.archive.org copy, snapshot 2013-08-26](http://web.archive.org/web/20130826173544/http://trackman.dk:80/getmedia/2f6c5cdc-e153-466c-9e1a-f8b612947435/TMNewsJul2009_1.aspx). Read: RAW (PDF text, 15 pages). Primary. This is the best available text for the D-plane, the spin axis rules of thumb and horizontal gear effect.

**S3. TrackMan blog, "Draw or Fade to Maximize Distance in Golf" (Tom Stickney II, dated 2016-04-11).** [trackman.com/blog/golf/draw-or-fade-to-maximize-distance](https://www.trackman.com/blog/golf/draw-or-fade-to-maximize-distance). Read: RAW. Primary as a TrackMan publication. The shots came from one TaylorMade R15 driver and the page says clubhead speeds were almost the same.

**S4. TrackMan "10 Fundamentals" slide document.** [PDF hosted by Troxhammar GK](https://www.troxhammargk.se/media/t4dn2xcy/trackman-s-10-fundamentals.pdf). Read: RAW (text layer; charts inside images were not read). Primary. No date printed in the text.

**S5. TrackMan data parameter sheet, Release 3.1.** [PDF hosted by Hank Haney Golf](https://hankhaney.com/app/uploads/2019/01/TrackmanTERMS.pdf). Read: RAW. TrackMan document, older software release. Its Tour averages are old and are not used.

**S6. TrackMan blog definition pages.** Read: RAW on 2026-09-29. Primary.
[Spin Loft](https://www.trackman.com/blog/spin-loft), [Dynamic Loft](https://www.trackman.com/blog/dynamic-loft), [Smash Factor](https://www.trackman.com/blog/smash-factor), [Spin Rate](https://www.trackman.com/blog/spin-rate), [Launch Angle](https://www.trackman.com/blog/launch-angle), [Attack Angle](https://www.trackman.com/blog/attack-angle), [Face Angle](https://www.trackman.com/blog/what-is-face-angle), [Face to Path](https://www.trackman.com/blog/face-to-path), [Spin Axis](https://www.trackman.com/blog/spin-axis), [Understanding Club Data in Golf](https://www.trackman.com/blog/club-data-definitions), [The true impact factors](https://www.trackman.com/blog/golf/trackman-talks-the-true-impact-factors), [Smash Index and Spin Index](https://www.trackman.com/blog/trackman-talks-master-the-smash-index-and-spin-index) (no formulas published there).

**S7. Henrikson, Wood, Broadie, Nuttall (PING), "The Role of Friction and Tangential Compliance on the Resultant Launch Angle of a Golf Ball," Proceedings 49(1):27, ISEA 2020.** [PDF via Semantic Scholar](https://pdfs.semanticscholar.org/85d6/34c59fa8658a17fae5044d5c17c0fd8deed8.pdf). Read: RAW, full text (figures are images and were not read). Peer-reviewed conference paper from a club maker's engineering group. 157 golfers, 1,575 shots.

**S8. Wood, Henrikson, Broadie (PING), "The Influence of Face Angle and Club Path on the Resultant Launch Angle of a Golf Ball," Proceedings 2(6):249, ISEA 2018.** [doi.org/10.3390/proceedings2060249](https://doi.org/10.3390/proceedings2060249). Read: API (Semantic Scholar and OpenAlex), abstract alone. The MDPI body returned Access Denied. Abstract: two studies (motion capture with Foresight ball data, and a robot with a high-speed camera), launch direction fell closer to the face than to the path, percent toward the face ranged from 61 to 83.

**S9. Cross and Nathan, "Experimental study of the gear effect in ball collisions," American Journal of Physics 75(7):658, 2007.** [PDF, University of Sydney](https://www.physics.usyd.edu.au/~cross/PUBLICATIONS/37.%20GearEffect.pdf). Read: RAW. Peer reviewed. Tennis ball on a moving surface and a golf ball on a wood block, with the theory in an appendix.

**S10. Cross and Nathan, "Performance versus moment of inertia of sporting implements," Sports Technology 2:7, 2009.** [PDF, University of Illinois](https://baseball.physics.illinois.edu/jwuk_jst_88_web.pdf). Read: RAW. Peer reviewed. Source of the effective mass relation used in Topic 7.

**S11. Dave Tutelman, "All about Gear Effect," 2009.** [tutelman.com/golf/ballflight/gearEffect.php](https://www.tutelman.com/golf/ballflight/gearEffect.php). Read: RAW. Secondary. An engineer's analytic model. The author says he validated it against Hotstix data from Golf Magazine. That data was not read.

**S12. Dave Tutelman, "Spin Decay for a Ball in Flight," 2016.** [tutelman.com/golf/ballflight/spinDecay.php](https://www.tutelman.com/golf/ballflight/spinDecay.php). Read: RAW. Secondary. It quotes the TrackMan newsletter of October 2010. The October 2010 newsletter itself was not read.

**S13. Biber, Jones, Champneys, Green, Szalai (Bristol, with R&A Rules Ltd), "Measurements and linearized models for golf ball bounce," arXiv 2302.02758, 2023.** [arxiv.org/pdf/2302.02758](https://arxiv.org/pdf/2302.02758). Read: RAW, methods, tables and conclusions. Preprint. 1,023 bounces on artificial tee turf and a natural tee.

**S14. Mitchell Golf, "Loft, Lie & Face Angles" club-building guide, 2010.** [PDF](https://www.mitchellgolf.com/wp-content/uploads/2017/05/measuring-bending.pdf). Read: RAW. Secondary, a club maker's note on static head geometry.

**S15. Golf.com, driver heel and toe miss robot test (Golf Laboratories robot, 95 mph).** [golf.com article](https://golf.com/gear/drivers/driver-miss-heel-toe-robot-test/). Read: RAW. Secondary, magazine.

**S16. Andrew Rice (TrackMan Master), "TrackMan Exposes Golf Myths," 2012.** [andrewricegolf.com](https://www.andrewricegolf.com/andrew-rice-golf/2012/05/trackman-exposes-golf-myths). Read: RAW. Secondary, coach blog.

**S17. Golf Club Brokers, "Lie Angle Explained."** [golfclubbrokers.com](https://www.golfclubbrokers.com/blog/lie-angle-explained). Read: RAW. Secondary, retailer article, no citations.

**S19. The Sand Trap, "Ball Flight Laws."** [thesandtrap.com](https://thesandtrap.com/b/playing_tips/ball_flight_laws). Read: RAW. Secondary. It reproduces Tuxen's 85 and 15 rule from the January 2009 newsletter and adds unsourced claims (see Topic 4).

**S18. Existing 004 Source Log, Anchor 7.** Carries Nathan's trajectory calculator, Bearman and Harvey (via Pallis and Mehta), Smits and Smith spin decay (via Nathan), Crabill et al. CFD, Kensrud's thesis and McNally et al. Cited here by reference. Those sources were not re-read for this file.

**S20. Foresight Sports blog, "How To Optimize Iron Distance Based On Swing Speed" (2025-01-06), with its "7 Iron Angle of Attack Chart."** [foresightsports.com blog](https://www.foresightsports.com/blogs/golf-tips/how-to-optimize-iron-distance-based-on-swing-speed) and [chart image](https://cdn.shopify.com/s/files/1/1796/5675/files/Gene_Parente_chart_1.png?v=1734643321). Read: RAW for the text, IMAGE for the chart (transcribed by eye from the picture; the 100 mph row was checked against the text's 21.7 yd figure). Manufacturer data, not peer reviewed. The page says 7 irons were tested at 60 to 100 mph of head speed at attack angles of -6, -4, -2, 0 and +2. It does not say who or what swung the club, how the attack angle was set, or the club's loft. The full report it links to was not found. The image file name mentions Gene Parente, and a Golf Digest result names him as the Golf Laboratories robot operator, so a robot is likely but unconfirmed.

**S21. Suzuki, Sheahan, Miyazawa, Okuda, Ichikawa, "Comparison of TrackMan Data between Professional and Amateur Golfers at Swinging to Uphill and Downhill Fairways," The Open Sports Sciences Journal 14:137, 2021.** [PDF](https://opensportssciencesjournal.com/contents/volumes/V14/TOSSJ-14-137/TOSSJ-14-137.pdf). Read: RAW, methods, Table 1, Table 2 and discussion. Peer reviewed, open access. 42 professionals and 25 amateurs hit their own drivers off a flat tee toward a fairway rising or falling 5 degrees.

**S22. Andrew Rice (TrackMan Master), spin loft and wedge posts.** [tag page](https://www.andrewricegolf.com/andrew-rice-golf/tag/spin+loft). Read: RAW. Secondary coach blog. Its TrackMan screenshots were not readable, so the text is the sole part used.

**Sources named in the brief that could not be read.**

- **Tuxen, "TrackMan Ball Flight Laws" (25 pages).** Yumpu returns no text. S1 and S2 are Tuxen's own interview statements and stand in for it.
- **Jorgensen, *The Physics of Golf*; Cochran and Stobbs, *Search for the Perfect Swing*; Dewhurst, *The Science of the Perfect Swing*.** Books. Their launch ratio figures reach this file through S7 alone.
- **Penner, "The physics of golf," Rep. Prog. Phys. 66:131 (2003), and "The run of a golf ball," Can. J. Phys. 80:931 (2002).** Blocked. The abstract of the second is the one part known, from a search result (SNIPPET).
- **Caldwell and McPhee, Sports Engineering 27:16 (2024).** Springer blocked. Abstract known from a search result (SNIPPET).
- **Brožka et al., International Journal of Performance Analysis in Sport 23(5), 2023, "Impact factors analysis."** Taylor and Francis blocked. A search result says launch angle is 70 to 80 percent dynamic loft and launch direction 70 to 85 percent face angle by club (SNIPPET, unverified).
- **Mizota, Bearman and Harvey originals, Smits and Smith, Arakawa, Lyu et al., USGA and R&A equipment notes, Wishon, PING and Titleist white papers.** No readable text found this session.

---

## Topic 1. Face angle and effective loft coupling (pulls versus pushes, hooks versus slices)

**Mechanism.**

- TrackMan lists what moves dynamic loft: attack angle, shaft bend, how the golfer releases the head, whether the face is open or closed to the path, and strike location (S6, Dynamic Loft). It gives no sign and no coefficient.
- Geometry supplies the size of the effect (DERIVED). Rotate the head about the shaft axis by an angle phi, open positive, with the shaft at lie angle lambda and no shaft lean. The face aim changes by phi times sin(lambda) and the loft changes by phi times cos(lambda). Loft does not appear in either result. The loft change per degree of face change is cot(lambda).
- A run of the rotation (COMPUTED from the geometry, 3 degrees of opening, lie 60): face +2.61, loft +1.50, ratio 0.57 to 0.58 for lofts 10.5 to 58. Lie 64 gives 0.48 to 0.49. Adding 8 degrees of forward shaft lean raises the ratio to 0.60 (10.5 deg loft) through 0.75 (58 deg loft) at lie 60.
- A yaw of the whole club about a vertical axis moves the face angle and leaves loft alone. So the coupling coefficient runs from 0 (yaw) to about 0.6 (roll about the shaft, the forearm release). No source read says where real golfers sit inside that range.
- Direction: opening adds loft and closing removes it. The club maker's note (S14) gives a related static fact. A wood or hybrid built with a closed face angle plays with more loft when squared at address, and one built open plays with less, about one for one (its 9.5 degree driver plays like 8.5 with a 1 degree open face and like 11.5 with 2 closed). That is static head geometry, not a swing measurement. The link to the swing is this file's reading: squaring a head built closed means opening it about the shaft, which adds loft.

**Observed effect on ball flight (S3, one driver, one player).**

| Shot | Dynamic loft | Spin | Height | Landing angle | Carry |
|---|---|---|---|---|---|
| Fade | 15 deg | 3768 rpm | 105.6 ft | 42.9 deg | 240.8 yd |
| Draw | 10.5 deg | 2643 rpm | 63.6 ft | 28.8 deg | 245.7 yd |
| Slice (extreme) | not given | 5218 rpm | not given | 45.3 deg | not given |
| Hook (extreme) | not given | 1992 rpm | not given | 19.4 deg | not given |

The page says the draw's lower landing angle gives it almost 20 yd more run-out. It also says big hooks carry less than slices but run out more, and that soft turf favors the slice and firm turf favors the hook. The page contradicts itself on carry. One paragraph says the fade carried farther than the draw, and the table above lists the draw as farther by 4.9 yd. Treat the carry sign as unresolved and the loft, spin and landing angle contrast as the finding.

**Pull versus push.** No primary source was found that compares a pull with a push at zero face-to-path. In the D-plane a straight pull and a straight push are mirror images with equal spin loft, so equal carry. Secondary coaching pages say pulls carry less dynamic loft and go farther on mid and short irons. Those pages are search results (SNIPPET) and the GolfWRX thread was blocked, so no distance figure from them is used. A TrackMan Master states that in a controlled case a draw and a fade go the same distance and that the real gap comes from the different impact conditions that usually produce them (S16).

**Magnitude.** In S3 the two shots differ by 4.5 degrees of dynamic loft, 1125 rpm and 14 degrees of landing angle. Whether that came from face-to-path alone is not stated.

**Source quality.** TrackMan blog example (one player, uncontrolled) plus DERIVED geometry. No measured coupling coefficient.

**Does our model capture it? No.** In launch.py face angle and dynamic loft are separate inputs. Spin loft grows a little with face-to-path (13.59 to 14.15 deg at 4 degrees, COMPUTED), and no term ties loft to face rotation.

## Topic 2. Draw versus fade distance

**TrackMan's analysis (S3, S4, S1).**

- The S3 numbers are in Topic 1.
- S3 and S16 agree that a draw and a fade with the same delivery except the spin axis sign carry the same distance. The differences come from dynamic loft, spin and landing angle.
- Tuxen (S1, S4) lists three ways to start and hold a shot on the target line. Method 1 is path 0, face 0, center strike, and carries farthest. Method 2 is an inside-out path with a closed face and a heel strike, which carries shortest. Method 3 is an outside-in path with an open face and a toe strike. S1 calls its carry "medium" and S4 calls it "short." Heel head speed is below center head speed and toe head speed is above it (S1).
- S3 also says a draw can lose carry when the ball comes out too flat, which happens when attack angle and dynamic loft leave the useful range.

**Mechanism.**

1. Face-to-path changes dynamic loft (Topic 1), and dynamic loft sets launch, spin loft and spin.
2. Landing angle and landing spin set the run (Topic 11, S4 fundamental 10).
3. A tilted spin axis moves some lift off the vertical, a small carry cost (Topic 10).
4. Off-center strikes change speed, spin and axis (Topic 7).

**Magnitude in the model (COMPUTED, PGA driver preset, path and face split equally about zero, face-to-path plus or minus 4).**

| Case | Carry | Total | Spin | Landing angle |
|---|---|---|---|---|
| Straight | 282.1 | 312.9 | 2545 | 39.3 |
| Draw (FTP -4) | 272.2 | 304.6 | 2648 | 38.0 |
| Fade (FTP +4) | 272.2 | 304.6 | 2648 | 38.0 |

PGA 7 iron: straight 171.7 / 178.5, draw and fade both 169.9 / 176.8. Amateur driver: straight 212.7 / 238.3, draw and fade both 207.6 / 233.8. Pull (path -4, face -4) and push (path +4, face +4) are also mirror images: 281.4 carry and 312.2 total for the PGA driver, 171.3 and 178.1 for the 7 iron.

**Source quality.** TrackMan blog (one player) plus Tuxen's three-method table. No controlled dataset found.

**Does our model capture it? No.** The model gives equal carry and total to the last digit for draw and fade, and for pull and push. That agrees with the controlled-case physics (S16) and disagrees with the observed loft, spin and run contrast in S3.

## Topic 3. D-plane geometry and spin axis formulas

**Definitions (S2, RAW).**

- The D-plane is the wedge-shaped plane between two 3D directions. One is the clubhead direction at impact, set by attack angle and club path. The other is the face orientation at impact, set by dynamic loft and face angle. The angle of the wedge is the spin loft.
- The ball's initial direction lies in the D-plane.
- For a center strike the spin axis is 90 degrees to the D-plane.
- TrackMan's Spin Loft page (S6) defines spin loft as the 3D angle between the CoG movement direction and the face orientation at the center of contact, and says dynamic loft minus attack angle approximates it with the error growing as face-to-path grows. The Spin Axis page says indoor TrackMan computes spin axis from spin loft and face-to-path. No equation is printed on any page read.
- Secondary pages credit Jorgensen with the D-plane concept. The book was not read.

**Formulas (DERIVED, frame x downrange, y right, z up).**

- Club direction d = (cos AA cos P, cos AA sin P, sin AA). Face normal n = (cos DL cos FA, cos DL sin FA, sin DL). TrackMan's text says face angle is horizontal and dynamic loft vertical orientation. The rule for composing them into a normal is not printed in anything read, so the azimuth and elevation reading in launch.py is an assumption.
- cos SL = cos AA cos DL cos(P - FA) + sin AA sin DL. For small angles SL squared is (DL - AA) squared plus cos AA cos DL times FTP squared. Check against the model: DL 12.685, AA -0.9, FTP 4 gives 14.15 by this formula and 14.15 in launch.py.
- D-plane normal m = d cross n. For small angles the tilt of that normal is atan(FTP / (DL - AA)), which is the atan2 form in launch.py's docstring.
- Check against Tuxen's rules of thumb (S2): face 5, path 3 (FTP 2). Driver: atan(2 / 14.7) = 7.7 deg, Tuxen says about 8. 6 iron: atan(2 / 24.3) = 4.7 deg, Tuxen says about 4. Tuxen's ratio is 4 times face-to-path for a driver and 2 times for a 6 iron, and he says the driver ratio is larger because its spin loft is about half that of a 6 iron.
- Launch direction inside the D-plane: u is a blend of d and n with weight k on the face (Topic 4).

**Where attack angle and dynamic loft enter.** They set the vertical spin loft (DL - AA). Face-to-path sets the sideways tilt. The tilt is FTP divided by spin loft, so it shrinks as spin loft grows.

**Friction and other caveats.** The axis is perpendicular to the plane when the friction force lies in the plane, which holds for a center strike. S7 and S9 model the contact with tangential compliance or gripping. Off-center strikes add gear effect sidespin (Topic 7).

**Source quality.** Primary (TrackMan, Tuxen) for the definition and rules of thumb, DERIVED for the equations. Tuxen's 25-page paper stays unread.

**Does our model capture it? Yes.** launch.py builds d and n, takes spin loft as the 3D angle, blends toward n and tilts by the D-plane normal times a scale c(SL) = 1.218 - 0.00883 SL (COMPUTED per degree of FTP: driver 4.5, 7 iron 2.0, wedge 1.35, against Tuxen's 4 and 2). The scale is fitted to TrackMan's eight face-to-path curvature examples (ADR 0004).

## Topic 4. Start direction share of face versus path

**Published figures.**

| Source | Driver | 7 iron or 6 iron | Wedge | Note |
|---|---|---|---|---|
| Tuxen 2009 (S1, S2, RAW) | 85 percent face | not split by club | not split | Rule of thumb. Example: path +6.7 and face -1 start on line. |
| TrackMan via Dewhurst 2015, quoted in S7 Table 1 | 87 | 75 (7 iron) | 70 (PW) | Vertical plane, share toward face normal. Book unread. |
| PING measured, S7 Table 1 | 83 (spread 8) | 81 (spread 5) | 72 (spread 6) | Vertical plane, 731 driver, 745 iron, 99 wedge shots. The plus or minus symbol was lost in extraction, so the spreads are the trailing numbers. |
| PING 2018 abstract (S8, API) | 61 to 83 across clubs and both planes | | | Body unread, so the horizontal-plane split is unknown. |

- Cochran and Stobbs published one example of a -20 degree path with 0 face and a ball direction near -7 degrees (search result summary, SNIPPET, a lead). S7 says Cochran and Stobbs and TrackMan both published such ratios.
- Unverified secondary claims (S19, The Sand Trap article, RAW): the face share for a wedge approaches 50 percent and stays above about 55, a putter reaches the mid to high 90s, and long drivers reach the low 90s. The article gives no measurement and attributes the figures to a MyGolfSpy test that was blocked. None is used.

**Physics (S7, RAW).**

- The launch direction lies between the path and the face normal for an oblique impact.
- S7 defines the launch ratio as the launch angle relative to path divided by the face normal angle relative to path. The measured ratio falls as loft rises.
- Their Hertzian contact model with Coulomb friction and tangential compliance (Maw, Barber and Fawcett) reproduces this with a friction coefficient of 0.4 (0.4 measured for a urethane cover, 0.35 for surlyn, on a grooved and blasted plate under low load; cannon test at 106 mph, plate angle 3 to 33 degrees, agreement near 1 degree).
- The ratio decreases as loft increases even when friction is the same for every club. For metal wood angles (under 20 degrees) lower friction gives a launch closer to the path, the reverse of the smoother-face explanation TrackMan gave. The authors attribute the driver's higher ratio to compliance during the impact.
- Derived cross-check (DERIVED, rolling grip from S9): a ball that rolls off the face leaves with tangential speed beta/(1+beta) times the face's tangential speed, beta = 0.4. With the normal speed (1 + e_A) V cos(SL), e_A = 0.49 and SL = 14.7, the ball leaves 2.9 degrees from the face normal, a launch ratio 1 - 2.9/14.7 = 0.80. That sits just under the published 0.83 to 0.87 driver range, which is close for a model with one assumed restitution and a ball that rolls.

**Does our model capture it? Yes.** k(SL) is 0.83 for the driver and 0.80 down to 0.73 for other clubs as spin loft rises from 12.7 to 25.9 (held at 0.73 above that). The published shares are 0.87 and 0.83 (driver), 0.75 and 0.81 (7 iron), 0.70 and 0.72 (wedge). The 7 iron model value (0.73 at spin loft 27) sits below both published figures and within 0.02 of TrackMan's. One k drives both launch angle and launch direction. PING's data fix the vertical plane alone.

## Topic 5. Attack angle, swing direction, club path, vertical swing plane

**Mechanism (S1, S2, S6).**

- Club path is the horizontal direction of the head at the instant of impact. Swing direction (horizontal swing plane) is the horizontal direction of the plane at the bottom of the arc. Path differs from swing direction because the club meets the ball on the way down or up the arc.
- Tuxen, worked examples: horizontal swing plane 0, attack angle -5, vertical plane 45 degrees gives a path near +5. An 8 or 9 iron with attack angle -5 and vertical plane 57 gives about +3 (S1). Driver with attack +2, plane 45, swing direction 0 gives path -2, and swing direction +2 gives path 0. A 6 iron with attack -5, plane 60, swing direction 0 gives +2.5, and swing direction -2.5 gives path 0 (S2). His summary rule: the driver needs swing direction equal to attack angle for zero path, irons need half of it. Aim the swing plane left when hitting down and right when hitting up. Moving the ball back makes attack angle steeper and path more inside-out.
- The formula: path = swing direction - attack angle times tan(90 - vertical plane). It appears in the repo as a forum formula (Source Log, Anchor 5c). It follows from geometry (DERIVED). For a plane at V degrees and a small angle phi along the arc, attack angle is about -phi sin V and the path offset is about phi cos V. Check against the Tuxen numbers: 5 times tan 45 = 5.0 (published 5); 5 times tan 33 = 3.2 (published 3); 5 times tan 30 = 2.9 (published 2.5, and his rule of thumb for irons says half, so his 6 iron figures are rounded).
- TrackMan's "true impact factors" (S6): a player controls five inputs, swing plane, swing direction, club speed, face angle and 3D low point. Attack angle and path are combinations. 3D low point sets attack angle and strike location, and for shots off the turf the low point must fall target-side of the ball.
- Path and attack angle change about 1 degree during the 1/2000 s of contact (S1). TrackMan reports them pre-impact at maximum compression (S6, Club Data Definitions).
- Tuxen (S1, 2009): every PGA and LPGA pro had iron attack angles between -6 and -2, and Tour club path ranges from about -6 to +6 (his examples are driver swings).

**Magnitude in the model (COMPUTED, PGA driver preset, dynamic loft fixed, face 0, swing direction 0, plane 49).**

| Attack angle | Path | Launch direction | Spin axis | Side at landing |
|---|---|---|---|---|
| +2 | -1.74 | -0.30 | +10.1 | +17.7 yd |
| -0.9 | +0.78 | +0.13 | -3.6 | -7.3 yd |
| -5 | +4.35 | +0.74 | -14.4 | -31.8 yd |

So steepening the driver from +2 to -5 with swing direction and face held moves the landing point about 49 yd. Lowering attack angle at fixed dynamic loft also raises spin loft from 10.8 to 18.2 (COMPUTED).

**Source quality.** Primary (Tuxen worked examples), DERIVED geometry.

**Does our model capture it? Partly.** swing_path implements the relation and the lab has a hold-swing-direction toggle. The path and attack sliders are otherwise independent, so a student who changes attack angle alone does not see path move.

## Topic 6. Lie angle at impact (toe up and toe down)

**Mechanism (DERIVED).** A change of lie is a rotation of the head about the target line. For a face of loft L, a lie change of delta changes the face angle by atan(tan L times sin delta), about delta tan L, and changes dynamic loft by under 0.03 degrees per degree of lie (COMPUTED, 2 degrees of lie at lofts 10.5 to 58 gave a loft change under 0.06). An upright lie (toe down, heel dug in) closes the face. A flat lie (toe up) opens it.

| Loft | Face angle change per degree of lie |
|---|---|
| 10.5 (driver) | 0.19 |
| 20 | 0.36 |
| 34 (7 iron) | 0.67 |
| 46 (PW) | 1.04 |
| 58 (lob wedge) | 1.60 |

**Published support.**

- S17 (retailer article, secondary): too upright sends the ball left, higher lofts amplify the face deviation, wedges are the most sensitive and drivers the least, and a 2 degree lie error moves a shot 8 to 10 yd at typical iron distances. The direction and the ordering by club match the derivation. The size does not match without extra effects: a 2 degree error at a 7 iron is a 1.35 degree face change (DERIVED). At about 0.75 launch share that is 1.0 degree of start direction (2.6 yd at 150), plus face-to-path of -1.35 giving a spin axis near -2.7 by the 2 times rule (S2) and about 2.8 yd at 0.7 percent per degree, together about 5 yd. The 8 to 10 yd claim would need extra effects such as a strike shifted toward the heel. The gap is open.
- Search results describe TrackMan's dynamic lie parameter (the shaft angle to the horizon at impact) as related to launch direction and turf interaction. The TrackMan support page was blocked.
- Search results also attribute to Wishon a one-to-one relation between lie and face and a figure of 4 yd per degree at 150 yd (SNIPPET, unverified, not used). His GolfWRX articles were blocked.

**Effect on spin axis.** The face angle change alters face-to-path with the path unchanged, so the axis moves by 2 to 4 times the face change (S2).

**Does our model capture it? No.** There is no lie input. A student can move face angle and nothing that ties it to lie.

## Topic 7. Impact location, gear effect, bulge and roll, smash loss

**Mechanism.**

- A strike off the CoG rotates the head. For a driver the CoG sits about 25 to 50 mm behind the face (S6), so the rotation moves the face sideways or up and down across the ball. Static friction grips the ball and turns it the opposite way, like meshing gears (S9, S11, S2). For an iron the CoG is close to the face, the rotation makes the face fall away from the ball, and there is little gear spin (S11).
- S9 shows the gear effect arises from static friction when both surfaces accelerate parallel to each other, and that it changes spin and rebound angle by different amounts on the two sides of the impact angle. Penner's analysis assumed a rolling ball. S9 gives the equations in an appendix.

**Numbers (Tuxen 2009, S2, RAW; typical MOI and CoG assumed by TrackMan).**

| Club | Strike | Spin axis | Offline at carry |
|---|---|---|---|
| Driver | 1 dimple (0.14 in) toward heel, face 0, path 0 | +6 deg | 10 yd right at 250 |
| Driver | 0.5 in toward heel | +20 deg | 35 yd right at 250 |
| 6 iron | 1 dimple toward toe | -2 deg | 2.5 yd left at 170 |
| 6 iron | 0.5 in toward toe | -7 deg | 8 yd left at 170 |

- Gear effect sidespin is about the same in rpm across the set for the same offset. 500 rpm of sidespin tilts the axis 11 degrees for a driver at 2500 rpm and 2.8 degrees for a wedge at 10000 rpm (S2). One dimple off center equals about 1 degree of face-to-path for a 6 iron and 1.5 degrees for a driver.
- Tutelman's model (S11, secondary): horizontal gear spin s = 58,830 Vb C x / Ih rpm, with ball speed Vb in mph, CoG depth C and offset x in inches and head MOI Ih in g cm squared, simplified to s = 16.4 Vb x for typical drivers. Vertical gear spin is s = 25 Vb y. He says vertical gear effect is 1.5 to 2 times horizontal for the same miss and can reach 1500 to 3000 rpm at extreme face heights. For a 150 mph ball, a hit 0.6 in above center gains 8 yd of carry and loses 6 degrees of descent angle in his model.
- Bulge and roll (S6, TrackMan): on a standard driver a 10 mm toe impact makes the face 2 degrees more open at the impact point, and a 10 mm low impact makes dynamic loft 2 degrees lower. That implies a radius near 286 mm, about 11 in (DERIVED, 10 mm over 2 degrees). Tuxen (S2) says bulge closes the face on a heel strike, starts the ball left and tilts the D-plane toward a draw, which offsets the gear-effect fade. Tutelman's model puts the best face roll radius near 8 in (secondary).
- Robot test (S15, secondary, 95 mph, 0 degree attack): center 222 yd, 11.4 deg, 2710 rpm. High toe: carry 5.5 yd shorter, launch up about 2.5 degrees, spin down under 300 rpm. Low heel: 203 yd, 8.95 deg, 3310 rpm.
- Smash loss: TrackMan (S4) 92 mph off center gave 129 mph ball speed and 196 yd, while 88 mph at center gave 132 mph and 204 yd. Tuxen (S1) says a half-thin hit is the gap between 1.48 and 1.45.
- Effective mass (S10, RAW): 1/Me = 1/M + b squared over Icm for an impact b from the CoG, apparent restitution e_A = (e Me - m)/(Me + m), ball speed = (1 + e_A) V for a ball at rest. Moving off center lowers Me and e_A. The paper's head properties for a driver were not read, so no number is computed.
- Iron toe strikes open the face 1 to 2 degrees during the collision (S6).

**Does our model capture it? No.** Strike location is not an input. spin_trim is a preset scalar that stands for the group's typical strike (launch.py).

## Topic 8. Center-face versus CoG path and attack angle offsets

- TrackMan measures club speed, attack angle and path at the geometric center of the head, within about 6 mm of the CoG (S6). The CoG of a driver sits 25 to 50 mm behind the face.
- The center-face path of a driver is about 3 degrees more outside-in than the CoG path, and center-face attack angle is about 1 degree higher. Non-drivers differ far less. Optical launch monitors read at the face center (S6).
- Face angle and dynamic loft are read at the impact point, not the face center. Timing is maximum compression using pre-impact data. That shifts the numbers under 0.05 mph and 0.4 degree against first touch.
- Collision changes the club after impact starts. For a driver with 10 to 15 degrees of spin loft the attack angle is 4 to 6 degrees steeper at separation than at first touch, and the toe strike on an iron opens the face 1 to 2 degrees (S6).

**Does our model capture it? A labeling issue.** The sliders should be labeled as TrackMan references (CoG for speed, path and attack angle, impact point for face and loft). A student comparing with an optical monitor reads about 1 degree more attack angle and 3 degrees more outside-in path for a driver.

## Topic 9. Spin loft, smash factor, spin rate, oblique impact models

**TrackMan statements (S6, S2, S4).**

- Higher spin loft gives higher spin rate and lower smash factor. Tuxen (2009): one degree of driver loft, all else equal, changes spin about 230 rpm and launch about 0.8 degree, which is about 5 yd for a 100 mph driver swing (S1). S4 says spin comes from spin loft and club speed, then impact position and friction. Hitting down does not by itself raise spin, and delofting can leave spin loft unchanged.
- Face-to-path enters spin loft as the 3D angle (Topic 3). S6 (True impact factors) says face angle affects spin rate in both the vertical and horizontal parts.
- S6 Optimizer standard assumptions: driver at 94 mph, attack 0, dynamic loft 15.6, spin loft 15.6, launch 13.6, spin 2772. 6 iron at 80 mph: dynamic loft 22.4, spin loft 25.5, launch 16.9, spin 5956. PW at 72 mph: dynamic loft 36.7, spin loft 40.6, launch 26.7, spin 8408. Published spin loft for the Tours: PGA driver 14.7, 6 iron 24.3, LPGA driver 15.0, 6 iron 25.9 (already in the log).

**Oblique impact theory.**

- S9 shows the ball grips or rolls on the face when the angle of incidence is small. S7 uses Hertzian contact with tangential compliance and Coulomb friction. The 2018 Cross and Dewhurst paper (abstract via URI digital commons, RAW) says the ball grips the face instead of rolling, that outgoing spin is larger, as a rule, than earlier rolling models estimated, and that it varies from ball to ball with tangential restitution.
- Smash from normal collision (DERIVED): ball speed is about (1 + e_A) V cos(SL) plus a small tangential part. Dividing the four published smash values by cos of their published spin loft gives 1.54 (PGA driver), 1.525 (PGA 6 iron), 1.54 (LPGA driver), 1.567 (LPGA 6 iron). Constant within 3 percent. At spin loft 40 the same law gives 1.18, and the fitted quadratic in launch.py gives 1.222 (COMPUTED), with the published PW Tour smash at 1.24 and a published PW spin loft of 40.6 for the Optimizer (not for the Tour row). The cos law under-predicts at high loft, since restitution rises as the normal speed falls (not sourced, physical expectation).
- Caldwell and McPhee 2024 (SNIPPET): for drivers the best impact model matched ball speed to 1 percent and launch angle and backspin to under 10 percent, with 30 to 50 percent errors in sidespin and horizontal launch angle. If true, that limits any first-principles model of the horizontal quantities.

**Does our model capture it? Yes for smash and spin.** smash_of is a quadratic in spin loft (1.49 cap, 1.222 at 40), spin is a power law in ball speed and spin loft (driver 1.335 v SL^1.041, irons 0.779 v SL^1.304, woods 0.879 times the iron law). Checks (COMPUTED): the model's driver spin change per degree of spin loft near 15 degrees is about 215 rpm against Tuxen's 230, and its launch change per degree of dynamic loft is 0.83 against Tuxen's 0.8. The drop of smash from spin loft 25 to 30 is 0.05.

## Topic 10. Aerodynamics, spin decay, curvature per degree of axis

**Coefficients (S18, carried from the log; not re-read).** Nathan's fit: CD = 0.1325 + 0.2087 S above about 81 mph, CL = 0.2294 S^0.4. Bearman and Harvey (via Pallis and Mehta): CL from 0.08 to 0.25 with S, CD from 0.27 to 0.32 above S 0.1, and no dependence on Reynolds number between 126,000 and 238,000. Crabill CFD: CD 0.247 static and 0.256 spinning at S 0.15 near Re 150,000. Shipped model (COMPUTED, Re 1.6e5): CD 0.258 and CL 0.224 at S 0.15, and CL 0.393 at S 0.45. The three published characterizations disagree with each other by up to 70 percent in CD and a factor of two in CL, as the log records.

**Spin decay.** Smits and Smith law with 2.0e-5 in SI (log). TrackMan says spin falls about 4 percent per second (quoted by S12 from the October 2010 newsletter, not read), and S12's own drive model uses 3.3 percent, both leaving 78 to 82 percent after 6 s. The model (COMPUTED) leaves 77.6 percent of a driver's spin after 7.05 s, 85.2 percent for a 7 iron after 6.38 s and 88.1 percent for a PW after 5.44 s.

**Curvature per degree of spin axis.**

- TrackMan Spin Axis page (S6): optimized 150 yd shot, 2 deg gives 2.2 yd and 10 deg gives 11 yd. Optimized 200 yd shot, 2 deg gives 3 yd and 10 deg gives 15 yd. That is 0.73 to 0.75 percent of carry per degree. The parameter sheet (S5) states 0.7 percent per degree and works 5 degrees at 200 yd as 7 yd. S4 shows -5 deg as 3.5 yd left and +10 deg as 14 yd right (chart values, carry not stated in the text).
- Model (COMPUTED, start direction 0, axis 2 and 10 degrees): 0.76 percent of carry per degree for a driver (150 mph, 12 deg, 2800 rpm), 1.07 for a 6 iron (130 mph, 14 deg, 6204 rpm), 0.79 for a PW (104 mph, 23.7 deg, 9316 rpm). The 6 iron figure is consistent with TrackMan's worked 6 iron example (2 degrees of face-to-path gives 8 yd at 183 yd carry): the model's axis for that case is near 4 degrees, and 4 times 1.07 percent times 183 yd is 7.8 yd.

**Does a tilted axis reduce carry and height?** Lift splits into cos(axis) upward and sin(axis) sideways (DERIVED). Model (COMPUTED, 171 mph, 10.4 deg, 2545 rpm): axis 0, 10, 20, 30 gives carry 283.7, 281.3, 273.9, 261.7 yd, height 35.2, 34.4, 32.0, 28.5 yd, landing angle 39.5, 38.9, 37.1, 34.2. No measured carry against axis dataset was found. TrackMan's statements on it are qualitative (S3, S1).

**Does lower spin reduce curvature?** Yes at a fixed axis (COMPUTED, same launch, axis 10): 2000 rpm curves 18.4 yd, 2545 rpm 22.2, 3500 rpm 27.4, 5000 rpm 31.8. Real shots also change the axis itself, since axis is FTP over spin loft (Topic 3).

**Does our model capture it? Yes.** The model holds the axis fixed in space, tilts the lift vector by the axis, and it declares the second-order lift overstatement beyond 45 degrees of axis.

## Topic 11. Landing, bounce and roll

**TrackMan (S4, fundamental 10).** Run depends on landing ball speed, landing angle and landing spin. Landing speed varies little across full swing shots, so landing angle and spin are the controls. S3 links draw to a lower landing angle and about 20 yd more run.

**Penner (abstract from a search result, SNIPPET; body blocked).** The run of a golf ball on turf is modeled with launch speed, impact angle, backspin and green firmness. For drives the impact angle dominates the run, and for high-lofted irons with enough backspin the ball on a firm green may bounce forward before running back.

**S13 (Bristol and R&A, RAW).**

- 1,023 bounces from 1.9 to 56 m/s, angles 16 to 89 degrees, spin -3880 to 16200 rpm, artificial and natural tee turf. Marker for a driver tee shot: 93.6 ft/s (63.8 mph), 37.3 degrees, 34.9 rev/s (2094 rpm).
- Rigid bounce with Coulomb friction, best fit: restitution 0.544 on artificial turf and 0.260 on the natural tee, friction coefficient 0.997 and 0.998. The Penner and constant-angle variants gave restitution 0.147 to 0.448 and friction 0.85 to 1.0. A constant effective contact angle (12.9 degrees artificial, 18.4 natural) fit better than Penner's angle formula. A piecewise-affine fit had about one fifth the error of the rigid and Penner models. Balls that reach rolling tend to lift off slipping after spin reversal. The authors conclude a simple physics-based bounce model is still missing.
- S13's introduction credits Haake with the largest public bounce dataset (more than 700 measurements at several courses), where a two-layer spring and damper model fit best. Haake's paper was not read.

**Hooks and draws roll more than slices and fades.** The mechanism is landing angle and landing spin, which come from dynamic loft and spin (Topic 1). S3: landing 28.8 (draw) against 42.9 (fade), hook 19.4 against slice 45.3, run about 20 yd apart on the draw and fade. No source found gives the run separately as a function of axis tilt.

**Model check (COMPUTED).** PGA driver lands at 63.5 mph, 39.5 degrees and 1975 rpm, against the S13 driver marker of 63.8 mph, 37.3 degrees and 2094 rpm. Landing speed for a 7 iron and PW is 54.2 and 54.6 mph.

**Does our model capture it? Partly.** roll() is one fitted formula (k times landing speed times cos(land angle)^4.34 times (2500 / landing spin)^0.559, capped at 0.359 times carry) trained on 60 driver rows of TrackMan's 2010 chart. It responds to landing angle and spin, so it will give a draw more run once dynamic loft differs. It has no sidespin or curving-ball term and irons and wedges are extrapolation.

## Topic 12. Other caveats for a teaching tool

1. **Higher lofts curve less per degree of face-to-path.** Tuxen (S2): driver axis is 4 times FTP, 6 iron 2 times. The model's factor falls from 4.5 to 2.0 to 1.35 from driver to 7 iron to wedge (COMPUTED). Captured.
2. **Hitting down does not by itself add spin.** S4 says so, and S16 adds that golfers who hit down hard often reduce loft at the same time. Model: at fixed dynamic loft, steepening attack angle raises spin loft and spin, because dynamic loft is an independent slider. The tool should say the slider holds dynamic loft, or offer a "hold spin loft" option. Captured with that caveat.
3. **Curvature is close to a constant share of carry** (0.7 to 0.75 percent per degree, S5 and S6). Model within 0.1 point for driver and wedge, high for mid irons (1.07). Captured.
4. **Face angle rule.** Sheet S5: with face angle about half the path the ball tends to fade or draw back onto the line. Model (COMPUTED, PGA 7 iron, path 4, face 2): lands 0.4 yd right of target. PGA driver, path 4, face 2: 8.7 yd left, and it needs face near 0.6 of path. Reasonable.
5. **Straight-shot windows.** Tuxen (S2): start within 1 degree and axis within 2 degrees counts as straight. Center strike with path and face within plus or minus 1 degree guarantees it for a 6 iron, plus or minus 0.5 for a driver.
6. **Wind, altitude, temperature are out of scope.** TrackMan says wind does not change the spin axis value (S6). No air density or temperature figure was read.
7. **Path and face angle are TrackMan conventions** (Topic 8). Tuxen says these two must be measured within 1 degree to be actionable, and a video cannot measure them (S1).
8. **Speed and curvature.** The per-degree share is 0.76 percent for a 150 mph driver ball and 0.79 for a 104 mph wedge ball (COMPUTED), so ball speed alone moves it little. The 6 iron at 1.07 is the outlier and no run isolated speed.


## Topic 13. Irons and wedges: attack angle, dynamic loft and compression

**Owner's claim.** Hitting up on an iron or wedge makes it fly shorter, because the strike loses compression, and flipping or scooping loses distance. Verdict on the evidence read: supported for 7 irons at head speeds of about 85 mph and above (carry falls 1.7 to 2.7 yd per degree of attack angle), near flat at 70 to 80 mph, and reversed at 60 mph, where +2 degrees beats -6. At 60 to 80 mph the best carry sits at -2 to -4 degrees. The cause is the loft that comes with the attack angle, and the upward motion alone does not explain it.

### 13.1 How dynamic loft moves with attack angle

**Arc geometry (DERIVED, floor of 1.0).**

- The club travels along an arc. Moving the low point behind the ball, or tilting the swing plane, changes the direction the head moves at impact. If the golfer's hands and wrists keep the same relation between shaft and head, the whole club turns with the velocity vector. Attack angle and face orientation rotate by the same amount, so dynamic loft rises one degree per degree of attack angle and spin loft stays put.
- TrackMan writes the same relation as a rule of thumb: dynamic loft equals static loft plus attack angle, adjusted for the bent shaft, with a typical adjustment of +2 degrees for a driver (S5, RAW). The adjustment for irons is the forward shaft lean, and it lowers loft. Rotating the whole club about the axis across the target line by a lean of L degrees changes loft by L degrees (DERIVED), so shaft lean also trades one for one.
- TrackMan states the same coupling in words: dynamic loft depends on attack angle, shaft bend, the release, whether the face is open or closed to path, and strike location (S6). S4 adds that hitting more down does not by itself raise spin, and that delofting can leave spin loft unchanged. S6 (Attack Angle) says slower golfers should take care not to hit too far down with irons because it costs distance.
- S16 and S22 make the same point from coaching data: a steeper blow alone does not change spin, and good ball strikers lower dynamic loft without hitting down more. In S22 a 54 degree wedge delivers 41 to 44 degrees of dynamic loft, more than 10 degrees below static loft, for players with the hands ahead of the ball.

**Flip and scoop addition.** A release that opens or adds loft near impact, or hands that finish behind the ball, add loft on top of the arc rotation. This is where the slope rises above 1.0. Two measured pieces of evidence exist.

1. **Foresight 7 iron chart (S20, IMAGE, manufacturer).** At each head speed, moving the attack angle from -6 to +2 raised launch angle about 10 to 12 degrees and, except at 80 mph, raised spin about 900 to 1250 rpm. If dynamic loft rose one for one and no more, spin loft and spin would stay put and launch would rise about 8 degrees. The chart shows more than that.
   - Launch rise from -6 to +2 by head speed: 60 mph 12.3, 70 mph 10.6, 80 mph 9.6, 90 mph 10.7, 100 mph 10.5 degrees.
   - Dynamic loft slope (DERIVED): launch = k times dynamic loft plus (1 - k) times attack angle, so slope = (launch rise - (1 - k) times 8) / (k times 8). With k = 0.73 (the repo's iron value above spin loft 26) this gives 1.73, 1.45, 1.27, 1.46, 1.43 for 60 to 100 mph. With k = 0.80 it gives 1.67, 1.41, 1.25, 1.42, 1.39. The median is about 1.4.
   - Independent check from spin (COMPUTED with the repo's spin law, spin proportional to spin loft to the 1.304): the spin rise at 90 and 100 mph means spin loft grew by about 3.7 and 4.1 degrees, so dynamic loft rose 11.7 and 12.1 degrees for 8 degrees of attack angle, a slope near 1.5. The 80 mph row changed little in spin (5748 to 5915 rpm) and gives about 1.1, and the page itself calls that row an exception.
   - The chart's method is unknown (Sources, S20), so this is a measured trend and not a controlled mechanism.
2. **Suzuki et al. 2021 (S21, RAW, driver off a tee, within-player).** Uphill and downhill fairways changed the attack angle. The players were told to swing in their usual way and given no other instructions.

| Group | Attack up / down | Dynamic loft up / down | Spin loft up / down (DERIVED) | Slope of dynamic loft on attack angle (DERIVED) |
|---|---|---|---|---|
| 42 professionals, 45 m/s head speed | +3.6 / +0.3 | 16.0 / 13.2 | 12.4 / 12.9 | 0.85 |
| 25 amateurs, 40 m/s | +0.6 / -0.7 | 16.2 / 14.6 | 15.6 / 15.3 | 1.23 |

Spin loft stayed within 0.5 degree in both groups, so within a player the coupling ran close to the arc value of 1.0 for a driver off a tee. Amateurs delivered 2.4 to 3.2 degrees more spin loft than professionals in the same condition (15.3 to 15.6 against 12.4 to 12.9), which is the flip and scoop effect between players. The paper reports launch angle up 2.8 degrees for professionals and 1.4 for amateurs across the two conditions.

**Between-player evidence (S6, TrackMan Combine driver averages, RAW).** Male amateurs by handicap, attack angle / dynamic loft / spin loft / smash: scratch -0.9 / 13.0 / 14.8 / 1.49, 5 handicap -1.1 / 13.2 / 15.8 / 1.45, 10 handicap -1.2 / 14.1 / 17.3 / 1.45, average golfer -1.8 / 15.1 / 18.3 / 1.44, bogey -2.1 / 14.3 / 18.2 / 1.43. Female amateurs, scratch -0.9 / 14.8 / 17.1 / 1.46 through 15 handicap -2.3 / 16.5 / 20.1 / 1.41. Weaker players hit down more and deliver more loft, so their spin loft is 3.5 degrees higher (scratch 14.8, average 18.3) and their smash lower by 0.05. Tour iron rows for one club exist for one pair (6 iron, Source Log Anchors 1 and 2 and S6): PGA attack -3.7, dynamic loft 20.2, spin loft 24.3; LPGA attack -2.3, dynamic loft 23.6, spin loft 25.9. The LPGA clubs carry more static loft, so that pair does not isolate a slope.

**Not found.** GolfTEC SwingTRU pages (the Canadian and PGA.com summaries) carry no shaft lean numbers by handicap. No Titleist or PING fitting note with degrees of loft per degree of attack angle turned up. Search results mention 4 to 8 degrees of shaft lean for a 7 iron and 24 degrees of dynamic loft from 32 degrees of static (SNIPPET, coach sites, not used). No sports-engineering study of ball position and launch conditions with dynamic loft was found. The PMC study of ball position (Biomechanical Effects of Ball Position on Address Position Variables) measures address posture and attack angle for 11 professionals and reports that moving the ball toward the target reduced the downward attack angle, with no dynamic loft (PMC6243633, RAW, not used for a coefficient).

### 13.2 Compression, smash and ball speed for irons

- TrackMan (S6, Spin Loft and Smash Factor pages): higher spin loft gives a lower smash factor, and some coaches call spin loft compression. A PW should have a smash near 1.25 and a 6 iron near 1.39 to 1.41 on Tour. Tour PGA rows in the log run from 1.46 (3 iron) to 1.24 (PW).
- Physics (DERIVED, Topic 9): smash is close to 1.54 times cos(spin loft) for the four published Tour points, so a rise in spin loft from 27.3 to 29.7 (the model's 6 degree case below at slope 1.4) costs about 0.02 of smash, about 2 mph of ball speed on a 92 mph swing.
- Andrew Rice (S22, secondary, TrackMan case): a student's 7 iron spin loft went from 31.1 to 24.8 degrees, height from 103 ft to 76 ft, and ball speed stayed the same while club speed fell more than 7 mph. That is a higher smash from less spin loft, one case.
- Foresight chart (S20): the ball speed column is one value per head speed, so the chart holds smash fixed across attack angles and says nothing about smash by attack angle. Do not read a smash trend from it.
- Fat and thin strikes: no measured ball speed loss for an iron struck fat or thin was found. TrackMan (S1) says a half-thin driver hit is the difference between 1.48 and 1.45 smash, and S4 shows 92 mph off center giving 129 mph against 132 mph from 88 mph at center. The iron case is open.

### 13.3 Carry: the same iron up and down

**Foresight 7 iron chart (S20, IMAGE).** Carry in yards, with launch, spin and descent for the -6 and +2 columns. Full rows for 60 to 70 mph are in the source.

| Head speed | Attack -6: launch / spin / carry / descent | Attack +2: launch / spin / carry / descent | Carry change |
|---|---|---|---|
| 100 mph | 14.4 / 6343 / 203.5 / 49.6 | 24.9 / 7591 / 181.8 / 56.5 | -21.7 |
| 90 mph | 14.3 / 5884 / 183.4 / 45.7 | 25.0 / 6944 / 169.5 / 54.9 | -13.9 |
| 80 mph | 14.6 / 5748 / 160.3 / 40.8 | 24.2 / 5915 / 156.3 / 51.5 | -4.0 |
| 70 mph | 14.9 / 5091 / 131.6 / 35.1 | 25.5 / 6026 / 129.8 / 48.8 | -1.8 |
| 60 mph | 14.1 / 4381 / 102.2 / 27.4 | 26.4 / 5305 / 107.7 / 44.9 | +5.5 |

Carry by attack angle at 90 mph: 183.4, 182.6, 180.0, 173.7, 169.5 yd for -6, -4, -2, 0, +2. At 100 mph: 203.5, 200.1, 195.4, 188.4, 181.8. At 80 mph: 160.3, 160.8, 161.0, 159.7, 156.3. At 70 mph the peak is 135.5 at -2, and at 60 mph 110.1 at -2. So the drop in carry with a rise in attack angle is 1.7 yd per degree at 90 mph and 2.7 yd per degree at 100 mph, near zero at 70 to 80 mph, and reversed at 60 mph. Foresight's own reading (S20): faster swings gain from more negative attack angles, slower swings from neutral or small negative ones, and slower swings need the higher descent angle (45 to 50 degrees) that a neutral or positive attack angle provides.

**Other examples.** A blog result quotes Tuxen at 90 mph with +5 attack giving 16 degrees of launch and 2200 rpm against -5 giving 10 degrees and 3100 rpm, about 30 yd farther for the upward strike (SNIPPET, driver context, not used). That direction, higher attack angle with lower spin, is the driver relation and opposite to the iron chart, which fits the difference in loft behavior (driver spin loft falls when attack rises, iron spin loft rises when the golfer adds loft).

### 13.4 Recommended MODELED coupling for the lab

**Relation.** For irons, wedges, hybrids and fairway woods played off the ground: `DL = DL_reference + s times (AA - AA_reference)`, with s = 1.4. The reference pair is the preset delivery. A student who drags the attack angle slider moves dynamic loft by 1.4 degrees per degree, and a "hold dynamic loft" toggle reverts to the current independent behavior. Use s = 1.0 for a driver off a tee (S21 gives 0.85 to 1.23). Label s as MODELED, with a range of 1.0 (pure arc) to 1.5.

**Support for the number.**

1. **Floor of 1.0:** TrackMan's rule that dynamic loft equals static loft plus attack angle plus a shaft adjustment (S5), the arc geometry above, and S21's within-player driver slopes of 0.85 and 1.23.
2. **Flip addition of about 0.4:** the Foresight 7 iron chart (S20), slope 1.4 from launch (range 1.25 to 1.7 across head speeds) and about 1.5 from spin at 90 and 100 mph. S21's amateur and professional spin loft gap of 2.4 to 3.2 degrees supports a flip effect between players. No source measures the coefficient for wedges, hybrids or fairway woods, so s = 1.4 there is an extension of the iron result.
3. **Check on the carry trend:** the model at s = 1.4 gives a carry change of -1.9 yd per degree of attack angle for the PGA 7 iron at 92 mph (175.9 to 159.0 yd from -3 to +6 degrees), which matches the chart's -1.7 yd per degree at 90 mph. The amateur 7 iron at 78 mph gives -1.1 yd per degree against about -0.5 in the chart at 80 mph.

**Top two sources to cite.** (1) Foresight Sports, 7 Iron Angle of Attack Chart, January 2025 (S20). (2) TrackMan, data parameter sheet Release 3.1 rule for dynamic loft (S5), with Suzuki et al. 2021 (S21) as the peer-reviewed cross-check.

**What the model then predicts (COMPUTED, shipped launch and flight models, spin trim from the preset, straight shots, change in attack angle from the preset value).** Carry / total in yards, with launch, spin and smash at +3 degrees.

| Club and preset | Slope | -3 deg | 0 (preset) | +3 deg | +6 deg | Launch / spin / smash at +3 |
|---|---|---|---|---|---|---|
| 7 iron, PGA, 92 mph | 0 (today) | 163.9 / 170.7 | 171.7 / 178.5 | 180.1 / 187.3 | 189.5 / 197.4 | 17.1 / 6248 / 1.390 |
| | 1.0 | 172.4 / 180.7 | 171.7 / 178.5 | 169.8 / 175.6 | 166.9 / 172.0 | 19.1 / 7124 / 1.361 |
| | 1.4 | 175.9 / 185.1 | 171.7 / 178.5 | 165.9 / 171.3 | 159.0 / 163.4 | 20.0 / 7470 / 1.349 |
| 7 iron, amateur, 78 mph | 0 (today) | 134.4 / 143.8 | 141.2 / 150.4 | 148.1 / 157.7 | 155.4 / 165.4 | 18.8 / 5945 / 1.372 |
| | 1.4 | 142.7 / 155.5 | 141.2 / 150.4 | 137.7 / 144.7 | 133.0 / 138.4 | 22.0 / 6998 / 1.330 |
| PW, PGA, 84 mph | 0 (today) | 125.1 / 131.0 | 130.5 / 135.9 | 135.6 / 140.6 | 140.7 / 145.6 | 24.4 / 8613 / 1.274 |
| | 1.4 | 133.9 / 140.6 | 130.5 / 135.9 | 126.3 / 130.7 | 121.6 / 125.2 | 27.6 / 9586 / 1.225 |
| 5 wood, PGA, 106 mph | 0 (today) | 228.2 / 239.1 | 241.7 / 256.1 | 253.9 / 275.6 | 256.3 / 295.8 | 10.5 / 3319 / 1.488 |
| | 1.4 | 240.0 / 265.5 | 241.7 / 256.1 | 236.1 / 245.4 | 226.4 / 233.2 | 13.5 / 4731 / 1.456 |

**Qualitative behavior.**

- Today's sliders (slope 0) say that hitting up on any club at fixed dynamic loft raises carry, cuts spin by about 290 rpm per degree for a 7 iron and raises smash. That contradicts the Foresight chart at 90 mph and above and the owner's claim, and the 5 wood total climbs 40 yd from +6 degrees of attack because spin falls to 2300 rpm.
- At slope 1.0 spin loft, spin and smash stay fixed, launch rises 1 degree per degree, and carry changes by about -0.6 yd per degree for the 7 iron. Hitting up raises launch and descent angle and shortens the shot by a few yards through height alone.
- At slope 1.4 each degree of upward attack adds 0.4 degree of spin loft, about 115 rpm and 0.004 of smash loss for the PGA 7 iron, and carry falls about 1.9 yd per degree. Hitting down by 3 degrees gains 4 yd of carry and 6.6 yd of total for the PGA 7 iron and lowers descent angle by 3.6 degrees.
- For a slow player the carry curve peaks near a small negative attack angle (amateur 7 iron: 142.7 at -3, 141.2 at 0, 137.7 at +3), which matches the chart's 70 to 80 mph rows, and total distance still favors the downward blow.
- The flip is a change to dynamic loft alone. The lab should keep the slider for dynamic loft, and show spin loft as the compression readout, since TrackMan calls spin loft compression (S6, S22).

**Limits.** One iron (7 iron), one manufacturer chart with an unknown method, and the model's launch and spin fits stop at spin loft 26 (k clamps at 0.73 and the axis scale at 26.9), while the chart's 7 iron delivers spin loft 28 to 33 by this inference. The inferred spin loft runs above the model's Tour 7 iron (27.3), so the chart may have used a higher-lofted club than the Tour preset, and the model's own carry for the chart rows runs 9 to 10 percent low and its spin up to 27 percent high (COMPUTED, 7 iron preset at chart launch angles). The slope, not the absolute carry, is the transferable result.

---

## Model check runs (COMPUTED)

Repeat with `analysis/004-ball-flight-laws`: `presets.preset(club, player)`, then `launch.deliver(club_speed, attack, path, face, dyn_loft, club, spin_trim=trim)` then `flight.simulate(ball_speed, launch, launch_dir, spin, axis)` and `flight.roll`. Shipped parameters throughout.

| Inputs | Result |
|---|---|
| PGA driver, straight | SL 13.59, launch 10.40, spin 2545, carry 282.1, total 312.9, landing 39.3 |
| PGA driver, path -4 face -4 (pull) | HLA -4.00, carry 281.4, side -19.7, total 312.2 |
| PGA driver, path +4 face +4 (push) | HLA +4.00, carry 281.4, side +19.7, total 312.2 |
| PGA driver, path +4 face 0 (draw) | SL 14.15, spin 2648, axis -17.75, curve -38.4, carry 273.6, total 305.9 |
| PGA driver, path -4 face 0 (fade) | same magnitudes, axis +17.75, carry 273.6, total 305.9 |
| PGA 7 iron, path +4 face 0 (draw) | axis -7.90, curve -14.4, carry 170.4, total 177.3 |
| Amateur driver, path +4 face 0 (draw) | axis -13.97, curve -22.9, carry 208.4, total 234.6 |

**Hypothetical coupling run (COMPUTED with an assumed rule, not a published one).** The run sets dynamic loft to the preset value plus kappa times face-to-path, with path and face split about zero (FTP +4 for the fade, -4 for the draw). kappa is a stand-in for the Topic 1 coupling, 0.3 as a mid value and 0.58 as the geometric ceiling for a 60 degree lie.

| Case | kappa | Draw carry / total | Fade carry / total | Draw minus fade: carry / total | Draw spin vs fade | Draw landing vs fade |
|---|---|---|---|---|---|---|
| PGA driver | 0 | 272.2 / 304.6 | 272.2 / 304.6 | 0 / 0 | 2648 vs 2648 | 38.0 vs 38.0 |
| PGA driver | 0.3 | 269.7 / 311.8 | 272.6 / 297.8 | -3.0 / +14.0 | 2440 vs 2856 | 34.3 vs 41.2 |
| PGA driver | 0.58 | 264.1 / 318.9 | 271.5 / 291.8 | -7.4 / +27.1 | 2241 vs 3048 | 30.3 vs 43.7 |
| PGA 7 iron | 0.3 | 173.5 / 181.1 | 166.4 / 172.8 | +7.1 / +8.3 | 6861 vs 7546 | 48.0 vs 49.5 |
| PGA 7 iron | 0.58 | 176.8 / 185.1 | 163.2 / 169.2 | +13.6 / +15.9 | 6538 vs 7861 | 47.2 vs 50.1 |
| Amateur driver | 0.3 | 206.7 / 239.1 | 207.2 / 228.7 | -0.4 / +10.5 | 3145 vs 3570 | 34.1 vs 39.7 |
| Amateur driver | 0.58 | 204.6 / 244.3 | 205.9 / 224.0 | -1.3 / +20.3 | 2944 vs 3765 | 31.0 vs 41.8 |

For comparison S3's single-player example has a 4.5 degree dynamic loft gap, a 1125 rpm spin gap, a 14 degree landing gap and about 20 yd more run for the draw. The kappa 0.58 driver row (loft gap 4.6 degrees, spin gap 807 rpm, landing gap 13.4 degrees) matches the loft and landing gaps and overshoots the run gap (35 yd against about 20). The kappa 0.3 row gives a 2.4 degree loft gap, a 416 rpm spin gap, a 6.9 degree landing gap and 17 yd of run difference, which undershoots the loft, spin and landing gaps and lands near the run gap. This is a plausibility check, not a fit. S3 does not report its face-to-path values.

---

## Prioritized model changes

Effects are from the runs above and are model output. Publish each as MODELED until a coefficient is measured.

**1. Add a face-to-path to dynamic loft coupling.** *Governing relation:* DL_eff = DL_input + kappa times (face - path), kappa between 0 (yaw) and cot(lie), about 0.5 to 0.6 (roll about the shaft), so a closed face to path removes loft and an open face adds it. *Cite:* TrackMan Dynamic Loft page for direction (S6), S3 for the contrast it should reproduce, the geometry in Topic 1 for the ceiling, S14 for the club-maker statement of the same physics. *Visible effect:* the largest effect on distance of any change. At kappa 0.3, FTP plus or minus 4: PGA driver draw goes 14 yd farther in total and 3 yd shorter in carry than the fade, and the 7 iron draw goes 7 yd farther in carry and 8 yd in total. At 0.58: 27 yd total for the driver, 16 for the 7 iron. This is the one change here that makes draw and fade distances differ, and for the tool's headline numbers (draw versus fade) it is the one to build. For pure pull versus push at FTP 0 it does nothing, and the honest statement is that the physics gives equal carry (Topic 1).

**2. Couple attack angle to path through swing direction by default.** *Relation:* path = swing direction - attack angle times cot(vertical plane). *Cite:* Tuxen worked examples (S1, S2). *Visible effect:* large on curvature. Steepening a driver from +2 to -5 attack with swing direction and face held moves the ball 49 yd (Topic 5). This is a teaching point Tuxen calls central.

**3. Add an optional strike location control.** *Relations:* gear spin s = 16.4 Vb x rpm (horizontal, driver) and 25 Vb y (vertical) with Vb in mph, offsets in inches (S11); axis adds atan(side spin / backspin); bulge and roll 2 degrees of face angle or loft per 10 mm (S6); smash loss through effective mass (S10); Tuxen's table as a check (S2: driver 6 degrees axis per dimple, 6 iron 2). *Visible effect:* large for off-center shots, none for center shots. It replaces spin_trim's stand-in role.

**4. Show the reference convention.** TrackMan CoG for speed, path and attack angle, impact point for face and loft. A student reading an optical monitor sees +1 degree attack and 3 degrees more outside-in driver path (S6). No number changes.

**5. Check the start-direction weight.** k for a 7 iron is 0.73 against 0.75 (TrackMan) and 0.81 (PING). A change to 0.78 moves start direction 0.2 degree at FTP 4 (0.6 yd at 170). Low priority. *Cite:* S7.

**6. Keep the spin axis scale, and add a note on the extrapolation edges.** The scale c(SL) is calibrated for spin loft 12.4 to 26.9, and at wedge spin loft it holds flat at the 26.9 value. Tuxen's 4 and 2 times rules fit the D-plane tilt with c close to 1, so the scale (4.5 and 2.0) sits within 15 percent of the rules. No visible change proposed.

**7. Extend the roll validation to irons and wedges.** Roll is fitted to driver rows. Use S13's landing conditions and the S3 draw and fade landing angles (28.8 and 42.9 degrees, about 20 yd of run difference) as checks after change 1. The kappa 0.3 driver case gives 17 yd of run difference and 0.58 gives 35.

**8. Leave the aerodynamics.** The shipped coefficients sit between the published sets at S 0.15 and reproduce the driver landing marker (Topic 11) and the spin decay (Topic 10). The three published sets still disagree above S 0.3 and no source covers wedge spin factors.

**9. Couple dynamic loft to attack angle for irons, wedges, hybrids and fairway woods off the deck.** *Governing relation:* DL = DL_reference + 1.4 times (AA - AA_reference), floor 1.0 from arc geometry, 1.0 for a driver off a tee. *Cite:* Foresight 7 Iron Angle of Attack Chart (S20) and TrackMan's dynamic loft rule (S5), with S21 as cross-check (Topic 13). *Visible effect:* large and it reverses today's answer. A 3 degree rise in attack angle now adds 8 yd of carry to a PGA 7 iron and would cost 6 yd, and a 6 degree rise on a 5 wood adds 15 yd of carry and 40 yd of total now and would cost 15 yd of carry and 23 yd of total. It rates with change 1 for effect on distance and above it for iron and wedge teaching.

**Ranking by effect on the lab's visible numbers.** Change 1 moves draw versus fade distance by up to 27 yd (driver) and changes carry by up to 14 yd (7 iron). Change 9 moves iron carry by 6 to 15 yd per 3 to 6 degrees of attack angle and flips its sign. Change 2 moves curvature by tens of yards whenever a student changes attack angle. Change 3 moves off-center shots by 2.5 to 35 yd offline and several yards of carry. Changes 4 to 8 move nothing or almost nothing.

## Open items for a person with a normal browser

- Tuxen, "TRACKMAN Ball Flight Laws" (Yumpu listing). It would fix the exact composition of face angle and dynamic loft into the face normal and any spin axis formula. S1 and S2 cover the rules of thumb and nothing more.
- Wood, Henrikson, Broadie 2018 (MDPI, Proceedings 2(6):249). The table of launch percent by plane would say whether the horizontal share matches the vertical (S8 gives the 61 to 83 range alone).
- Penner 2003 (Rep. Prog. Phys.) and 2002 (Can. J. Phys.), Jorgensen, Cochran and Stobbs (Internet Archive lending copy), Caldwell and McPhee 2024, the International Journal of Performance Analysis in Sport 2023 impact factor paper, and Lyu et al. for aerodynamic coefficients.
- TrackMan newsletter of October 2010 (source for the 4 percent per second spin decay). The Internet Archive was offline at the last attempt.
- TrackMan support article on dynamic lie, MyGolfSpy's draws versus fades robot test, and the Wishon lie angle articles on GolfWRX (all blocked).
- Foresight's full 7 iron attack angle report (the chart page links to it) for the test method, the club loft and whether a robot or players swung. GolfTEC SwingTRU shaft lean at impact by handicap, if GolfTEC publishes the figures. Any measured ball speed loss for fat and thin iron strikes.
