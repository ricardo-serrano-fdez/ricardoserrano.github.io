"""Carcassonne Companion scoring engine and rules."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import uuid

DEFAULT_PALETTE = [
    {"name": "Blue", "color": "#3976bb"},
    {"name": "Red", "color": "#be463e"},
    {"name": "Yellow", "color": "#d7a320"},
    {"name": "Green", "color": "#468354"},
    {"name": "Black", "color": "#323232"},
    {"name": "Pink", "color": "#cf6f99"},
]

RULES = {
    "city": {
        "label": "City",
        "amount_label": "City tiles",
        "bonus_label": "Pennants / shields",
        "has_bonus": True,
        "max_amount": None,
        "help": "Incomplete city: 1 point per tile and 1 per pennant/shield.",
    },
    "road": {
        "label": "Road",
        "amount_label": "Road tiles",
        "bonus_label": "Not used",
        "has_bonus": False,
        "max_amount": None,
        "help": "Incomplete road: 1 point per tile.",
    },
    "monastery": {
        "label": "Monastery",
        "amount_label": "Adjacent tiles (0–8)",
        "bonus_label": "Not used",
        "has_bonus": False,
        "max_amount": 8,
        "help": "Incomplete monastery: 1 point for monastery + 1 for each adjacent tile (1–9 total).",
    },
    "farm": {
        "label": "Farm",
        "amount_label": "Completed cities supplied",
        "bonus_label": "Not used",
        "has_bonus": False,
        "max_amount": None,
        "help": "Farmer: 3 points for each completed city adjacent to this farm/field.",
    },
}


def score_feature(feature_type: str, amount: int, bonus: int = 0) -> int:
    """Calculate the points earned for a given construction."""
    if feature_type == "city":
        return amount + bonus
    elif feature_type == "road":
        return amount
    elif feature_type == "monastery":
        return 1 + amount
    elif feature_type == "farm":
        return amount * 3
    return 0


def calculate_totals(players: list[dict], features: list[dict]) -> dict[str, int]:
    """Calculate total scores per player."""
    totals = {player["id"]: 0 for player in players}
    for feature in features:
        pts = score_feature(feature["type"], feature["amount"], feature.get("bonus", 0))
        for player_id in feature.get("owners", []):
            if player_id in totals:
                totals[player_id] += pts
    return totals
