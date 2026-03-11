import hashlib
import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone


TOKEN_REGEX = re.compile(r'(?:#\w+(?:-\w+)*)|\b\w+\b', flags=re.UNICODE)

POSITIVE_WORDS = {
    "adorei",
    "gostei",
    "bom",
    "otimo",
    "excelente",
}

NEGATIVE_WORDS = {
    "ruim",
    "terrivel",
    "pessimo",
}

INTENSIFIERS = {
    "muito",
    "super",
}

NEGATIONS = {
    "nao",
    "nunca",
}


def normalize_for_matching(token: str) -> str:
    lowered = token.lower()
    nfkd = unicodedata.normalize("NFKD", lowered)
    return "".join(ch for ch in nfkd if not unicodedata.combining(ch))


def parse_timestamp_utc(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def tokenize(text: str) -> list[str]:
    return TOKEN_REGEX.findall(text)


def is_meta_message(content: str) -> bool:
    return content.strip().lower() == "teste técnico mbras"


def sentiment_score_for_message(content: str, user_id: str) -> tuple[float, str]:
    if is_meta_message(content):
        return 0.0, "meta"

    tokens = tokenize(content)
    lex_tokens = [normalize_for_matching(tok) for tok in tokens if not tok.startswith("#")]
    if not lex_tokens:
        return 0.0, "neutral"

    intensifier_positions = {idx for idx, token in enumerate(lex_tokens) if token in INTENSIFIERS}
    negation_positions = [idx for idx, token in enumerate(lex_tokens) if token in NEGATIONS]

    total = 0.0
    for idx, token in enumerate(lex_tokens):
        if token in POSITIVE_WORDS:
            value = 1.0
        elif token in NEGATIVE_WORDS:
            value = -1.0
        else:
            continue

        if (idx - 1) in intensifier_positions:
            value *= 1.5

        neg_count = 0
        for neg_pos in negation_positions:
            if 0 < (idx - neg_pos) <= 3:
                neg_count += 1
        if neg_count % 2 == 1:
            value *= -1.0

        if value > 0 and "mbras" in user_id.lower():
            value *= 2.0

        total += value

    score = total / len(lex_tokens)
    if score > 0.1:
        return score, "positive"
    if score < -0.1:
        return score, "negative"
    return score, "neutral"


def get_followers(user_id: str) -> int:
    normalized_user_id = normalize_for_matching(user_id)
    if "cafe" in normalized_user_id:
        return 4242
    if len(user_id) == 13:
        return 233
    if user_id.lower().endswith("_prime"):
        base = (int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16) % 900) + 100
        while True:
            if base < 2:
                base += 1
                continue
            is_prime = True
            for div in range(2, int(base ** 0.5) + 1):
                if base % div == 0:
                    is_prime = False
                    break
            if is_prime:
                return base
            base += 1

    return (int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16) % 10000) + 100


def detect_burst(timestamps: list[datetime]) -> bool:
    if len(timestamps) < 11:
        return False
    sorted_ts = sorted(timestamps)
    left = 0
    window = timedelta(minutes=5)
    for right in range(len(sorted_ts)):
        while sorted_ts[right] - sorted_ts[left] > window:
            left += 1
        if (right - left + 1) > 10:
            return True
    return False


def detect_alternating_pattern(labels: list[str]) -> bool:
    sequence = [label for label in labels if label in {"positive", "negative"}]
    if len(sequence) < 10:
        return False
    for idx in range(1, len(sequence)):
        if sequence[idx] == sequence[idx - 1]:
            return False
    return True


def analyze_feed(messages: list, time_window_minutes: int) -> dict:
    started = time.perf_counter()

    parsed_messages = []
    for message in messages:
        parsed_messages.append({
            "id": message.id,
            "content": message.content,
            "timestamp": parse_timestamp_utc(message.timestamp),
            "user_id": message.user_id,
            "hashtags": message.hashtags,
            "reactions": message.reactions,
            "shares": message.shares,
            "views": message.views,
        })

    if parsed_messages:
        now_utc = max(item["timestamp"] for item in parsed_messages)
    else:
        now_utc = datetime.now(timezone.utc)

    lower_bound = now_utc - timedelta(minutes=time_window_minutes)
    window_messages = [
        item
        for item in parsed_messages
        if lower_bound <= item["timestamp"] <= now_utc
    ]

    sentiment_counts = Counter({"positive": 0, "negative": 0, "neutral": 0})
    sentiment_by_message = {}
    user_timestamps = defaultdict(list)
    user_sentiments = defaultdict(list)
    hashtag_stats = defaultdict(lambda: {"weight": 0.0, "freq": 0, "sentiment_weight": 0.0})

    flag_mbras_employee = False
    flag_special_pattern = False
    flag_candidate_awareness = False

    for item in window_messages:
        content = item["content"]
        user_id = item["user_id"]
        timestamp = item["timestamp"]

        if "mbras" in user_id.lower():
            flag_mbras_employee = True
        if len(content) == 42 and "mbras" in content.lower():
            flag_special_pattern = True
        if "teste técnico mbras" in content.lower():
            flag_candidate_awareness = True

        _, label = sentiment_score_for_message(content, user_id)
        sentiment_by_message[item["id"]] = label
        user_timestamps[user_id].append(timestamp)
        user_sentiments[user_id].append(label)

        if label != "meta":
            sentiment_counts[label] += 1

        for hashtag in item["hashtags"]:
            minutes_since = max((now_utc - timestamp).total_seconds() / 60.0, 1.0)
            temporal_weight = 1.0 + (1.0 / minutes_since)
            if label == "positive":
                sentiment_factor = 1.2
            elif label == "negative":
                sentiment_factor = 0.8
            else:
                sentiment_factor = 1.0

            length_factor = 1.0
            if len(hashtag) > 8:
                length_factor = math.log10(len(hashtag)) / math.log10(8)

            weight = temporal_weight * sentiment_factor * length_factor
            hashtag_stats[hashtag]["weight"] += weight
            hashtag_stats[hashtag]["freq"] += 1
            hashtag_stats[hashtag]["sentiment_weight"] += sentiment_factor

    non_meta_total = sentiment_counts["positive"] + sentiment_counts["negative"] + sentiment_counts["neutral"]
    if non_meta_total == 0:
        distribution = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    else:
        distribution = {
            "positive": round((sentiment_counts["positive"] / non_meta_total) * 100, 1),
            "negative": round((sentiment_counts["negative"] / non_meta_total) * 100, 1),
            "neutral": round((sentiment_counts["neutral"] / non_meta_total) * 100, 1),
        }

    ranked_hashtags = sorted(
        hashtag_stats.items(),
        key=lambda entry: (
            -entry[1]["weight"],
            -entry[1]["freq"],
            -entry[1]["sentiment_weight"],
            entry[0],
        ),
    )
    trending_topics = [tag for tag, _ in ranked_hashtags[:5]]

    influence_ranking = []
    by_user = defaultdict(lambda: {"reactions": 0, "shares": 0, "views": 0})
    for item in window_messages:
        user_metrics = by_user[item["user_id"]]
        user_metrics["reactions"] += item["reactions"]
        user_metrics["shares"] += item["shares"]
        user_metrics["views"] += item["views"]

    phi = (1 + 5 ** 0.5) / 2
    for user_id, metrics in by_user.items():
        followers = get_followers(user_id)
        interactions = metrics["reactions"] + metrics["shares"]
        views = max(metrics["views"], 1)
        engagement_rate = interactions / views
        if interactions > 0 and interactions % 7 == 0:
            engagement_rate *= (1 + (1 / phi))

        influence_score = (followers * 0.4) + (engagement_rate * 0.6)
        if user_id.lower().endswith("007"):
            influence_score *= 0.5
        if "mbras" in user_id.lower():
            influence_score += 2.0

        influence_ranking.append({
            "user_id": user_id,
            "influence_score": round(influence_score, 4),
        })

    influence_ranking.sort(key=lambda item: (-item["influence_score"], item["user_id"]))

    detected_anomaly_types: list[str] = []
    for user_id, timestamps in user_timestamps.items():
        if detect_burst(timestamps):
            detected_anomaly_types.append("burst")
        if detect_alternating_pattern(user_sentiments[user_id]):
            detected_anomaly_types.append("alternating_sentiment")

    if len(window_messages) >= 3:
        min_ts = min(item["timestamp"] for item in window_messages)
        max_ts = max(item["timestamp"] for item in window_messages)
        if (max_ts - min_ts).total_seconds() <= 4:
            detected_anomaly_types.append("synchronized_posting")

    anomaly_detected = len(detected_anomaly_types) > 0
    anomaly_type: str | None = detected_anomaly_types[0] if anomaly_detected else None

    if flag_candidate_awareness:
        engagement_score = 9.42
    else:
        if by_user:
            total_rate = 0.0
            for metrics in by_user.values():
                total_rate += (metrics["reactions"] + metrics["shares"]) / max(metrics["views"], 1)
            engagement_score = round((total_rate / len(by_user)) * 100, 2)
        else:
            engagement_score = 0.0

    processing_time_ms = round((time.perf_counter() - started) * 1000, 3)

    return {
        "analysis": {
            "sentiment_distribution": distribution,
            "engagement_score": engagement_score,
            "trending_topics": trending_topics,
            "influence_ranking": influence_ranking,
            "anomaly_detected": anomaly_detected,
            "anomaly_type": anomaly_type,
            "flags": {
                "mbras_employee": flag_mbras_employee,
                "special_pattern": flag_special_pattern,
                "candidate_awareness": flag_candidate_awareness,
            },
            "processing_time_ms": processing_time_ms,
        }
    }