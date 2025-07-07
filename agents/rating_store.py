import json
from pathlib import Path

RATING_FILE = Path("ratings.json")

def store_rating(rating: int):
    """Store the new rating into ratings.json."""
    if not RATING_FILE.exists():
        with open(RATING_FILE, "w") as f:
            json.dump([], f)

    with open(RATING_FILE, "r") as f:
        ratings = json.load(f)

    ratings.append(rating)

    with open(RATING_FILE, "w") as f:
        json.dump(ratings, f)

def get_average_rating() -> float:
    """Return average rating."""
    if not RATING_FILE.exists():
        return 0.0

    with open(RATING_FILE, "r") as f:
        ratings = json.load(f)

    if not ratings:
        return 0.0

    return round(sum(ratings) / len(ratings), 2)
