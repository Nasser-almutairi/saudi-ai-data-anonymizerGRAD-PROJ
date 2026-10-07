# -*- coding: utf-8 -*-
"""Purpose profiles + recommendation table. Deliberately simple: a lookup table, not a policy engine."""

METHODS = ["Keep", "Masking", "Suppression", "Replacement", "Generalization", "Hashing"]

PROFILES = {
    "external": {
        "name": "AI / External Company",
        "description": "Data leaves the organisation → STRONGER anonymization: direct identifiers removed or heavily masked, "
                       "quasi-identifiers generalised into wide bands.",
        "strength": "strong", "target_bins": 3, "min_group_frac": 0.10, "format_preserving": False,
    },
    "developer": {
        "name": "Developer Testing",
        "description": "Developers need realistic-looking data → FORMAT-PRESERVING fake values (valid-looking IDs, phones, "
                       "IBANs, names) so applications and validators keep working.",
        "strength": "medium", "target_bins": 8, "min_group_frac": 0.05, "format_preserving": True,
    },
    "internal": {
        "name": "Internal Analytics",
        "description": "Trusted internal analysts → preserve MORE statistical information: narrow bins, linkable hashed IDs, "
                       "common categories kept as-is.",
        "strength": "medium", "target_bins": 12, "min_group_frac": 0.05, "format_preserving": False,
    },
}

# entity -> {profile: method}
_ALL = lambda m: {"external": m, "developer": m, "internal": m}
RECOMMENDATIONS = {
    "SAUDI_NATIONAL_ID": {"external": "Suppression", "developer": "Replacement", "internal": "Masking"},
    "SAUDI_MOBILE":      {"external": "Masking", "developer": "Replacement", "internal": "Masking"},
    "SAUDI_IBAN":        {"external": "Suppression", "developer": "Replacement", "internal": "Masking"},
    "EMAIL_ADDRESS":     {"external": "Masking", "developer": "Replacement", "internal": "Masking"},
    "ARABIC_PERSON_NAME": _ALL("Replacement"),
    "PERSON_NAME":       _ALL("Replacement"),
    "SAUDI_ADDRESS":     {"external": "Suppression", "developer": "Generalization", "internal": "Generalization"},
    "CUSTOMER_ID":       _ALL("Hashing"),
    "AGE":               _ALL("Generalization"),
    "SALARY":            _ALL("Generalization"),
    "DATE_OF_BIRTH":     _ALL("Generalization"),
    "CITY":              {"external": "Generalization", "developer": "Keep", "internal": "Keep"},
    "DISTRICT":          {"external": "Suppression", "developer": "Generalization", "internal": "Generalization"},
    "GENDER":            _ALL("Keep"),
    "JOB_TITLE":         {"external": "Generalization", "developer": "Keep", "internal": "Keep"},
    "NATIONALITY":       {"external": "Generalization", "developer": "Keep", "internal": "Keep"},
}

WHY = {
    "Masking": "keeps the format but hides most characters",
    "Suppression": "removes the value completely (strongest protection)",
    "Replacement": "swaps the value for a pseudonym / fake value",
    "Generalization": "turns exact values into ranges or broader groups",
    "Hashing": "one-way salted hash: records stay linkable but values are not readable",
    "Keep": "low-risk field, keep as-is for analytical value",
}


def recommend(entities, embedded, profile_key):
    """entities: list of entity names flagged in one column. Free-text columns are masked inline."""
    if not entities:
        return "Keep"
    if embedded:
        return "Masking"
    return RECOMMENDATIONS.get(entities[0], _ALL("Masking"))[profile_key]
