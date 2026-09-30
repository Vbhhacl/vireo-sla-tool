from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, TfidfVectorizer

KEYWORDS = {
    "delivery/order issue": ["delivery", "shipment", "tracking", "lost", "late", "damaged", "refund", "reship", "order"],
    "refund/payment": ["payment", "invoice", "charge", "refund", "billing", "transaction", "duplicate payment", "coupon"],
    "product fault": ["fault", "defect", "broken", "noisy", "not working", "battery", "mic", "speaker", "pairing", "quality"],
    "warranty": ["warranty", "repair", "rma", "replacement", "claim"],
    "replacement": ["replace", "replacement", "send new", "new unit"],
    "account/payment": ["login", "password", "account", "profile", "otp", "email", "verification"],
    "promotion": ["coupon", "promo", "offer", "discount", "voucher"],
}

THEME_STOP_WORDS = set(ENGLISH_STOP_WORDS) | {
    "dear", "sir", "madam", "regards", "thanks", "thank", "hello", "hii", "hi",
    "ivr", "transcript", "vireo", "pulse", "order", "product", "customer",
    "purchased", "purchase", "expected", "tried", "issue", "writing", "reference",
    "request", "please", "team", "regarding",
}


def classify_driver(message: str | None) -> str:
    text = (message or "").lower()
    if not text:
        return "other"
    for label, terms in KEYWORDS.items():
        if any(term in text for term in terms):
            return label
    return "other"


def classify_sample(df: pd.DataFrame, sample_size: int = 80) -> pd.DataFrame:
    eligible = df[["ticket_id", "customer_message", "agent_notes"]].dropna(subset=["customer_message"])
    sample = eligible.sample(min(sample_size, len(eligible)), random_state=42).copy()
    sample["driver_label"] = sample["customer_message"].apply(classify_driver)
    sample["review_status"] = "classified"
    return sample


def discover_themes(df: pd.DataFrame, n_topics: int = 5) -> pd.DataFrame:
    """Discover recurring ticket-text themes with local, unsupervised ML."""
    messages = df["customer_message"].dropna().astype(str).str.strip()
    messages = messages[messages.str.len().ge(20) & ~messages.str.fullmatch(r"[-–—.?! ]*")]
    columns = ["theme_id", "tickets", "share", "top_terms", "example_message"]
    if len(messages) < 2 or n_topics < 1:
        return pd.DataFrame(columns=columns)

    vectorizer = TfidfVectorizer(stop_words=list(THEME_STOP_WORDS), ngram_range=(1, 2), min_df=2, max_features=5000)
    try:
        matrix = vectorizer.fit_transform(messages)
    except ValueError:
        return pd.DataFrame(columns=columns)

    topic_count = min(n_topics, len(messages), matrix.shape[1])
    if topic_count < 2:
        return pd.DataFrame(columns=columns)

    model = KMeans(n_clusters=topic_count, random_state=42, n_init=10)
    cluster_ids = model.fit_predict(matrix)
    terms = vectorizer.get_feature_names_out()
    result = pd.DataFrame({"message": messages.to_numpy(), "theme_id": cluster_ids})
    rows: list[dict[str, Any]] = []
    for theme_id, members in result.groupby("theme_id"):
        top_indices = model.cluster_centers_[theme_id].argsort()[::-1][:6]
        nearest_position = model.transform(matrix[members.index])[:, theme_id].argmin()
        example = members.iloc[int(nearest_position)]["message"]
        rows.append({
            "theme_id": int(theme_id) + 1,
            "tickets": int(len(members)),
            "share": float(len(members) / len(result)),
            "top_terms": ", ".join(terms[top_indices]),
            "example_message": example[:240],
        })
    return pd.DataFrame(rows, columns=columns).sort_values("tickets", ascending=False).reset_index(drop=True)


def validate_ai_output(classified_df: pd.DataFrame) -> dict[str, Any]:
    labels = classified_df["driver_label"].value_counts().to_dict()
    valid_labels = set(KEYWORDS) | {"other"}
    invalid = int((classified_df["driver_label"].isna() | ~classified_df["driver_label"].isin(valid_labels)).sum())
    report = {
        "model_used": "local TF-IDF + KMeans theme discovery; keyword tags are a heuristic baseline",
        "keyword_sample_size": int(len(classified_df)),
        "label_distribution": labels,
        "missing_or_invalid_labels": invalid,
        "keyword_label_coverage_rate": float(1 - invalid / len(classified_df)) if len(classified_df) else 0.0,
        "unclassified_or_other_count": int((classified_df["driver_label"] == "other").sum()),
        "semantic_accuracy": None,
        "semantic_accuracy_note": "Not measured: no independently human-labeled reference set is included.",
        "human_review_required": True,
        "common_failure_modes": ["generic messages without a clear root cause", "multiple issue types in one note", "TF-IDF themes are exploratory and need human interpretation"],
        "cost_per_run_usd": 0.0,
        "cost_per_month_usd": 0.0,
    }
    return report


def save_ai_report(report: dict[str, Any], path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return out
