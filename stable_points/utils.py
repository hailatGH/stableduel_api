from sys import maxsize

# TODO!: Move this to DB, please
tier_list = [
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

# Sort tier list just in case
sorted(tier_list, key= lambda tier: tier["min"])

def get_tier(points):
    for tier in tier_list:
        min_points = tier["min"]
        max_points = tier["max"]
        if (points >= min_points and points < max_points):
            return tier
    
    if (points == maxsize):
        return tier_list[-1]

    return tier_list[0]

def get_tier_by_name(name):
    return next((t for t in tier_list if t["tier"] == name), tier_list[0])
def get_next_tier(tier):
    return next((t for t in tier_list if t["min"] >= tier["max"]), None)