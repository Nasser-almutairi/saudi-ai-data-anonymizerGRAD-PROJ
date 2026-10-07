# 🛡️ Saudi AI-Assisted Data Anonymization System

A graduation-project **MVP prototype**: a local web app that helps Saudi organisations anonymize sensitive datasets
(CSV / Excel) *before* sharing them with developers, analysts or AI systems.
Built on **Microsoft Presidio**, extended with a **Saudi / Arabic privacy layer** and a simple **privacy-vs-utility evaluation**.

> Prototype only. It is **not** an enterprise product, **not** legal advice, and does **not** guarantee PDPL compliance.

---

## 1. The problem & why anonymization matters
Organisations increasingly share data with external AI vendors, outsourced developers and analysts. Customer files often contain
National IDs, Iqama numbers, mobile numbers, IBANs, e-mails and Arabic names. Sharing them raw creates privacy, security and
regulatory risk (e.g. under the Saudi Personal Data Protection Law). Existing tools are built mainly for English/Western data
formats and miss Saudi identifiers and Arabic context (e.g. a column called “رقم الهوية”).

## 2. What Microsoft Presidio does – and what we added
| Microsoft Presidio (foundation) | **Our contribution** |
|---|---|
| Pattern recognizers (regex detection) | **Saudi custom recognizers** on top of Presidio's `PatternRecognizer` (ID / Iqama, mobile, IBAN, e-mail) |
| Generic anonymizer operators | In-text masking through Presidio's `AnonymizerEngine` with **custom Saudi masking operators** |
| English-centric context | **Arabic contextual detection**: Arabic column names, phrases like “رقم الهوية:”, Arabic-Indic digits (٠١٢…) |
| – | **Validation logic**: Saudi ID checksum, IBAN mod-97 → confidence, not just pattern matching |
| – | **Direct vs. indirect identifier** classification (user-confirmable) |
| – | **Purpose profiles**: AI / External · Developer Testing · Internal Analytics |
| – | **Prototype Re-identification Risk** score (before/after) |
| – | **Data Utility** score → privacy–utility trade-off |
| – | **Saudi Privacy Assessment Report** + explainable detections |

We do not claim each idea is new; the contribution is integrating and adapting them into a Saudi / Arabic-focused workflow.

## 3. Supported Saudi / Arabic detections
| Entity | How it is detected |
|---|---|
| Saudi National ID / Iqama | 10 digits starting with 1 (citizen) or 2 (resident) + Luhn-style checksum + context (“رقم الهوية”, “الإقامة”, `national_id` …) |
| Saudi mobile | `05XXXXXXXX`, `+9665…`, `009665…`, with spaces/dashes, Arabic digits |
| Saudi IBAN | `SA` + 22 characters, ISO mod-97 validation, spaced or compact |
| E-mail | regex + context |
| Arabic / Saudi personal names | name shape + Saudi name lexicon + particles (بن، آل، bin, Al) + column name (“الاسم”, “اسم العميل”) |
| Arabic / Saudi address | keywords (حي، شارع، طريق، ص.ب …) + column name (“العنوان”) |
| Indirect identifiers (suggested) | age, date of birth, city, district, gender, job, salary, nationality – from column names / values; user confirms |

**Context-aware example:** a random 10-digit number scores ≈ 47 % (not flagged). The same number in a column named
`رقم الهوية`, or next to “رقم الهوية:” inside a free-text note, scores ≈ 95–97 %.
Each detection returns *entity, column, confidence, risk level and the reasons*.

## 4. Anonymization techniques
| Method | Example |
|---|---|
| Masking | `0551234567` → `055****567` |
| Suppression | National ID → `[REMOVED]` |
| Replacement | `أحمد القحطاني` → `Person_001` (or a realistic fake name for the Developer profile) |
| Generalization | Age `23` → `20–25`, Salary `8,700` → `8,000–9,000`, City → Saudi region |
| Hashing | Customer ID → `H_3fa9c1d2e7` (salted SHA-256, random per-run salt) |

**Profiles:** *AI / External* = stronger (suppress IDs/IBANs, wide bins, city→region) · *Developer Testing* = format-preserving fakes
(valid-looking IDs, IBANs, phones, names) · *Internal Analytics* = narrower bins, hashed linkable IDs, common categories kept.

## 5. How the Privacy Risk score works (0–100, higher = riskier)
`Risk = DIRECT part (max 55) + QUASI part (max 45)`
* **Direct part** = 55 × weighted average *exposure* of direct-identifier columns
  (Keep 1.0 · Masking 0.1–0.8 depending on visible characters · Generalization 0.3 · Hashing 0.25 · Replacement 0.1 · Suppression 0).
* **Quasi part** = 45 × average re-identification probability, assuming an attacker who knows any **3** quasi-identifiers
  (e.g. Age + City + Job). A record in a group of size *k* has probability 1/*k*.
* Levels: LOW < 30 ≤ MEDIUM < 60 ≤ HIGH. Called *“Prototype Re-identification Risk Score”* – not a formal certification.

## 6. How Data Utility works (0–100, original = 100)
`Utility = 20 % A + 20 % B + 25 % C + 15 % D + 20 % E`
A columns preserved · B values not suppressed · C numeric precision kept (bin width vs. range) · D data types preserved ·
E distributions preserved (mean/std for numbers, category counts for text). C/D/E ignore direct identifiers.
It is a general indicator and does not represent every analytical use case.

## 7. Run it
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Works fully offline: no paid APIs, no cloud, no GPU, no model download (Presidio pattern recognizers don't need spaCy).
Run the tests with `pytest tests -q`. Regenerate the demo data with `python scripts/make_demo_dataset.py`.

### Project layout
```
app.py                       Streamlit UI (6 pages)
src/detection/               lexicon.py · saudi_recognizers.py (Presidio + validators) · detector.py
src/anonymization/           methods.py · profiles.py · pipeline.py
src/risk/risk.py             Prototype Re-identification Risk
src/utility/utility.py       Prototype Data Utility
src/reporting/report.py      Saudi Privacy Assessment Report (Markdown + HTML)
data/sample_saudi_dataset.csv  48 FAKE Saudi-style records
tests/                       unit + end-to-end tests
```

## 8. Suggested 3–5 minute demo
1. Dashboard → **Load Saudi demo dataset** (jumps to detection).
2. Show detected National ID / mobile / IBAN / Arabic names, confidence, risk, and *Why*. Open **Below threshold** (`order_ref` is *not* an ID) and **Try the detector** (type “رقم الهوية: …” vs. a bare number).
3. **Configure** → choose *AI / External Company* → show recommended methods → change one.
4. Click **Anonymize** → Results: risk ~97 → ~26, utility ~100 → ~80, side-by-side tables.
5. **Privacy Report** → generate and download; download the anonymized CSV/Excel.
6. Optional: switch profile to *Developer Testing* and compare the output and scores.

## 9. Limitations
* Prototype scores are simple and transparent, **not** formal risk certification; no differential privacy, no k-anonymity enforcement.
* Free-text: Saudi IDs, mobiles, IBANs and e-mails are found and masked inside text; **names/addresses inside free text are not detected**.
* Name detection is lexicon + column-name based (no ML); unusual names in unlabeled columns may be missed.
* Indirect identifiers are *suggested* from column names – the user must confirm them.
* CSV/XLSX only, a few thousand rows; no images, PDFs, OCR, authentication or databases.
* The interface is English; Arabic values and Arabic keywords are fully supported (language toggle left as a future improvement).
* Not legal advice; does not guarantee PDPL compliance.

## 10. Key terms
* **PII** – information that can identify a person.
* **Anonymization** – irreversibly reducing the ability to identify a real individual.
* **Direct identifier** – identifies a person on its own (name, National ID, Iqama, phone, e-mail, IBAN).
* **Indirect identifier / quasi-identifier** – identifies someone only when combined (age, city, job, salary …).
* **Re-identification risk** – estimated possibility of identifying someone again after anonymization.
* **Data utility** – how useful the anonymized dataset remains for analytics or AI.
* **Privacy–utility trade-off** – stronger protection usually removes detail, lowering utility.
