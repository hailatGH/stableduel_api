from django.db import models
from django.contrib.auth import get_user_model

from stables.models import Stable
from sys import maxsize

User = get_user_model()

TierList = [
    {
        "tier": "none",
        "position": 0.00,
        "min": 0,
        "max": 15000
    },
    {
        "tier": "silver",
        "position": 0.10,
        "min": 15000,
        "max": 50000
    },
    {
        "tier": "gold",
        "position": 0.3,
        "min": 50000,
        "max": 100000
    },
    {
        "tier": "platinum",
        "position": 0.50,
        "min": 100000,
        "max": 250000
    },
    {
        "tier": "diamond",
        "position": 0.70,
        "min": 250000,
        "max": 1000000
    },
    {
        "tier": "vip",
        "position": 0.90,
        "min": 1000000,
        "max": maxsize
    }
]

def get_tier(points):
    for tier in TierList:
        min_points = tier["min"]
        max_points = tier["max"]
        if (points >= min_points and points < max_points):
            return tier
    
    if (points == maxsize):
        return TierList[-1]

    return TierList[0]

def get_tier_and_progress_for_prev_curr_year_points(prev_year_points, curr_year_points):
    prev_tier = get_tier(prev_year_points)
    
    # the next year we effectively start from zero, but keep the previous tier
    # so find the max points between prev_tier["max"] and curr_year_points and subtract the prev_tier["max"]
    # this will give us points earned this year that will count towards this years tier
    points_earned_towards_curr_year_tier = max(prev_tier["min"], curr_year_points)

    curr_year_tier = get_tier(points_earned_towards_curr_year_tier)
    # if our curr year tier is less than the prev tier, just use that for the rest of the calculations
    if (curr_year_tier["max"] < prev_tier["max"]):
        curr_year_tier = prev_tier    

    next_tier = get_tier(curr_year_tier["max"])

    points_to_next_tier = next_tier["min"] - curr_year_tier["min"]
    next_tier_progress = 0.0
    if (points_to_next_tier == 0):
        next_tier_progress = 0.0
    else:
        next_tier_progress = (points_earned_towards_curr_year_tier - curr_year_tier["min"] ) / points_to_next_tier

    if (next_tier_progress < 0):
        next_tier_progress = 0.0

    return {
        "current_tier": curr_year_tier["tier"],
        "current_tier_full": curr_year_tier,
        "next_tier_progress": next_tier_progress
    }

class StablePoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    stable = models.ForeignKey(Stable, on_delete=models.CASCADE, blank=True, null=True)
    points = models.IntegerField(default=0)
    notes = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

