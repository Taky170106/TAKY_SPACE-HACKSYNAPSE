"""SignGuard AI - project document (paper style, flowing prose).

    python documentation/make_project_document.py

Writes documentation/SignGuard_AI_Project_Document.docx
Figures come from documentation/figures/ (make_diagrams.py).
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).parent
FIG = HERE / "figures"
OUT = HERE / "SignGuard_AI_Project_Document.docx"

TITLE = ("SignGuard AI: Integrity-Guarded Content Delivery for Public-Transport "
         "Digital Signage with Explainable Intrusion Detection")

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Tahoma"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Tahoma")
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.15


def para(text: str, *, size: int = 11, bold: bool = False, italic: bool = False,
         align: str = "just", before: float = 0, after: float = 8, indent: float = 0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.left_indent = Inches(indent)
    p.alignment = {"just": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER,
                   "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    r.font.name = "Tahoma"
    return p


def h1(text: str):
    return para(text, size=13, bold=True, align="left", before=14, after=6)


def figure(name: str, caption: str, width: float = 6.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / name), width=Inches(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(10)
    r = c.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.name = "Tahoma"


def table(headers, rows, widths=None, size: float = 9.0):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "7F7F7F")
        borders.append(el)
    t._tbl.tblPr.append(borders)
    for i, htxt in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.space_before = Pt(2)
        r = p.add_run(htxt)
        r.bold = True
        r.font.size = Pt(size)
        r.font.name = "Tahoma"
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "EDEDED")
        cell._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(2)
            r = p.add_run(str(val))
            r.font.size = Pt(size)
            r.font.name = "Tahoma"
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def code(text: str):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Inches(0.3)
    pf.space_before = Pt(6)
    pf.space_after = Pt(8)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "F4F4F4")
    p._p.get_or_add_pPr().append(shd)
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(9)


# --------------------------------------------------------------------------- #
def front_matter():
    para("School of Computer Science Engineering and Information Systems", size=11, bold=True,
         align="center", after=2)
    para("5Yr Integrated M.Tech (Software Engineering)", size=10.5, align="center", after=2)
    para("ISWE415L : Cyber Security, FALL 2026-2027", size=10.5, align="center", after=20)
    para(TITLE, size=14, bold=True, align="center", after=4)
    para("Course Project Document", size=11, italic=True, align="center", after=24)

    para("TEAM Name :  <TEAM NAME>", size=11, bold=True, align="left", after=14)
    para("Team Member(s) with Reg # and Name :", size=11, bold=True, align="left", after=4)
    para("<NAME1>;<REG NO1>;<MOBILE1>;<EMAIL1>", size=11, align="left", after=2)
    para("<NAME2>;<REG NO2>;<MOBILE2>;<EMAIL2>", size=11, align="left", after=2)
    para("<NAME3>;<REG NO3>;<MOBILE3>;<EMAIL3>", size=11, align="left", after=18)

    para("October 2026", size=11, align="left", after=6)


def abstract():
    h1("Abstract")
    para(
        "Public transport agencies now publish passenger information on networks of electronic destination boards, "
        "and the channels that feed those boards are rarely authenticated. A field technician copies a file onto a "
        "USB stick, a controller synchronises over wireless, or a duty manager corrects a platform number through a "
        "browser panel; in none of these cases is the arriving text checked against anything the transport authority "
        "actually approved. Recent incidents show what that costs. In October 2025 flight-information displays at "
        "four North American airports were defaced, and in the following month e-paper bus-stop panels operated by "
        "the Los Angeles Metro displayed a fabricated emergency warning telling passengers to leave immediately "
        "because of a suicide bomb. The error in every published case was noticed by a person, not by the system."
    )
    para(
        "This document presents SignGuard AI, a gate that sits between content ingress and rendering. Content is "
        "authorised in advance, its SHA-256 digest is written into a hash-linked ledger whose blocks are signed with "
        "Ed25519, and every arriving payload is verified against that record before it can be shown. A mismatch ends "
        "the decision immediately, and no machine-learning component is allowed to reopen it. Around that "
        "deterministic gate we run an isolation forest over a seven-element feature window of five minutes to "
        "quantify the attack context, fuse it with rule signals into a score between 0 and 100, and attach SHAP "
        "attributions to every verdict so that an operator can see why a decision was taken rather than only what it "
        "was. Verdicts are appended to a file-backed audit store that survives restarts, and they are enforced "
        "physically on an ESP8266 signage node through an LCD, a green and red LED pair and a buzzer."
    )
    para(
        "Over four scenarios, namely genuine content, malicious USB replacement, a rogue wireless update and a "
        "default-credential panel attack, the system rendered the genuine update at a risk of 1/100 and blocked the "
        "three attacks at 71, 66 and 62. The automated suite reports 46 of 46 tests passing, the complete explainable "
        "decision costs 21.7 ms of processing, and the audit trail and ledger were re-read successfully after the "
        "service was restarted.",
        after=14,
    )


def introduction():
    h1("1. Introduction")
    para(
        "A modern transport operator runs electronic displays everywhere: platform indicators inside the station, "
        "departure boards in the concourse, and e-paper panels at bus stops. Each of those displays is driven by a "
        "small controller that obtains its picture from one of three convenient channels. A field technician "
        "carries a USB flash drive with the new artwork, a controller synchronises wirelessly with a central server "
        "on a schedule, or a duty manager logs into a browser panel to change a platform number during engineering "
        "work. All three channels were designed for availability and ease of maintenance, and none of them "
        "authenticates the picture. The controller accepts whatever bytes arrive, renders them, and only a human who "
        "happens to notice that the board is wrong discovers that something happened."
    )
    para(
        "The problem is no longer hypothetical. Bristol Airport's departure screens were made to display a ransom "
        "message in an earlier incident, in October 2025 four North American airports had their flight-information "
        "displays defaced by an unknown group, and in November 2025 e-paper bus-stop panels run by the Los Angeles "
        "Metro were made to show a fabricated warning that told passengers to leave the stop immediately because of "
        "a suicide bomb. The message stayed on the panels until the vendor traced the intrusion. What is striking "
        "about all of these incidents is how ordinary the entry point was. National CERT guidance on kiosk and "
        "signage hardening lists the same three items in the same order every time: exposed USB ports, factory "
        "default credentials on management interfaces, and update packages that are never signed. Those are exactly "
        "the settings most installed hardware ships with, because changing them usually breaks the maintenance "
        "routine that the vendor sold along with the display."
    )
    para(
        "Two families of defence already exist and neither one closes this gap. Security of the transport path, "
        "through TLS between the content server and the controller, an authenticated repository, or a VPN across the "
        "operator network, proves that bytes travelled down a protected pipe. It says nothing about the USB stick, "
        "which never traverses that pipe, and it says nothing about whether the file an authenticated operator just "
        "pushed was ever authorised by the content authority. On the other side, intrusion detection systems "
        "classify network traffic and raise alerts for a human to triage. They can say that a host looks unusual; "
        "they cannot say whether the two lines of text about to be shown on a platform indicator are the two lines "
        "the transport authority approved last Tuesday. Between the authority that approved a message and the "
        "passenger reading it there is no integrity check of any kind, and the operational consequence is not "
        "cosmetic. A platform indicator that names the wrong platform sends a carriage in the wrong direction during "
        "an evacuation, and a wrong departure time quietly causes missed connections and a claims process."
    )
    para(
        "We built SignGuard AI to place that missing check immediately before rendering. The design has one "
        "deliberately asymmetric idea at its centre. Authenticity is decided by a deterministic comparison: content "
        "is registered in advance by the transport authority, its digest is stored in a hash-linked ledger whose "
        "blocks are signed with Ed25519, and every arriving payload is hashed and compared against that record. If "
        "the digest does not match, the update is blocked and a safe fallback message is shown, and the decision "
        "engine returns before any model is consulted. Around that gate sits a probabilistic layer that never "
        "decides authenticity but does decide severity. An isolation forest scores a seven-element vector built from "
        "the device's own recent behaviour, rule signals for unauthorised USB, default credentials and rogue "
        "wireless activity are added with frozen weights, and the result is a risk score between 0 and 100 that "
        "decides what happens when the hash does match: render, block, or isolate the update channel."
    )
    para(
        "Three properties distinguish the result from a research prototype. The first is that explanation travels "
        "with the verdict instead of living in a separate report; each decision object carries the ranked SHAP "
        "contributions that produced the model assessment, and they are shown next to the decision on the audit "
        "endpoint and on the dashboard. The second is that the trail survives the process. Authorised content is "
        "held in a ledger that can be re-verified independently through an API call, and operational decisions are "
        "appended to a file-backed SQLite store rather than an in-memory one, so both remain readable after the "
        "service is restarted. The third is that the verdict reaches the physical world. The decision is published "
        "over MQTT to an ESP8266 node driving a 16x2 LCD, a green and red LED pair and a buzzer, so the sign shows "
        "authorised text, a tamper message or a safe fallback even if the management dashboard is closed and even if "
        "the network link that carried the decision has since gone away."
    )
    para(
        "The rest of this document is organised as follows. Section 2 reviews the three strands of published work we "
        "build on, namely provenance through ledgers, unsupervised anomaly detection at the edge, and explainable "
        "AI for intrusion detection, and states the gap each one leaves. Section 3 describes the design, the "
        "architecture and the algorithms, including the pseudo-code of the gate and the fusion rule. Section 4 "
        "explains the data we built and used, because no public corpus of tampered signage content exists, and "
        "describes how the measurements were taken. Section 5 reports the results and analyses two of them in "
        "detail, including a latency artefact that cost us some time to understand. Section 6 concludes."
    )


def related_work():
    h1("2. Related Work")
    para(
        "Work relevant to this project comes from three directions. The first asks how the provenance of data "
        "produced by devices can be made verifiable, the second asks how an unusual observation can be detected "
        "without labelled data, and the third asks how such a detection can be explained to a human. We briefly "
        "review each and then state what none of them does."
    )
    para(
        "On provenance, Dai, Zheng and Zhang named the combination of blockchain with the Internet of Things as "
        "blockchain of things and surveyed how a distributed ledger can replace a trusted intermediary when devices "
        "cannot rely on a central authority [1]. Liu and colleagues narrowed the question to trust management and "
        "reviewed how reputation and ledger-backed attestation are shared between devices, concluding that such "
        "schemes improve tamper evidence but usually assume that the device itself is trustworthy [2]. Khan and "
        "colleagues surveyed blockchain applications across the IoT stack and identified integrity of data in "
        "motion as the dominant use case while noting that verification on the device side remains largely "
        "unimplemented [10]. He and colleagues examined the weakness on the other side of the ledger, namely the "
        "vulnerabilities of the smart contracts that record those claims, and argued that on-chain state is only as "
        "strong as the off-chain verification feeding it [3]. That last point shaped our implementation more than "
        "any other: the ledger stores authorised digests and their signatures, but the verdict is produced by an "
        "ordinary off-chain verifier that can be unit tested, and the chain is re-verifiable on demand instead of "
        "being trusted on faith."
    )
    para(
        "On unsupervised detection, the algorithm family we adopted was argued for by Ortega and colleagues, who "
        "showed that an isolation forest can be discretised to fit the memory and compute budget of "
        "resource-constrained IoT edge devices [4]. That matters here because the decision service runs beside a web "
        "server and a broker on a laptop, and because a deep autoencoder would have been disproportionate to a "
        "seven-feature problem. Zahoor and colleagues combined an isolation forest with a one-class SVM for IoT "
        "traffic and reported complementary strengths, with the forest fast and stable and the SVM tighter on "
        "unseen classes [5]. Both of those works assume features drawn from network flows. The features we use are "
        "windowed state of a single display controller, such as failed logins in the last five minutes, whether an "
        "unauthorised stick was seen, and how long ago the last approved update arrived, because that is the shape "
        "of the question actually asked at the display."
    )
    para(
        "On explainability, a score that cannot be justified is of little use to a duty manager who has to decide "
        "whether to keep a sign dark during a busy service. Bin hulayyil, Li and Saxena built an explainable "
        "intrusion detection system for IoT in which SHAP justifies each classification rather than only auditing "
        "the model offline [6]. Dong and colleagues proposed NGSHAP-IDS, pairing NGBoost with a SHAP explanation "
        "framework and demonstrating on UNSW-NB15, CICIDS2017 and N-BaIoT that interpretability can be obtained "
        "without giving up detection accuracy [7]. Taheri and colleagues carried the same principle into connected "
        "vehicles under federated learning, where a deep detector is explained per vehicle by SHAP [8]. Almadhor "
        "and colleagues pushed further towards self-explaining architectures with a neuro-symbolic dual model, "
        "arguing that explanation should be part of the detection loop rather than a post-hoc report [9]."
    )
    para(
        "Reading those three strands together makes the gap plain, and it is a gap of assembly rather than of "
        "technique. Ledger-based work proves that data was recorded, not that the bytes about to be rendered are "
        "the authorised bytes. Anomaly detection classifies observations but has no opinion on authenticity. "
        "Explainability justifies a class label but is rarely wired to an actuator. SignGuard AI joins the three: a "
        "deterministic integrity gate in front of rendering, an unsupervised model and rule signals for context, "
        "SHAP factors carried inside the decision object, and an MQTT command that changes what the sign shows."
    )


def method():
    h1("3. Method")
    h1("3.1 Architecture")
    para(
        "The system runs in three planes on one local network, as shown in Figure 1. The edge plane holds the "
        "sensors and actuators: a USB monitor that reports drive insertion, a board watcher that detects a serial "
        "device and clears its cached state when the device disappears, the event and content simulators used for "
        "evaluation, and the NodeMCU ESP-12E node that drives the indicators. The broker plane is a single Mosquitto "
        "instance on port 1883 carrying three topics, namely signguard/events for security observations, "
        "signguard/content for arriving payloads, and signguard/commands for verdicts travelling back out. The "
        "server plane is a FastAPI application on port 8000 that exposes the REST surface, runs one shared analysis "
        "pipeline, and owns two stores: a file-backed SQLite audit table and the hash-linked ledger of authorised "
        "content. Those two ports, 8000 and 1883, are the only ones the system occupies."
    )
    figure("fig3_architecture.png",
           "Figure 1: The three planes of the deployment. Edge sensors publish to the broker, the server plane "
           "subscribes, and verdicts travel back out to the signage node.")
    para(
        "One detail of this layout is worth stating because it removes a whole class of bugs. The REST handler and "
        "the MQTT consumer both call the same function, run_analysis, which owns verification, feature "
        "construction, model scoring, explanation, fusion, decision and audit write in a fixed order. There is no "
        "second implementation of the decision logic behind the message bus, so a request arriving over HTTP and the "
        "same request arriving over MQTT cannot produce different verdicts."
    )
    h1("3.2 The two tracks and the order between them")
    para(
        "Inside that pipeline the work is split into two tracks that are deliberately unequal. The first track is "
        "deterministic. Authorisation records the authority-approved bytes and their SHA-256 digest, the record is "
        "appended to a ledger whose blocks are hash-linked and signed with Ed25519, and verification recomputes the "
        "digest of the arriving payload and compares it with the stored one. The comparison returns match, mismatch "
        "or unknown content, and the decision engine reads that result first. A mismatch is terminal: the engine "
        "returns block and safe fallback with the reason hash mismatch, and it does so before touching the risk "
        "score or the model. The second track is probabilistic. A per-device event store behind the MQTT "
        "subscription supplies the last five minutes of activity, the feature engine collapses that window into "
        "seven numbers, the isolation forest turns them into an anomaly assessment between 0 and 1, and the SHAP "
        "explainer decomposes the same assessment into signed per-feature contributions. Rule signals for "
        "unauthorised USB, default credentials and rogue wireless activity are then added to the scaled model "
        "assessment with frozen weights, and the total, capped at 100, is the risk score."
    )
    para(
        "The order between the tracks is the safety argument of the project, so it is worth being blunt about what "
        "it buys. Because authenticity is decided by a separate function with its own tests, a failure of the model, "
        "a drifted forest or a missing explainer cannot let tampered content through; they can only make the "
        "response to genuine content less accurate. The measured trace of this is visible in Section 5, where every "
        "blocked scenario reports the reason hash mismatch and nothing else, which tells us the fusion stage did not "
        "participate in those verdicts at all."
    )
    figure("fig5_decision_flow.png",
           "Figure 2: The decision flow. The digest gate is evaluated first, and the model only refines the case "
           "where the digest matched.")
    h1("3.3 Algorithms")
    para(
        "Authorisation and verification together form the gate. The pseudo-code below is the complete logic; the "
        "signature step is what makes the ledger an authority record rather than a shared list."
    )
    code(
        "AUTHORISE(bytes B, content C, device D):\n"
        "    h <- SHA256(B)\n"
        "    s <- Ed25519_SIGN(authority_key, h || C || D)\n"
        "    ledger.append({h, C, D, s, prev_hash})      # hash-linked block\n"
        "    return record\n"
        "\n"
        "VERIFY(payload B', content C, device D):\n"
        "    record <- ledger.lookup(C, D)\n"
        "    if record is None:            return (False, 'unknown_content')\n"
        "    if verify_chain() is False:   return (False, 'ledger_invalid')\n"
        "    if SHA256(B') != record.hash: return (False, 'hash_mismatch')\n"
        "    return (True, 'hash_match')"
    )
    para(
        "The context model and its explanation are equally short. The feature window is fixed at 300 seconds and "
        "the column order is held in a single constant that both the scorer and the explainer import, which is what "
        "stops the two components from ever reading the same vector with different alignment."
    )
    code(
        "ASSESS(device D, window W of last 300 s):\n"
        "    x  <- feature_vector(D, W)      # 7 columns, fixed order\n"
        "    a  <- isolation_forest(x)       # anomaly assessment in [0,1]\n"
        "    phi<- shap_values(model, x)     # signed per-feature contributions\n"
        "    return a, top(phi, k=5)\n"
        "\n"
        "FUSION(match, events, a):\n"
        "    R <- 40*hash_mismatch + 20*unauthorised_usb + 15*default_credential\n"
        "         + 10*wireless_anomaly + 15*a, capped at 100\n"
        "    if not match:            return BLOCK  + safe_fallback   # terminal\n"
        "    if R >= 80:              return ISOLATE + escalate\n"
        "    if R >= 50:              return BLOCK  + safe_fallback\n"
        "    return RENDER"
    )
    para(
        "The weights are frozen constants rather than learned parameters, and the cut points at 50 and 80 are "
        "shared by the scoring module and the decision engine. We kept them frozen on purpose: when a score appears "
        "as evidence after an incident, a reviewer should be able to predict it by hand from the event list."
    )
    h1("3.4 Enforcement at the edge")
    para(
        "A verdict that stays in a database is only an opinion. The decision is therefore published as an MQTT "
        "command, and the ESP-12E node maps the three command values onto the physical display: render shows the "
        "authorised text with the green LED lit, safe fallback replaces it with a guarded message and lights the red "
        "LED, and isolate additionally sounds the buzzer for 1.2 seconds and shows that updates are blocked. The "
        "node keeps showing the last state it received, which is precisely the property that matters when the "
        "management network drops during an incident. On the operator side the board watcher mirrors this in "
        "software: when a serial device disappears it clears its cached device state, so a later insertion is "
        "judged on fresh evidence rather than on a stale allow-list entry."
    )


def experimentation():
    h1("4. Experimentation")
    h1("4.1 Data")
    para(
        "No public corpus exists for tampered transit-signage content. Reported incidents yield screenshots in news "
        "articles rather than labelled payloads, and the standard intrusion detection benchmarks such as UNSW-NB15, "
        "CICIDS2017 and N-BaIoT describe network flows rather than the authenticity of a text file about to be "
        "displayed. We therefore built two data sources, both of which ship with the repository so that every "
        "number in Section 5 can be reproduced."
    )
    para(
        "The first is a static event corpus of 29 synthetic security events distributed over six simulated signs, "
        "identified as SG-RNP-001 through SG-RNP-006. The events are drawn from a taxonomy of twelve types and "
        "eleven of those types appear in the file: content received and content hash mismatch are the most common, "
        "followed by USB connected, unauthorised USB, unauthorised wireless, login failure, login success, content "
        "hash match, wireless activity, default credential attempt and display tamper. The twelfth type, safe "
        "fallback activated, is deliberately absent from the file because it is produced at run time by the decision "
        "engine rather than replayed into it. This corpus is used by the unit tests to populate the feature window "
        "and by the dashboard to show historical activity."
    )
    para(
        "From those events the feature engine builds a seven-element vector over a 300 second window: failed "
        "logins, whether an unauthorised stick was seen, whether an unscheduled wireless source was seen, whether a "
        "hash mismatch was recorded, events per minute, seconds since the last authorised update capped at a "
        "constant, and a standing device trust score between 0 and 1. The second data source is generated at run "
        "time by four scenarios that inject real content and real events through the broker and are analysed by the "
        "production path: a baseline carrying authority-approved content, a malicious USB replacement of that "
        "content, a rogue wireless update, and a default-credential attack on the administration panel. Those four "
        "scenarios form the evaluation corpus of Section 5."
    )
    h1("4.2 Environment and procedure")
    para(
        "Everything ran on a single Windows laptop with Python 3.13.4, FastAPI 0.141.1 behind Uvicorn 0.52.4, "
        "paho-mqtt 2.1.0 talking to a Mosquitto broker on port 1883, scikit-learn 1.8.0 for the isolation forest, "
        "SHAP 0.52.0 for the explanations, Pydantic 2.13.4 for the schemas and SQLite from the standard library for "
        "the audit store. The automated suite uses pytest 9.1.1 and contains 46 cases spread over seven modules. "
        "Measurements were taken in three ways so that they could be cross-checked against each other. The pipeline "
        "was timed in process, without sockets, for 40 repetitions of each scenario. The HTTP path was timed over a "
        "keep-alive connection for 50 requests, and separately with a fresh TCP connection per request for 15 "
        "requests, because the two differ far more than we expected. Latency is reported as median unless a mean is "
        "stated."
    )


def results():
    h1("5. Result and Analysis")
    para(
        "The four scenarios were executed end to end, meaning that the content and events travelled through the "
        "broker, the pipeline produced the verdict, and the results below come from the production code path rather "
        "than from a replay or a mock. Table 1 summarises what happened."
    )
    table(
        ["Scenario", "Verification", "Risk", "Decision", "Command", "Reason given"],
        [["Baseline, authority-approved content", "Match", "1/100 (low)", "Render", "render",
          "hash match, risk acceptable"],
         ["Malicious USB replacement", "Mismatch", "71/100 (high)", "Block", "safe fallback", "hash mismatch"],
         ["Rogue wireless update", "Mismatch", "62/100 (high)", "Block", "safe fallback", "hash mismatch"],
         ["Default-credential panel attack", "Mismatch", "66/100 (high)", "Block", "safe fallback", "hash mismatch"]],
        widths=[2.0, 0.85, 0.95, 0.7, 0.85, 1.15],
        size=8.6)
    para(
        "Detection on this corpus is therefore three attacks out of three blocked, with one genuine update rendered "
        "and no false positive. The number worth staring at is not 71 but the column next to it: all three attacks "
        "report the same reason, hash mismatch, which is the fingerprint of the ordering described in Section 3.2. "
        "The fusion stage contributed risk points but did not decide anything, and had the forest been unavailable "
        "at that moment the three payloads would still have been blocked. Figure 3 plots the risk scores against "
        "the frozen thresholds."
    )
    figure("fig6_risk.png",
           "Figure 3: Risk score of each scenario measured against the frozen level thresholds. The genuine update "
           "sits far below the render threshold of 50; all three attacks sit above it.")
    para(
        "Latency was the part of the evaluation that taught us something we had not expected. Timing the pipeline "
        "in process gave a mean of 21.7 ms for a scenario with a populated event window, of which the SHAP "
        "explanation is the dominant term, while a content-only request over keep-alive HTTP measured a median of "
        "3.3 ms. Both are far inside the budget of a display that updates every few seconds. The surprise was the "
        "fresh-connection case, which measured a suspiciously constant 2040 ms. Chasing it down showed that the "
        "health endpoint was exactly as slow as the analysis endpoint, that a keep-alive request on the same "
        "connection took half a millisecond, and that the hostname localhost resolves to the IPv6 address ::1 on "
        "this host while the ASGI server binds IPv4 only. Each new connection was therefore waiting about two "
        "seconds before falling back. The processing path was never the slow part; an environmental artefact was "
        "being attributed to our decision engine. Figure 4 shows both numbers side by side so that the distinction "
        "is not lost, and the practical guidance we recorded from it is to address the service by an IPv4 literal "
        "or to bind a dual-stack listener."
    )
    figure("fig7_latency.png",
           "Figure 4: Measured decision latency. Explainable inference dominates the pipeline, transport is "
           "negligible, and the two second bar on the right is the name-resolution artefact discussed above.")
    para(
        "The explanations themselves were consistent in a way that we consider the strongest evidence for keeping "
        "them inside the decision object. In the baseline it is the staleness of the last authorised update that "
        "pushes the assessment up, with an impact of about plus 2.1, while the device trust score and login history "
        "pull it down. In all three attacks the dominant factor is the standing device trust score, between plus "
        "3.2 and plus 3.7, followed immediately by the specific hostile signal: unauthorised stick at plus 2.2 for "
        "the USB case, wireless anomaly at plus 2.5 for the rogue radio, and failed logins at plus 1.5 for the "
        "credential attack. An operator reading the third factor of any verdict can name the behaviour that caused "
        "it without opening a notebook, and because the ranking is stable across near-identical inputs there is no "
        "reason to learn to ignore it. Figure 5 shows the decomposition for the highest scoring attack."
    )
    figure("fig8_shap.png",
           "Figure 5: SHAP decomposition of the malicious USB assessment. The contribution of each of the seven "
           "features is signed, so the operator sees what raised the score and what held it down.")
    para(
        "Two limitations belong in this discussion rather than in a footnote. The MQTT broker is reachable on all "
        "interfaces without transport security, which is acceptable on an isolated demonstration network but must be "
        "replaced by TLS with client certificates before anything operational. The feature window also lives in "
        "memory, so a restart of the service resets the per-device counters, although the audit trail and the ledger "
        "are file-backed and did survive the restarts we performed. The edge node acts on the command it receives "
        "rather than re-verifying the digest itself, which means it trusts the broker; moving SHA-256 verification "
        "into the firmware would remove that assumption and is the next architectural step rather than a tuning "
        "change."
    )


def conclusion():
    h1("6. Conclusion")
    para(
        "SignGuard AI places a deterministic integrity check where the incidents of the last few years show it is "
        "missing, namely immediately before a public display renders text it did not create. Content is authorised "
        "in advance, its digest lives in a signed hash-linked ledger, and every arriving payload is compared against "
        "that record. A mismatch ends the decision and no probabilistic component can reopen it. Around that gate we "
        "run an unsupervised model over a five minute window of the device's own behaviour, fuse it with rule "
        "signals into a risk score with frozen weights, and attach SHAP attributions to the verdict so the operator "
        "learns why rather than only what. Verdicts are appended to a file-backed audit store, re-verifiable "
        "through the chain endpoint, and enforced physically on an ESP8266 node with text, LEDs and a buzzer."
    )
    para(
        "The evaluation supports the design. Three attacks out of three were blocked and the genuine update was "
        "rendered with no false positive; 46 of 46 automated tests pass; a full explainable decision costs 21.7 ms; "
        "and the audit trail and the ledger were read back successfully after the service was restarted. The "
        "incidents described in the introduction were successful precisely because nothing like this gate sat "
        "between a USB stick and a screen, and the results suggest that adding one is neither expensive nor "
        "latency-critical."
    )
    para(
        "The work also produced one finding that generalises beyond this project. A latency measurement that looks "
        "wrong should be decomposed before it is optimised; the two second cost we first attributed to explainable "
        "inference turned out to be IPv6 name resolution on the client side, and had we not separated the transport "
        "from the pipeline we would have written a very confident paragraph about the wrong thing."
    )
    para(
        "Several directions follow naturally. Verification should move into the edge firmware so that the node no "
        "longer has to trust the broker. The broker should be put behind TLS with per-device client certificates, "
        "and the authority key should be rotated rather than kept static. The feature window should be persisted "
        "with the audit store so that counters survive a crash. The Ethereum prototype that sits alongside this "
        "repository could be wired to the authorisation endpoint as an alternative ledger backend, keeping the "
        "current hash-linked chain as the local source of truth. And the trust score could be shared across a fleet "
        "so that a display newly exposed to an unknown stick is treated cautiously everywhere on the network, "
        "without centralising the raw events themselves."
    )


def references():
    h1("7. References")
    items = [
        "Dai HN, Zheng Z, Zhang Y. Blockchain for Internet of Things: a survey. IEEE Internet Things J. "
        "2019;6(5):8076-8094.",
        "Liu Y, Wang J, Yan Z, Wan Z, Jantti R. A survey on blockchain-based trust management for Internet of "
        "Things. IEEE Internet Things J. 2023;10(7):5898-5922.",
        "He D, Wu R, Li X, Chan S, Guizani M. Detection of vulnerabilities of blockchain smart contracts. IEEE "
        "Internet Things J. 2023;10(14):12178-12185.",
        "Ortega E, Su F, Chattopadhyay R, Chakrabarty K. Discretized-isolation forest: memory- and compute-efficient "
        "unsupervised anomaly detection for resource-constrained Internet of Things edge devices. IEEE Internet "
        "Things J. 2025;12(2):1699-1717.",
        "Zahoor A, Abbasi W, Babar MZ, et al. Robust IoT security using isolation forest and one class SVM "
        "algorithms. Sci Rep. 2025;15:36586.",
        "Bin hulayyil S, Li S, Saxena N. Explainable AI-based intrusion detection in IoT systems. Internet Things. "
        "2025;31:101589.",
        "Dong J, et al. Interpretable intrusion detection for IoT security: a SHAP-based approach. Comput Netw. "
        "2025;:111937.",
        "Taheri R, Jafari R, Gegov A, Arabikhan F, Ichtev A. Explainable AI for federated learning-based intrusion "
        "detection systems in connected vehicles. Electronics. 2025;14(22):4508.",
        "Almadhor A, Alsubai S, Al Hejaili A, Klai Z, Bouallegue B, Kovac U. Designing a neuro-symbolic dual-model "
        "architecture for explainable and resilient intrusion detection in IoT networks. Sci Rep. 2025;15:42786.",
        "Khan I, Majib Y, Ullah R, Rana O. Blockchain applications for Internet of Things - a survey. Internet "
        "Things. 2024;27:101254.",
    ]
    for i, ref in enumerate(items, start=1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Inches(0.45)
        pf.first_line_indent = Inches(-0.45)
        pf.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(f"[{i}] {ref}")
        r.font.size = Pt(10)
        r.font.name = "Tahoma"


if __name__ == "__main__":
    front_matter()
    abstract()
    introduction()
    related_work()
    method()
    experimentation()
    results()
    conclusion()
    references()
    for target in (OUT, OUT.with_name(OUT.stem + "_v2.docx")):
        try:
            doc.save(target)
        except PermissionError:
            print(f"! {target.name} is open in another program - trying the next name")
            continue
        print("saved", target)
        break
    else:
        raise SystemExit("close the open document and re-run")
