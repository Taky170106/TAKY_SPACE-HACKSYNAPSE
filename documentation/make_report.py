"""Build the ISWE415L Cyber Security course-project report (SignGuard AI).

    python documentation/make_report.py

Produces  documentation/SignGuard_AI_Course_Project_Report.docx
Figures come from documentation/figures/ (made by make_diagrams.py);
numbers come from documentation/metrics.json (made by collect_metrics.py).
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = Path(__file__).parent
FIG = HERE / "figures"
OUT = HERE / "SignGuard_AI_Course_Project_Report.docx"
M = json.loads((HERE / "metrics.json").read_text(encoding="utf-8"))

TITLE = ("SignGuard AI — Integrity-Guarded Content Delivery for Public-Transport "
         "Digital Signage with Explainable Intrusion Detection")

TEMPLATE = Path(r"C:\Users\tamiz\Downloads\Cyber Security QP P (2).docx")
if not TEMPLATE.exists():
    raise SystemExit(f"template not found: {TEMPLATE}")

doc = Document(TEMPLATE)
# body elements that came with the template, used later to relocate our content
_TEMPLATE_BODY = {id(el) for el in doc.element.body.iterchildren()}

# --------------------------------------------------------------------------- #
# low-level docx helpers
# --------------------------------------------------------------------------- #
_ALIGN = {"just": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER,
          "left": WD_ALIGN_PARAGRAPH.LEFT, "right": WD_ALIGN_PARAGRAPH.RIGHT}


def _base_style() -> None:
    st = doc.styles["Normal"]
    st.font.name = "Tahoma"
    st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Tahoma")
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.2


def para(text: str = "", *, size: int = 11, bold: bool = False, italic: bool = False,
         align: str = "just", before: float = 0, after: float = 6, color: str | None = None,
         indent: float = 0.0, font: str = "Tahoma"):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.left_indent = Inches(indent)
    p.alignment = _ALIGN[align]
    if text:
        r = p.add_run(text)
        r.bold, r.italic = bold, italic
        r.font.size = Pt(size)
        r.font.name = font
        if color:
            r.font.color.rgb = RGBColor.from_string(color)
    return p


def h1(text: str):
    return para(text, size=14, bold=True, align="left", before=16, after=8)


def h2(text: str):
    return para(text, size=12, bold=True, align="left", before=12, after=6)


def h3(text: str):
    return para(text, size=11, bold=True, italic=True, align="left", before=8, after=4)


def bullet(text: str, size: int = 11, indent: float = 0.35):
    # the submitted template carries no list styles, so markers are drawn manually
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(indent + 0.25)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("\u2022  " + text)
    r.font.size = Pt(size)
    r.font.name = "Tahoma"
    return p


_LIST_COUNTER = itertools.count(1)


def numbered(text: str, size: int = 11):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.6)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(f"{next(_LIST_COUNTER)}.  " + text)
    r.font.size = Pt(size)
    r.font.name = "Tahoma"
    return p


def figure(name: str, caption: str, width: float = 6.1):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(FIG / name), width=Inches(width))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(12)
    r = c.add_run(caption)
    r.italic = True
    r.font.size = Pt(9)
    r.font.name = "Tahoma"
    return p


def _shade(cell, fill: str) -> None:
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(shd)


def _table_borders(t) -> None:
    """The template ships only the 'Table Normal' style, so borders are drawn here."""
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "7F7F7F")
        borders.append(el)
    t._tbl.tblPr.append(borders)


def table(headers: list[str], rows: list[list], widths: list[float] | None = None,
          size: float = 9.0, caption: str | None = None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    _table_borders(t)
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
        _shade(cell, "DDEBF7")
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
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_before = Pt(4)
        c.paragraph_format.space_after = Pt(10)
        r = c.add_run(caption)
        r.italic = True
        r.font.size = Pt(9)
        r.font.name = "Tahoma"
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def code(text: str, size: float = 8.5):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Inches(0.2)
    pf.right_indent = Inches(0.1)
    pf.space_before = Pt(6)
    pf.space_after = Pt(8)
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), "F2F2F2")
    p._p.get_or_add_pPr().append(shd)
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(size)
    return p


def pagebreak():
    doc.add_page_break()


# --------------------------------------------------------------------------- #
# 1. Problem statement
# --------------------------------------------------------------------------- #
def section_1() -> None:
    h1("1. Problem Statement")

    h2("1.1 Background (System Study Details in brief)")
    para(
        "Every large transport operator now runs a fleet of electronic destination boards: platform indicators inside "
        "a station, departure boards in the concourse, and e-paper panels on bus stops. Each of these displays is driven "
        "by a small controller that obtains its picture from one of three convenient channels — a USB flash drive "
        "carried by a field technician, a scheduled wireless synchronisation with a central content server, or a "
        "browser-based administration panel used for ad-hoc corrections such as a platform change during engineering "
        "work. All three channels were engineered for availability and ease of maintenance, and in practice none of "
        "them authenticates the picture itself. The controller accepts whatever bytes arrive, renders them, and only "
        "a human noticing that the board is wrong discovers the problem. Between the authority that authorised the "
        "message and the passenger reading it there is therefore no integrity check of any kind."
    )
    para(
        "This gap is no longer theoretical. In October 2025 four North American airports had flight-information "
        "displays defaced by an unknown group, and in the following month e-paper bus-stop panels operated by the "
        "Los Angeles Metro were made to display a fabricated emergency warning telling passengers to leave immediately "
        "because of a suicide bomb; the displays kept showing the message until the vendor traced the intrusion "
        "(AV Magazine, 5 November 2025). Bristol Airport's departure screens suffered a comparable ransom message "
        "years earlier. In every published case the mechanism was mundane rather than exotic: a management interface "
        "left on factory credentials, an exposed USB port, or an update copied over an unauthenticated link. National "
        "CERT advisories on kiosk and signage hardening list exactly these three items — open USB ports, default "
        "credentials and unsigned update packages — as the first things to close, yet they remain the default state "
        "of most installed hardware because closing them usually breaks the maintenance routine the vendor sold."
    )
    para(
        "The consequence of a wrong sign is operational rather than merely cosmetic. A platform indicator that names "
        "the wrong platform sends an entire carriage in the wrong direction; a departure time that silently slips "
        "causes missed connections; an unexplained blank or hostile message during an evacuation removes the one "
        "channel a station has for directing people. The operator's liability, the cost of manual verification, and "
        "the erosion of passenger trust all scale with the number of displays, while the number of displays scales "
        "with the size of the network. Inspection by walking the platforms is therefore not a solution that survives "
        "growth."
    )
    para(
        "Two families of existing defence fall short of the requirement. Cryptographic protection of the transport "
        "path (TLS, authenticated package repositories, VPNs between the server and the controller) proves that the "
        "bytes came down a protected pipe, but a USB stick never traverses that pipe, and a legitimate operator can "
        "still push a file that was never authorised by the content authority. Signature verification on the "
        "controller would help, yet commodity signage firmware rarely implements it, and where it exists it usually "
        "verifies the container rather than the payload. On the other side of the literature, intrusion-detection "
        "systems classify network traffic and raise alerts; they do not decide whether the specific text about to be "
        "shown to ten thousand passengers is the text the transport authority approved. What is missing is a gate "
        "that sits immediately before rendering, verifies the content itself against an authorised reference, "
        "considers the attack context around it, explains its verdict, and can force the display into a safe state "
        "without a human in the loop."
    )

    h2("1.2 Problem Statement")
    para(
        "Design and implement an integrity gate — SignGuard AI — that sits between every content-ingress channel of a "
        "public-transport digital sign (USB, wireless synchronisation and administration panel) and the act of "
        "rendering, such that:"
    )
    for b in [
        "R1  Authenticity is decided deterministically: an update renders only if its SHA-256 digest equals the "
        "digest of a content record authorised in advance by the transport authority and bound to an Ed25519-signed, "
        "hash-linked ledger entry.",
        "R2  Tampering is a terminal condition: any mismatch, unknown content or absent authorisation blocks the "
        "update and drives a safe fallback message, and no probabilistic component is allowed to overrule that "
        "verdict (false negatives for tampered content must be structurally impossible, not merely unlikely).",
        "R3  The surrounding attack context is assessed by an unsupervised model and fused with rule signals into a "
        "single 0–100 risk score that refines what happens when the hash does match — render, block or isolate the "
        "update channel.",
        "R4  Every verdict is explainable: the decision carries the ranked SHAP factors that produced the model's "
        "assessment, so an operator sees why, not only what.",
        "R5  Every verdict is non-repudiable: it is appended to a tamper-evident audit trail that survives process "
        "restarts, and the ledger can be re-verified independently through an API endpoint.",
        "R6  The verdict reaches the physical display within a real-time budget (tens of milliseconds of processing, "
        "MQTT round-trip included) and is enforced physically through LCD text, a green/red LED pair and a buzzer, so "
        "a failed network link cannot silently leave a false sign lit.",
    ]:
        bullet(b)
    para(
        "The objective is therefore a two-track decision system in which deterministic content verification gates "
        "rendering, explainable machine learning quantifies the context around it, a single fusion rule converts both "
        "into an actionable command, and the command is observable on hardware, on a dashboard and in an audit record "
        "that can be produced after the incident.",
        before=6,
    )

    h2("1.3 Novelty")
    para("The contribution of this project relative to existing signage-security and IoT-IDS work is fivefold:")
    numbered(
        "Integrity before intelligence. Verification is a hard gate placed ahead of the model: a hash mismatch blocks "
        "immediately and never waits for inference (Section 4.1). Published IoT intrusion-detection systems, including "
        "the SHAP-based ones surveyed in Section 2.1, produce a classification that a human may ignore; here the "
        "probabilistic component can only refine a match, never open one."
    )
    numbered(
        "Explainability attached to the verdict rather than to the model. Each decision object embeds the top SHAP "
        "factors and their signed impact, and they are surfaced next to the decision on the audit endpoint and the "
        "dashboard. Explainability becomes an operational artefact usable during an incident, not a research plot."
    )
    numbered(
        "Authorisation provenance on a hash-linked, Ed25519-signed ledger that is independent of the process, "
        "re-verifiable on demand through /chain/verify, and separated from the append-only operational audit store "
        "so that compromise of one does not silently rewrite the other."
    )
    numbered(
        "Physical enforcement of the safe state. The decision travels over MQTT to the edge node, which renders "
        "authorised text, a tamper message or a safe fallback on an LCD and signals it with LEDs and a buzzer, giving "
        "the safe state a representation that survives the loss of the management network."
    )
    numbered(
        "A single shared pipeline (run_analysis) behind both REST and MQTT entry points, proved by an automated suite "
        "in which the negative cases — tampered content, unknown content, default credentials, rogue wireless activity "
        "— are first-class tests rather than demonstrations."
    )

    h2("1.4 Dataset (If Used)")
    para(
        "No public corpus exists for tampered transit-signage content: reported incidents yield screenshots rather "
        "than labelled payloads, and the standard intrusion-detection benchmarks (UNSW-NB15, CICIDS2017, N-BaIoT) "
        "describe network flows rather than the authenticity of a text file about to be displayed. The project "
        "therefore uses two purpose-built sources, both of which ship with the repository so that every number in "
        "Section 5 can be reproduced."
    )
    h3("(a) Static event corpus — data/sample_events.json")
    para(
        "29 synthetic security events distributed over six simulated signs (SG-RNP-001 … SG-RNP-006) drawn from a "
        "12-type taxonomy, covering 11 of the 12 types (only safe_fallback_activated is produced at runtime by the "
        "decision engine rather than replayed from the file). The corpus is used by the unit tests to populate the "
        "300-second feature window and by the dashboard to seed historical activity."
    )
    table(
        ["Event type", "Count", "What it represents in the threat model"],
        [["content_received", "6", "A content payload arrives over one of the three ingress channels"],
         ["content_hash_mismatch", "4", "Arrived bytes differ from the authorised digest (integrity break)"],
         ["content_hash_match", "2", "Genuine update — the true-positive control case"],
         ["usb_connected / unauthorized_usb", "3 / 3", "A stick is inserted; it is not on the allow-list"],
         ["wireless_activity / unauthorized_wireless", "1 / 3", "Normal sync vs. an unscheduled radio source"],
         ["login_success / login_failure", "2 / 3", "Normal administration sign-in and failed attempts"],
         ["default_credential_attempt", "1", "Vendor-default username/password used against the panel"],
         ["display_tamper", "1", "Direct physical interference with the display unit"],
         ["safe_fallback_activated", "0 (runtime)", "Emitted by the decision engine when a sign is blocked"],
         ["Total", "29", "6 devices · 11 of 12 taxonomy types observed"]],
        widths=[1.9, 0.9, 3.5],
        caption="Table 1: Composition of the static security-event corpus.",
    )
    h3("(b) Scenario corpus — the four live attack scenarios")
    para(
        "The evaluation corpus is produced at runtime by four scenarios that inject real events and real content "
        "through the MQTT broker and are then analysed by the production path: a baseline with authority-approved "
        "content, a malicious USB replacement of that content, a rogue wireless update, and a default-credential "
        "administration-panel attack. Each scenario yields a verification result, a seven-feature vector, a model "
        "assessment, a risk score, a ranked SHAP explanation and a final decision; these are the rows measured in "
        "Section 5."
    )
    table(
        ["#", "Feature (fixed column order)", "Definition and window"],
        [["1", "failed_logins_5min", "Count of login_failure events in the last 300 s"],
         ["2", "unknown_usb_detected", "1 if an un-authorised stick was seen in the window, else 0"],
         ["3", "wireless_anomaly", "1 if an unscheduled wireless source was seen, else 0"],
         ["4", "content_hash_mismatch", "1 if a mismatch was recorded in the window, else 0"],
         ["5", "events_per_minute", "Event throughput of the device, normalised rate"],
         ["6", "time_since_authorized_update", "Seconds since the last authority-approved update (capped)"],
         ["7", "device_trust_score", "Standing reputation of the device, 0 (unknown) to 1 (authorised)"]],
        widths=[0.35, 2.0, 3.95],
        caption="Table 2: The seven-element feature vector shared by the model and the SHAP explainer.",
    )
    para(
        "The fixed column order is held in a single constant (FEATURE_ORDER) imported by both the isolation-forest "
        "scorer and the SHAP explainer, so a vector can never be read with a different alignment by the two "
        "components — a failure mode that would silently corrupt every explanation produced at run time.",
        before=4,
    )


# --------------------------------------------------------------------------- #
# 2. Related works
# --------------------------------------------------------------------------- #
def section_2() -> None:
    h1("2. Related Works")

    h2("2.1 Literature Survey")
    para(
        "Securing the things that produce and consume data in the Internet of Things has been studied from three "
        "angles that are relevant here: making the data's provenance verifiable, deciding whether an observation is "
        "anomalous, and explaining that decision to a human."
    )
    h3("Provenance, ledgers and content integrity")
    para(
        "The broadest reference point is Dai, Zheng and Zhang [1], who named the combination of blockchain with IoT "
        "as 'blockchain of things' and catalogued how a distributed ledger replaces a trusted intermediary when "
        "devices cannot rely on a central authority. Liu et al. [2] narrowed the question to trust management and "
        "surveyed how reputation and ledger-backed attestation are shared between IoT devices, concluding that "
        "blockchain-based schemes improve tamper evidence but usually assume the device itself is trustworthy. Khan "
        "et al. [10] reviewed blockchain applications across the IoT stack and identified integrity of data in motion "
        "as the dominant use case, with device-side verification still largely unimplemented. He et al. [3] examined "
        "the other side of the ledger — the vulnerabilities of the smart contracts that record those claims — and "
        "argued that on-chain state is only as strong as the off-chain verification feeding it. Together these works "
        "motivate the design choice taken in this project: the ledger stores authorised digests and their signatures, "
        "but the decision is made by an off-chain verifier that can be unit-tested, and the chain is re-verifiable "
        "independently rather than trusted on faith."
    )
    h3("Unsupervised anomaly detection at the edge")
    para(
        "Because labelled attack data for signage networks does not exist, the context assessment had to be "
        "unsupervised and small enough to run beside a web server. Ortega et al. [4] showed that an isolation forest "
        "can be discretised to fit the memory and compute budget of resource-constrained IoT edge devices, which is "
        "the argument for the algorithm family rather than a deep autoencoder. Zahoor et al. [5] combined an "
        "isolation forest with a one-class SVM for IoT traffic and reported the complementary strengths of the two: "
        "the forest is fast and stable, the SVM tighter on unseen classes. Both assume network-flow features; our "
        "features are windowed state of a single device (failed logins, unauthorised sticks, time since an approved "
        "update, standing trust), which is the shape of the problem actually faced at the display."
    )
    h3("Explainability")
    para(
        "A score that cannot be justified is unusable to a duty manager, so the third thread is explainable AI. Bin "
        "hulayyil, Li and Saxena [6] built an explainable IDS for IoT in which SHAP is used to justify each "
        "classification rather than only to audit the model offline. Dong et al. [7] proposed NGSHAP-IDS, pairing "
        "NGBoost with a SHAP explanation framework and demonstrating on UNSW-NB15, CICIDS2017 and N-BaIoT that "
        "interpretability can be obtained without giving up detection accuracy. Taheri et al. [8] carried the same "
        "principle into connected vehicles under federated learning, where a deep detector is explained by SHAP per "
        "vehicle. Almadhor et al. [9] pushed further towards self-explaining architectures with a neuro-symbolic "
        "dual model, again evaluated on NF-BoT-IoT-V2, arguing that explanation should be part of the detection "
        "loop rather than a post-hoc report. The pattern across this literature is that explanation is attached to a "
        "classification of traffic; none of the surveyed systems explains a content-authenticity verdict, because "
        "none of them makes one."
    )
    h3("Gap addressed by this project")
    para(
        "The comparison in Section 2.2 makes the gap explicit. Ledger-based work proves data was recorded, not that "
        "the bytes about to be rendered are the authorised bytes; anomaly-detection work classifies flows but cannot "
        "say whether this file is authentic; explainability work justifies a class label but is never wired to an "
        "actuator. SignGuard AI joins the three: a deterministic integrity gate in front of rendering, an unsupervised "
        "model plus rule signals for context, SHAP factors carried inside the decision object, and an MQTT command "
        "that physically changes what the sign shows."
    )

    h2("2.2 Comparative Statement (10 Latest Journal Papers)")
    table(
        ["#", "Authors (Year)", "Journal", "Approach / evaluation", "Limitation relative to this work"],
        [["1", "Dai, Zheng & Zhang (2019)", "IEEE Internet of Things Journal",
          "Survey of blockchain-of-things architectures; taxonomy of ledger use across IoT",
          "Architecture only — no content verification at the display, no decision or actuator"],
         ["2", "Liu, Wang, Yan, Wan & Jäntti (2023)", "IEEE Internet of Things Journal",
          "Survey of blockchain-based trust management for IoT; comparison of consensus and reputation schemes",
          "Assumes a trustworthy device; nothing verifies the payload before rendering"],
         ["3", "He, Wu, Li, Chan & Guizani (2023)", "IEEE Internet of Things Journal",
          "Detection of vulnerabilities in blockchain smart contracts; formal + empirical analysis",
          "Protects the ledger, not the off-chain content; no real-time gate"],
         ["4", "Ortega, Su, Chattopadhyay & Chakrabarty (2025)", "IEEE Internet of Things Journal",
          "Discretised isolation forest for memory/compute-constrained IoT edge nodes",
          "Optimises the detector but gives no explanation tied to a verdict, and never blocks content"],
         ["5", "Zahoor, Abbasi, Babar et al. (2025)", "Scientific Reports",
          "Isolation forest + one-class SVM for IoT security; benchmark evaluation",
          "Flow-based features; binary alerting only — no fusion with deterministic integrity"],
         ["6", "Bin hulayyil, Li & Saxena (2025)", "Internet of Things (Elsevier)",
          "Explainable AI-based IDS for IoT using SHAP justification per classification",
          "Explains traffic classes; the explanation is not attached to a rendering decision"],
         ["7", "Dong et al. (2025)", "Computer Networks",
          "NGSHAP-IDS: NGBoost classifier + SHAP framework on UNSW-NB15, CICIDS2017, N-BaIoT",
          "High accuracy but supervised and offline; no integrity gate or hardware enforcement"],
         ["8", "Taheri, Jafari, Gegov, Arabikhan & Ichtev (2025)", "Electronics (MDPI)",
          "Explainable federated IDS for connected vehicles; DNN + SHAP",
          "Federation and vehicles; explanation remains a dashboard artefact, not an action"],
         ["9", "Almadhor, Alsubai, Al Hejaili, Klai, Bouallegue & Kovac (2025)", "Scientific Reports",
          "Neuro-symbolic dual-model architecture for explainable, resilient IoT IDS (NF-BoT-IoT-V2)",
          "Detection-centric; assumes labelled traffic and a human responder"],
         ["10", "Khan, Majib, Ullah & Rana (2024)", "Internet of Things (Elsevier)",
          "Survey of blockchain applications across the IoT stack",
          "Identifies data integrity as the key use case but leaves device-side enforcement open"]],
        widths=[0.28, 1.35, 1.3, 1.75, 1.75],
        size=8.2,
        caption="Table 3: Comparative statement over ten recent journal papers in the domain.",
    )

    h2("2.3 Hardware Requirements")
    table(
        ["Component", "Specification", "Qty", "Role in the system"],
        [["Development laptop", "Windows 11, x86-64, ≥ 8 GB RAM", "1",
          "Hosts the broker, the FastAPI decision service, the dashboard and the tests"],
         ["Wi-Fi network", "2.4 GHz / LAN, WPA2", "1",
          "Shared transport between edge node, broker and decision service"],
         ["NodeMCU ESP-12E board", "ESP8266, 80 MHz, 4 MB flash, MicroPython", "1",
          "Edge signage node: subscribes to commands, drives the indicators"],
         ["LCD display", "16 × 2 character LCD with I2C backpack (PCF8574)", "1",
          "Shows authorised text, tamper message or the safe fallback"],
         ["LEDs (green, red)", "5 mm, 330 Ω series resistors", "2",
          "Green = verified content rendered; Red = blocked / isolated"],
         ["Buzzer", "5 V passive buzzer", "1", "Audible alert on a blocked or isolated update"],
         ["Breadboard + jumpers", "400-point half-size", "1", "Indicator wiring"],
         ["USB flash drive", "Standard mass-storage device", "1",
          "Simulated vector for the malicious-content attack"],
         ["Micro-USB cable", "Data-capable", "1", "Power and firmware flashing of the edge node"]],
        widths=[1.35, 1.9, 0.35, 2.8],
        caption="Table 4: Hardware bill of materials.",
    )

    h2("2.4 Software Requirements")
    table(
        ["Software", "Version used", "Purpose"],
        [["Windows 11 (PowerShell)", "23H2+", "Execution host; COM-port watching via winreg/SERIALCOMM"],
         ["Python", "3.13.4", "Service, tooling, test suite"],
         ["FastAPI", "0.141.1", "REST API, dependency injection, OpenAPI docs"],
         ["Uvicorn", "0.52.4", "ASGI server hosting the decision service on :8000"],
         ["Pydantic", "2.13.4", "Typed request/response schemas for events, content and decisions"],
         ["Eclipse Mosquitto", "2.x (launched by run_demo.py)", "MQTT broker on :1883 for the event/command bus"],
         ["paho-mqtt", "2.1.0", "MQTT client used by the orchestrator and the edge node"],
         ["scikit-learn", "1.8.0", "IsolationForest anomaly model and its persistence"],
         ["SHAP", "0.52.0", "TreeExplainer attributions carried inside each decision"],
         ["NumPy", "2.4.2", "Feature-vector arithmetic"],
         ["SQLite (standard library)", "3.x", "Append-only audit store, file-backed for restart survival"],
         ["pytest", "9.1.1", "Automated test suite (46 cases)"],
         ["MicroPython for ESP8266", "1.23.x", "Firmware on the NodeMCU ESP-12E edge node"],
         ["matplotlib", "3.10.8", "Generation of all figures in this report"],
         ["python-docx", "1.2.0", "Assembly of this document"],
         ["Git / GitHub", "2.x", "Version control and submission history"]],
        widths=[1.7, 1.5, 3.2],
        caption="Table 5: Software environment.",
    )


# --------------------------------------------------------------------------- #
# 3. System design
# --------------------------------------------------------------------------- #
def section_3() -> None:
    h1("3. System Design")

    h2("3.1 High-Level Design (Black Box Design)")
    para(
        "Figure 1 shows the system as a black box. Everything to the left of the box produces data, everything to "
        "the right consumes a verdict, and the box itself is deliberately opaque: at this level the only obligation "
        "of the drawing is to state what crosses the boundary, in which direction, and with what guarantee."
    )
    figure("fig1_hld.png", "Figure 1: High-level (black-box) design of SignGuard AI.")
    para(
        "External entities and the data they exchange are as follows. The unknown USB stick, the rogue wireless "
        "source and the default-credential administration panel are the adversarial inputs: they inject content bytes "
        "and associated security events without any authorisation. The transport authority is the trusted input: it "
        "registers content ahead of time, which fixes the reference digest and produces the signature that the box "
        "will later compare against. The edge sensor plane (USB monitor, board watcher, simulators) is the neutral "
        "input: it reports context — a stick appeared, a COM port vanished, a login failed — and makes no claim about "
        "content. On the output side the box emits four things: a command on the MQTT bus (render, safe_fallback or "
        "isolate) addressed to the sign, the physical indication itself (LCD text, green/red LED, buzzer), a durable "
        "record (audit endpoint plus hash-linked ledger, both readable after a restart), and the safe fallback text "
        "that replaces unverified content on the public display."
    )
    para(
        "Two properties of the black box are worth stating explicitly because the rest of the design protects them. "
        "First, the box is stateless with respect to the verdict: the same request body always yields the same "
        "decision, so a verdict can be reproduced during an incident. Second, the only path from input to actuator "
        "passes through the box — there is no side door in which a controller renders content that the box has not "
        "seen, which is exactly the property missing in the incidents described in Section 1.1."
    )

    h2("3.2 Low-Level Design (Detailed Design)")
    para(
        "Figure 2 opens the box. One entry point, run_analysis, drives two tracks that are kept deliberately "
        "asymmetric, and a fusion stage that combines them."
    )
    figure("fig2_lld.png", "Figure 2: Low-level design — modules, tracks and their data flow.")
    para(
        "Track A is the deterministic lane (green, top). Authorization records the authority-approved bytes and "
        "their SHA-256 digest, and the registry persists that record in a ledger whose blocks are Ed25519-signed and "
        "hash-linked. Verification recomputes the digest of the arriving bytes and compares it with the stored one, "
        "producing match, mismatch or unknown-content. The decision engine consumes that result first: a mismatch is "
        "terminal and returns block plus safe_fallback immediately. No model is consulted on this path, which is what "
        "makes false negatives structurally impossible rather than statistically unlikely."
    )
    para(
        "Track B is the probabilistic lane (blue, middle). The ingestion module keeps a per-device event store "
        "behind the MQTT subscription; the feature engine collapses the last 300 seconds of activity into the "
        "seven-element vector of Table 2; the isolation forest converts that vector into an anomaly assessment in "
        "[0, 1]; the SHAP explainer decomposes the same assessment into signed per-feature contributions; and the "
        "risk module converts rule signals plus the model assessment into a 0–100 score with a level. Track B never "
        "gates integrity — it only refines what happens when Track A has already said the content is authentic."
    )
    para(
        "The two tracks meet in the fusion stage (amber, bottom): risk is combined with the verification result by "
        "the decision rules of Section 4.1, and the resulting command is handed to three sinks simultaneously — the "
        "audit store (append-only row), the MQTT orchestrator (command for the physical sign), and the fallback "
        "module (the safe text that replaces the rejected payload). The web module exposes the same objects over "
        "REST, SSE and WebSocket so that the dashboard and the audit endpoint cannot show a different verdict from "
        "the one the hardware received."
    )
    h3("Deployment view")
    figure("fig3_architecture.png",
           "Figure 3: Deployment architecture — edge, broker and server planes on one LAN.")
    para(
        "Figure 3 separates the deployment into three planes. The edge plane holds the USB monitor, the board "
        "watcher (which detects a serial device on insertion and clears its cached state when it disappears), the "
        "simulators, and the NodeMCU ESP-12E node. The broker plane is a single Mosquitto instance reachable on all "
        "interfaces at port 1883 carrying three topics: signguard/events, signguard/content and signguard/commands. "
        "The server plane hosts FastAPI on port 8000 — the API surface, the shared pipeline, the SQLite audit store "
        "and the ledger — together with the browser-facing pages and the WebSocket stream. The only ports SignGuard "
        "occupies are 8000 and 1883."
    )
    h3("Interaction view")
    figure("fig4_sequence.png",
           "Figure 4: Sequence diagram of the malicious-USB attack, from insertion to physical fallback.")
    para(
        "Figure 4 traces one complete incident. The stick is inserted (1), the edge monitor publishes the "
        "unauthorised-USB event and the payload (2), the broker fans both to the server (3), and verification "
        "recomputes the digest against the signed record (4). The mismatch comes back (5) — this is the Track A gate, "
        "and it is the only step that decides authenticity. In parallel the model and explainer quantify the context "
        "(6), the audit row is appended (7), the command is published (8), the edge node receives it (9) and drives "
        "the LCD, red LED and buzzer (10) while the web sign shows the safe fallback text (11). When the stick is "
        "removed the watcher clears its cached device state (12), so a later insertion is judged on fresh evidence "
        "rather than on a stale allow-list entry."
    )
    h3("Decision view")
    figure("fig5_decision_flow.png",
           "Figure 5: Decision flow — the hash gate is evaluated first; the model only refines a match.")
    para(
        "Figure 5 is the operational contract of the system and is the drawing that a duty manager can be taught in "
        "one minute. If the digest does not match an authorised record, execution stops at the red box: block, safe "
        "fallback, +40 risk points, and the model is not consulted. If the digest matches, Track B computes the risk "
        "and the single threshold test at 50 decides between rendering and blocking, while the critical threshold at "
        "80 additionally isolates the update channel. Every terminal state writes an audit row and publishes exactly "
        "one MQTT command."
    )


# --------------------------------------------------------------------------- #
# 4. System implementation
# --------------------------------------------------------------------------- #
def section_4() -> None:
    h1("4. System Implementation")

    h2("4.1 Algorithms (Followed, Proposed or Altered)")
    h3("A1 — Content authorisation (followed: signed publication, altered to be display-local)")
    code(
        "INPUT : bytes B, content_id C, device_id D\n"
        "OUTPUT: ContentRecord {C, D, sha256(B), signature, authorised_at}\n"
        "1  h  <- SHA256(B)\n"
        "2  key<- Ed25519 authority private key (never leaves the authority host)\n"
        "3  s  <- Sign(key, h || C || D)\n"
        "4  AppendBlock(ledger, {h, C, D, s, prev_hash})   # hash-linked\n"
        "5  RETURN record"
    )
    h3("A2 — Content verification (the integrity gate)")
    code(
        "INPUT : arriving bytes B', content_id C, device_id D\n"
        "OUTPUT: VerificationResult {match, action, reason}\n"
        "1  r  <- Lookup(C, D)                       # None if never authorised\n"
        "2  IF r IS NULL            -> (False, block, \"unknown_content\")\n"
        "3  IF VerifyChain() FAILS  -> (False, block, \"ledger_invalid\")\n"
        "4  h' <- SHA256(B')\n"
        "5  IF h' != r.sha256       -> (False, block, \"hash_mismatch\")\n"
        "6  RETURN (True, render, \"hash_match\")"
    )
    para(
        "The gate is monotone: no branch of A2 can return 'render' for bytes whose digest is absent from the ledger, "
        "and step 3 means a corrupted authorisation history fails closed rather than open.",
        before=4,
    )
    h3("A3 — Context assessment (proposed: isolation forest over windowed state)")
    code(
        "INPUT : device_id D, window W = last 300 s of events\n"
        "OUTPUT: AnomalyResult {anomaly_score a in [0,1]}, top SHAP factors\n"
        "1  x <- build_feature_vector(D, W)          # the 7 columns of Table 2\n"
        "2  a <- IsolationForest.predict_proba(x)    # trained unsupervised, no labels needed\n"
        "3  phi <- TreeExplainer(model).shap_values(x)\n"
        "4  order phi descending by |impact|\n"
        "5  RETURN a, phi[0..k]"
    )
    h3("A4 — Risk fusion and decision (proposed, frozen weights)")
    code(
        "INPUT : verification V, event set E, anomaly a, device D\n"
        "OUTPUT: Decision {decision, recommended_action, reasons[]}\n"
        "1  IF V.match == False            -> BLOCK + safe_fallback(reason=\"hash_mismatch\")  # terminal\n"
        "2  R <- 40*hash_mismatch + 20*unauthorized_usb + 15*default_credential_attempt\n"
        "           + 10*wireless_anomaly + 15*a            , capped at 100\n"
        "3  IF R >= 80 -> ISOLATE + escalate(reason=\"critical_risk\")\n"
        "4  IF R >= 50 -> BLOCK + safe_fallback(reason=\"elevated_risk\")\n"
        "5  RETURN RENDER(reason=\"hash_match\", \"risk_acceptable\")"
    )
    para(
        "Line 1 is the whole safety argument of the project: the deterministic verdict is evaluated before, and "
        "independently of, line 2. The weights in line 2 are frozen constants rather than learned parameters, so a "
        "reviewer can predict the score of any event combination by hand — a property that matters when the score "
        "appears as evidence after an incident.",
        before=4,
    )

    h2("4.2 Mathematical Model")
    para("Content integrity is a set equality over digest space. For arriving bytes B′ with content identifier C:")
    para("h′ = SHA-256(B′)          match(C, B′) ≡ [ h′ = H(C) ∧ C ∈ A ]", align="center", size=11, bold=True)
    para(
        "where A is the set of content identifiers authorised on the Ed25519-signed, hash-linked ledger. The verdict "
        "function is then a piecewise map from (match, risk) to a command:",
        before=4,
    )
    para("D(V, R) =  block ,  if V = mismatch      (R is not evaluated)",
         align="center", size=11, bold=True, after=2)
    para("          isolate,  if V = match ∧ R ≥ 80", align="center", size=11, bold=True, after=2)
    para("          block ,  if V = match ∧ 50 ≤ R < 80", align="center", size=11, bold=True, after=2)
    para("          render ,  if V = match ∧ R < 50", align="center", size=11, bold=True, after=8)
    para("The risk score is a capped linear fusion of rule signals and the model assessment:")
    para(
        "R = min ( 100,  40·m  +  20·u  +  15·c  +  10·w  +  15·a )",
        align="center", size=11, bold=True, after=6,
    )
    table(
        ["Term", "Weight", "Meaning", "Source"],
        [["m", "40", "content_hash_mismatch present in the window", "Track A (deterministic)"],
         ["u", "20", "unauthorised USB insertion observed", "Rule signal"],
         ["c", "15", "default-credential attempt observed", "Rule signal"],
         ["w", "10", "unscheduled wireless source observed", "Rule signal"],
         ["a", "15 × a", "isolation-forest anomaly assessment a ∈ [0, 1]", "Track B (probabilistic)"],
         ["—", "≤ 100", "cap: the score can never exceed 100", "Score ceiling"]],
        widths=[0.5, 0.7, 3.3, 1.9],
        caption="Table 6: Frozen risk-fusion weights (Section 9 defaults of the specification).",
    )
    para(
        "Levels follow the same cut points as the decision engine: low ≤ 24, medium ≤ 49, high ≤ 79, critical ≥ 80, "
        "with the operational thresholds at 50 (render versus block) and 80 (isolate). The explanation model is the "
        "standard additive decomposition of the model output f(x) around its expected value:",
        before=4,
    )
    para("f(x) − E[f(x)] = Σ φᵢ   with   φ₀ = E[f(x)]", align="center", size=11, bold=True, after=6)
    para(
        "where φᵢ is the SHAP contribution of feature i (one of the seven columns of Table 2). Because the explainer "
        "and the scorer both import the same frozen column order, the φᵢ reported on the dashboard refer to exactly "
        "the same inputs the model consumed. Finally, the end-to-end latency of one decision decomposes as"
    )
    para("T = T_ingest + T_verify + T_model + T_shap + T_fuse + T_audit + T_mqtt",
         align="center", size=11, bold=True, after=6)
    para(
        "which Section 5.2 measures directly: the sum of the first five terms is the pipeline time, and adding the "
        "audit write plus the MQTT round trip gives the time from arrival to physical fallback."
    )

    h2("4.3 Module Development Code")
    h3("The integrity gate")
    code(
        "def verify_content(registry, update: ContentUpdate) -> VerificationResult:\n"
        "    record = registry.get(update.content_id, update.device_id)\n"
        "    if record is None:                       # never authorised\n"
        "        return VerificationResult(match=False, action=\"block\",\n"
        "                                   reason=\"unknown_content\")\n"
        "    digest = sha256(update.content_bytes).hexdigest()\n"
        "    match = digest == record.sha256\n"
        "    return VerificationResult(\n"
        "        match=match,\n"
        "        action=\"render\" if match else \"block\",\n"
        "        authorized_hash=record.sha256,\n"
        "    )"
    )
    h3("The decision rules (the only place a command is produced)")
    code(
        "RISK_THRESHOLD    = 50    # match + risk below this -> render\n"
        "CRITICAL_THRESHOLD= 80    # risk at/above this     -> isolate + escalate\n"
        "\n"
        "def decide(device_id, verification, risk=None) -> Decision:\n"
        "    # Track A gate: hash mismatch is terminal, ML is irrelevant here.\n"
        "    if verification is not None and not verification.match:\n"
        "        return Decision(device_id=device_id, decision=\"block\",\n"
        "                        recommended_action=CommandType.safe_fallback,\n"
        "                        reasons=[\"hash_mismatch\"])\n"
        "    score = risk.score if risk is not None else 0\n"
        "    if score >= CRITICAL_THRESHOLD:\n"
        "        return Decision(device_id=device_id, decision=\"isolate\",\n"
        "                        recommended_action=CommandType.isolate, reasons=[\"critical_risk\"])\n"
        "    if score >= RISK_THRESHOLD:\n"
        "        return Decision(device_id=device_id, decision=\"block\",\n"
        "                        recommended_action=CommandType.safe_fallback, reasons=[\"elevated_risk\"])\n"
        "    return Decision(device_id=device_id, decision=\"render\",\n"
        "                    recommended_action=CommandType.render,\n"
        "                    reasons=[\"hash_match\", \"risk_acceptable\"])"
    )
    h3("Frozen weights and level cut points")
    code(
        "WEIGHTS = {\"content_hash_mismatch\": 40, \"unauthorized_usb\": 20,\n"
        "           \"default_credential_attempt\": 15, \"wireless_anomaly\": 10,\n"
        "           \"ai_anomaly\": 15}            # scaled by anomaly_score\n"
        "_LOW_MAX, _MEDIUM_MAX, _HIGH_MAX = 24, 49, 79      # >= 80 is critical"
    )
    h3("Single column order shared by model and explainer")
    code(
        "FEATURE_ORDER: tuple[str, ...] = (\n"
        "    \"failed_logins_5min\", \"unknown_usb_detected\", \"wireless_anomaly\",\n"
        "    \"content_hash_mismatch\", \"events_per_minute\",\n"
        "    \"time_since_authorized_update\", \"device_trust_score\",\n"
        ")\n"
        "WINDOW_SECONDS = 300   # the 5-minute feature window"
    )
    h3("Physical enforcement at the edge (MQTT command -> indicators)")
    code(
        "import network, time\n"
        "from machine import Pin, I2C\n"
        "import lcd_i2c                                   # 16x2 backpack @ 0x27\n"
        "\n"
        "def on_message(topic, msg):\n"
        "    cmd = ujson.loads(msg).get(\"command\")\n"
        "    if cmd == \"render\":           green.on();  red.off(); buzzer.off();\n"
        "                                     lcd.show(l1, l2)\n"
        "    elif cmd == \"safe_fallback\":  green.off(); red.on();\n"
        "                                     lcd.show(\"SIGN GUARDED\", \"SAFE MODE\")\n"
        "    elif cmd == \"isolate\":        green.off(); red.on(); alarm(1.2)\n"
        "                                     lcd.show(\"ISOLATED\", \"UPDATES BLOCKED\")"
    )
    h3("Board detection on the operator laptop (insert / remove)")
    code(
        "# usb_demo/laptop/board_watcher.py  (stdlib only)\n"
        "def poll_once() -> dict:            # 2 s period, no polling back-door\n"
        "    ports = list(serial.tools.comports())\n"
        "    fresh = {p.device for p in ports if not _is_bluetooth_baseline(p)}\n"
        "    added, removed = fresh - known, known - fresh\n"
        "    for dev in sorted(added):   log(\"INSERT\", dev, friendly_name(dev))\n"
        "    for dev in sorted(removed): cache.pop(dev, None)   # stored state cleared\n"
        "    known = fresh                              # baseline survives re-plug"
    )

    h2("4.4 Test Cases")
    para(
        "The suite is executed with python -m pytest -q and currently reports 46 passed across seven modules. The "
        "cases below are the representative ones for each requirement; the remainder follow the same pattern."
    )
    table(
        ["#", "Test case", "Input / stimulus", "Expected result", "Actual"],
        [["1", "test_authorize_then_analyze_match_renders",
          "Authorise content, POST /analyze with identical bytes",
          "decision=render, reasons contain hash_match", "render (pass)"],
         ["2", "test_analyze_mismatch_blocks",
          "POST /analyze with altered bytes for an authorised id",
          "decision=block, action=safe_fallback", "block (pass)"],
         ["3", "test_unknown_content_blocks",
          "Content id never authorised", "block, reason=unknown_content", "block (pass)"],
         ["4", "test_tampered_content_blocks",
          "Ledger record present, payload bytes modified", "block; model not consulted", "block (pass)"],
         ["5", "test_clean_situation_is_low_risk",
          "Feature vector with no hostile events", "risk ≤ 24 (low)", "risk=1, low (pass)"],
         ["6", "test_hash_mismatch_weight",
          "Isolated mismatch signal", "+40 points on the score", "+40 (pass)"],
         ["7", "test_decision_blocks_on_elevated_risk_even_with_match",
          "match=True, risk=50..79", "block with reason elevated_risk", "block (pass)"],
         ["8", "test_decision_isolates_on_critical_risk",
          "match=True, risk ≥ 80", "decision=isolate, action=isolate", "isolate (pass)"],
         ["9", "test_ai_anomaly_is_scaled",
          "anomaly_score a ∈ [0,1] injected", "ai term = round(15·a)", "scaled (pass)"],
         ["10", "test_score_caps_at_100",
          "All signals hostile simultaneously", "score == 100, never larger", "100 (pass)"],
         ["11", "test_analyze_populates_xai_from_events",
          "Device with a populated event window", "xai_explanation present with factors", "populated (pass)"],
         ["12", "test_store_is_append_only_and_newest_first",
          "Three inserts, then read", "No update/delete; newest first", "verified (pass)"],
         ["13", "test_analyze_writes_audit_row_that_audit_endpoint_returns",
          "One analysis request, then GET /audit", "Same row visible over HTTP", "matched (pass)"],
         ["14", "test_signature_is_valid_and_chain_verifiable",
          "Authorise, then GET /chain/verify", "valid=true, blocks appended", "valid (pass)"],
         ["15", "test_manual_default_credentials_are_flagged_and_content_blocked",
          "Vendor-default credentials on the panel",
          "credential flagged, content blocked", "blocked (pass)"],
         ["16", "test_trigger_with_signguard_blocks_and_works_without_broker",
          "Attack scenario with the broker unavailable",
          "Still blocks; degrades without MQTT", "blocked (pass)"],
         ["17", "test_scenarios_endpoint_lists_buttons_in_order",
          "GET /demo/scenarios", "Four scenarios in fixed order", "4 listed (pass)"],
         ["18", "test_dashboard_page_serves", "GET /", "200 with dashboard markup", "200 (pass)"],
         ["19", "test_health", "GET /health", '{"status":"ok"}', "ok (pass)"],
         ["20", "test_record_handles_null_tracks",
          "Audit row without model or events", "Row written, nulls tolerated", "written (pass)"]],
        widths=[0.3, 2.0, 1.7, 1.5, 0.9],
        size=8.2,
        caption="Table 7: Representative test cases (20 of 46) with inputs, expectations and observed results.",
    )
    figure("fig10_tests.png", "Figure 10: Distribution of the 46 automated test cases across modules.")
    para(
        "Coverage spans the two tracks independently (test_track_a, test_track_b), the fusion mathematics "
        "(test_scoring), the ledger (test_secure_chain), persistence (test_audit), the demo surfaces (test_demo) and "
        "the HTTP contract (test_api). The negative tests outnumber the positive ones, which is intentional: for an "
        "integrity gate the expensive mistake is a false negative, so the suite spends most of its assertions proving "
        "that tampered, unknown or unauthorised input cannot reach a render verdict."
    )


# --------------------------------------------------------------------------- #
# 5. Results and discussion
# --------------------------------------------------------------------------- #
def _sc(sid: str) -> dict:
    return next(r for r in M["scenarios"] if r["id"] == sid)


def section_5() -> None:
    h1("5. Results and Discussion")

    h2("5.1 Implementation Results")
    para(
        "The system was executed end to end: run_demo.py starts the Mosquitto broker on port 1883 and the FastAPI "
        "decision service on port 8000, the four scenarios inject real content and real events through the broker, "
        "and the verdicts reported below were produced by the production pipeline (the same code the REST and MQTT "
        "entry points call), not by a replay or a mock. Every row of Table 8 is a measured run."
    )
    rows = []
    labels = {"baseline": "Baseline (authority-approved content)",
              "usb": "Malicious USB replacement",
              "wireless": "Rogue wireless update",
              "credential": "Default-credential panel attack"}
    for sid in ("baseline", "usb", "wireless", "credential"):
        r = _sc(sid)
        rows.append([labels[sid],
                     "MATCH" if r["verified_match"] else "MISMATCH",
                     f"{r['risk']}/100 ({r['level']})",
                     r["decision"].upper(),
                     r["command"],
                     ", ".join(r["reasons"])])
    table(
        ["Scenario", "Verification", "Risk score", "Decision", "Command sent to sign", "Reasons"],
        rows,
        widths=[1.9, 0.85, 1.1, 0.7, 1.0, 1.05],
        size=8.6,
        caption="Table 8: Measured end-to-end results for the four attack scenarios.",
    )
    figure("fig6_risk.png", "Figure 6: Risk score of each scenario against the frozen level thresholds.")
    figure("fig9_outcomes.png",
           "Figure 9: Verification outcome versus final decision — four scenarios, four correct verdicts.")
    para(
        "The baseline renders with a risk of 1/100 and the reasons hash_match and risk_acceptable; the three "
        "attacks are blocked with reasons hash_mismatch at risk 71, 66 and 62 respectively. The important property is "
        "not the numbers themselves but their ordering: the mismatch was detected before any risk score existed, so "
        "even a hypothetical failure of the model could not have let the tampered payload through. Detection on this "
        "corpus is 3/3 attacks blocked with 0 false positives on the genuine update."
    )

    h2("5.2 Metrics")
    p = M["pipeline_latency_ms"]
    h = M["http_latency_ms"]
    table(
        ["Metric", "Value", "How it was measured"],
        [["Automated test pass rate", "46 / 46 (100 %)", "python -m pytest -q"],
         ["Attack detection rate", "3 / 3 (100 %)", "Scenarios of Table 8 blocked"],
         ["False-positive rate", "0 / 1 genuine update", "Baseline rendered"],
         ["Pipeline latency, content only",
          f"{h['analyze_keepalive_ipv4']['median']:.1f} ms median "
          f"(p95 {h['analyze_keepalive_ipv4']['p95']:.1f} ms, n=50)",
          "POST /analyze over keep-alive HTTP on 127.0.0.1"],
         ["Pipeline latency, with events + SHAP",
          f"{p['usb']['mean']:.1f} ms mean (n=40 per scenario)",
          "run_analysis() timed in-process for all four scenarios"],
         ["Transport cost of a new connection",
          f"{h['analyze_fresh_ipv4']['median']:.1f} ms median (IPv4 literal, n=15)",
          "Fresh TCP connection per request"],
         ["Environment artefact on localhost",
          f"{h['analyze_fresh_localhost']['median']:.0f} ms median",
          "Hostname 'localhost' resolves to ::1 first — see Section 5.5"],
         ["Risk score range observed", "1 – 71 of 100", "Table 8"],
         ["Audit rows persisted", f"{M['audit_rows']} (file-backed SQLite)",
          "data/audit.db, survives process restart"],
         ["Ledger integrity", "chain valid, 55 blocks", "GET /chain/verify"],
         ["Feature vector", "7 dimensions × 300 s window", "FEATURE_ORDER"],
         ["SHAP factors reported per verdict", "5 (ranked, signed)", "TreeExplainer on the same vector"]],
        widths=[1.85, 1.85, 2.7],
        size=8.6,
        caption="Table 9: Operational metrics of the implemented system.",
    )
    figure("fig7_latency.png",
           "Figure 7: Measured decision latency — explainable inference dominates, transport is negligible.")

    h2("5.3 Results in Tables and Graphs")
    para(
        "Table 10 lists every decision together with the explanation the system attached to it, and Figure 8 plots "
        "the SHAP decomposition for the highest-scoring attack. The tabulated values are the source of every graph in "
        "this section."
    )
    rows = []
    for sid in ("baseline", "usb", "wireless", "credential"):
        r = _sc(sid)
        top = r["shap"][0]
        rows.append([labels[sid].split(" (")[0],
                     r["decision"].upper(),
                     str(r["risk"]),
                     r["level"],
                     top["name"].replace("_", " "),
                     f"{top['impact']:+.2f}"])
    table(
        ["Scenario", "Decision", "Risk", "Level", "Dominant SHAP factor", "Impact"],
        rows,
        widths=[2.0, 0.8, 0.6, 0.7, 1.75, 0.65],
        size=8.8,
        caption="Table 10: Decision and dominant explanation factor per scenario.",
    )
    figure("fig8_shap.png",
           "Figure 8: SHAP decomposition of the malicious-USB assessment (risk 71/100).")
    para(
        "The explanations are consistent with the threat model rather than merely numerically plausible: in the "
        "baseline it is the staleness of the last authorised update that pushes the assessment (impact +2.10) while "
        "device trust and login history pull it down, whereas in all three attacks device_trust_score is the largest "
        "positive driver (+3.25 to +3.67) followed by the specific hostile signal — unknown_usb_detected (+2.22) for "
        "the USB case, wireless_anomaly (+2.51) for the rogue radio, failed_logins_5min (+1.52) for the credential "
        "attack. An operator reading factor three of any verdict can name the behaviour that caused it."
    )

    h2("5.4 Mapping with Problem Statement and Existing Systems")
    table(
        ["Requirement", "Implemented in", "Evidence", "Observed result"],
        [["R1  Deterministic authenticity", "authorization + chain registry + verification (Track A)",
          "Tests 1, 3, 14; Table 8", "MATCH only for authorised bytes; chain valid (55 blocks)"],
         ["R2  Tampering is terminal", "decide() line 1 — gate precedes fusion",
          "Tests 2, 4, 7; Figure 5", "3/3 attacks blocked with reasons=hash_mismatch"],
         ["R3  Context-aware risk", "scoring module with frozen weights + isolation forest",
          "Tests 6, 8, 9, 10; Figure 6", "Risk 1 (genuine) vs 62–71 (attacks)"],
         ["R4  Explainable verdicts", "xai module (SHAP TreeExplainer) inside the decision object",
          "Test 11; Figure 8; Table 10", "5 ranked, signed factors on every verdict"],
         ["R5  Non-repudiable audit", "SQLite audit store (file-backed) + ledger + /chain/verify",
          "Tests 12, 13, 14; Table 9", "168 rows persisted; verification survives restart"],
         ["R6  Real-time + physical enforcement",
          "run_analysis pipeline + MQTT orchestrator + ESP-12E node",
          "Figure 7; Figures 3, 4", "21.7 ms processing; LCD/LED/buzzer command on :1883"],
         ["Gap from Section 2.1 — verdict-bound explanation",
          "SHAP factors carried inside the Decision object",
          "Table 10", "Explanation travels with the command, not a separate report"],
         ["Gap from Section 2.1 — device-side enforcement",
          "edge node renders authorised text or safe fallback only",
          "Figure 4 steps 9–10", "Sign state mirrors the decision even if the dashboard is closed"]],
        widths=[1.7, 1.8, 1.3, 2.2],
        size=8.4,
        caption="Table 11: Mapping of each requirement to its implementation and measured evidence.",
    )

    h2("5.5 Discussions")
    h3("(a) Why the ordering of the two tracks is the real result")
    para(
        "The most common failure mode in ML-mediated security controls is a model that can be talked out of a "
        "verdict an algorithm had already reached. Here the ordering makes that impossible: the digest comparison is "
        "a separate function with its own tests, and the decision engine returns before touching the risk score when "
        "the comparison fails. The measured corollary is visible in Table 8 — every blocked row reports "
        "reasons=hash_mismatch and nothing else, i.e. the fusion stage did not participate in those verdicts at all."
    )
    h3("(b) The explanations are stable across attacks")
    para(
        "device_trust_score dominates all three attack explanations while time_since_authorized_update dominates the "
        "genuine one. Stability of this kind is what makes an explanation trustworthy: if the ranking changed "
        "arbitrarily between near-identical inputs, the operator would learn to ignore it. Because the model is an "
        "isolation forest over seven fixed columns rather than a high-dimensional embedding, the ranking is also "
        "legible to a non-specialist without additional tooling."
    )
    h3("(c) A measured deployment pitfall: name resolution costs two seconds")
    para(
        "The first latency measurements of the service returned a suspiciously constant 2040 ms for every request. "
        "Isolating the effect showed that /health was exactly as slow as /analyze, that a keep-alive request on the "
        "same connection took 0.5 ms, and that the hostname 'localhost' resolves to ::1 on this host while the ASGI "
        "server binds IPv4 only: each new connection therefore waits roughly two seconds before falling back to "
        "127.0.0.1. The processing path was never the slow part. The practical guidance recorded here is to address "
        "the service by an IPv4 literal (or to bind a dual-stack listener) and to measure a service under keep-alive, "
        "otherwise a purely environmental artefact of 2 s is attributed to the decision engine — Figure 7 shows both "
        "numbers side by side precisely so that the distinction is not lost."
    )
    h3("(d) Limitations")
    for b in [
        "The MQTT broker is reachable on all interfaces without transport security, which is acceptable on an "
        "isolated demonstration LAN but must be replaced by TLS with client certificates before any operational "
        "deployment.",
        "The feature window lives in memory: a restart of the service resets per-device counters, so a short-lived "
        "window of hostile activity could be lost across a crash. The audit trail and the ledger are file-backed and "
        "do survive restarts; the event window does not.",
        "The edge node acts on the command it receives rather than re-verifying the digest itself, so it trusts the "
        "broker. Pushing verification into the firmware (SHA-256 over the payload on the ESP-12E) would remove that "
        "trust assumption and is the next architectural step.",
        "Evaluation uses four scenarios over a synthetic corpus; no labelled dataset of real signage incidents "
        "exists to quantify generalisation (Section 1.4).",
        "Physical insertion detection was validated with simulated COM-port transitions; a real board was not "
        "attached during the measurements reported here.",
    ]:
        bullet(b)


# --------------------------------------------------------------------------- #
# 6. Conclusion
# --------------------------------------------------------------------------- #
def section_6() -> None:
    h1("6. Conclusion and Future Developments")
    para(
        "SignGuard AI answers the problem statement of Section 1.2 with an implemented, tested system rather than a "
        "proposal. Content is authorised once by the transport authority, recorded on a hash-linked Ed25519-signed "
        "ledger, and compared by digest immediately before rendering; a mismatch ends the decision, and no model can "
        "reopen it. Around that gate, an isolation forest over a seven-element, five-minute feature window quantifies "
        "the attack context, the frozen fusion weights turn rule signals and the model assessment into a 0–100 risk "
        "score, and three thresholds map the result onto render, block or isolate. Every verdict carries its ranked "
        "SHAP factors, is appended to a file-backed audit store that survives restarts, and reaches the physical sign "
        "over MQTT as LCD text, a green/red indication and a buzzer."
    )
    para(
        "The evaluation shows the design behaving as intended: 46 of 46 automated tests pass; the genuine update "
        "renders at risk 1/100 while the three attacks — malicious USB, rogue wireless, default-credential panel — "
        "are blocked at 71, 66 and 62; the verification and the explanation agree on why; a full analysis including "
        "SHAP costs 21.7 ms and a content-only request 3.3 ms, both far inside the budget of a display that updates "
        "every few seconds; and the ledger re-verifies at 55 blocks after the process was restarted. The incidents in "
        "Section 1.1 were successful precisely because nothing like this gate existed between the USB stick and the "
        "screen."
    )
    para("Future developments, in decreasing order of value:", before=6)
    for b in [
        "Move verification to the edge: compute SHA-256 on the ESP-12E itself and make the node re-check the payload "
        "against the authorised digest, so the sign no longer has to trust the broker.",
        "Secure the bus: TLS with per-device client certificates on the MQTT listener and short-lived credentials "
        "per node, plus rotation of the authority key.",
        "Persist the feature window with the audit store so that counters survive a crash, and add a rolling "
        "retraining schedule for the isolation forest with drift monitoring on the anomaly distribution.",
        "Wire the existing Ethereum prototype (chain_eth contracts with their Truffle tests) to the authorisation "
        "endpoint as an alternative ledger backend, keeping the current hash-linked chain as the local, offline "
        "source of truth.",
        "Fleet-level learning: aggregate per-device trust scores across signs so that a device newly exposed to an "
        "unknown stick is treated cautiously everywhere, without centralising raw events.",
        "Extend the board watcher from detection to enforced response — for example, suspending rendering for a "
        "device whose stored state was cleared on removal — and validate insertion/removal against physical hardware "
        "in the next iteration.",
    ]:
        bullet(b)


# --------------------------------------------------------------------------- #
# 7. References (Vancouver)
# --------------------------------------------------------------------------- #
def section_7() -> None:
    h1("7. References")
    refs = [
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
    for i, r in enumerate(refs, start=1):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.left_indent = Inches(0.45)
        pf.first_line_indent = Inches(-0.45)
        pf.space_after = Pt(6)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"{i}. {r}")
        run.font.size = Pt(10.5)
        run.font.name = "Tahoma"


# --------------------------------------------------------------------------- #
# fill the submitted template's own placeholders
# --------------------------------------------------------------------------- #
def _set_para_text(par, text: str, *, size: float | None = None, bold: bool | None = None) -> None:
    """Replace a paragraph's text, keeping the first run's formatting."""
    runs = par.runs
    if not runs:
        runs = [par.add_run()]
    runs[0].text = text
    for r in runs[1:]:
        r._element.getparent().remove(r._element)
    if size is not None:
        runs[0].font.size = Pt(size)
    if bold is not None:
        runs[0].bold = bold


def _set_cell_text(cell, text: str) -> None:
    _set_para_text(cell.paragraphs[0], text)
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def fill_template() -> None:
    p = doc.paragraphs
    _set_para_text(p[7], TITLE, size=16, bold=True)   # <TITLE OF THE PROJECT-font size 16>
    _set_para_text(p[33], TITLE)                      # < Project Title >
    t0 = doc.tables[0]
    _set_cell_text(t0.rows[0].cells[0], "TEAM Name :  <TEAM NAME>")
    _set_cell_text(t0.rows[2].cells[0], "Project Title :  " + TITLE)
    # the evaluator sign-off sheet repeats merged cells — touch each cell once.
    # every proxy is kept alive in the list: lxml recycles id() values, and a
    # recycled id silently skips a real cell.
    seen: list = []
    for row in doc.tables[2].rows:
        for cell in row.cells:
            tc = cell._tc
            if any(tc is s for s in seen):
                continue
            seen.append(tc)
            txt = cell.text.strip()
            if txt == "Title:":
                _set_cell_text(cell, "Title :  " + TITLE)
            elif txt == "Team Name":
                _set_cell_text(cell, "Team Name :  <TEAM NAME>")
            elif txt == "Project Team":
                _set_cell_text(cell, "Project Team :  <TEAM NAME>")


def relocate_before_signoff_sheet() -> None:
    """Move everything built after the template was loaded in front of the sign-off table."""
    body = doc.element.body
    anchor = doc.tables[2]._tbl
    added = [el for el in list(body.iterchildren()) if id(el) not in _TEMPLATE_BODY]
    for el in added:
        anchor.addprevious(el)


# =========================================================================== #
if __name__ == "__main__":
    fill_template()
    section_1()
    pagebreak()
    section_2()
    pagebreak()
    section_3()
    pagebreak()
    section_4()
    pagebreak()
    section_5()
    pagebreak()
    section_6()
    pagebreak()
    section_7()
    pagebreak()          # keep the evaluator sign-off sheet on its own page
    relocate_before_signoff_sheet()
    # the submission file may be open in Word, which locks it
    for target in (OUT, OUT.with_name(OUT.stem + "_v2.docx")):
        try:
            doc.save(target)
        except PermissionError:
            print(f"! {target.name} is open in another program - trying the next name")
            continue
        print("saved", target)
        break
    else:
        raise SystemExit("close the open document and re-run make_report.py")
