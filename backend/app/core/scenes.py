from __future__ import annotations

SCENES: dict[str, dict] = {
    "interview": {
        "name": "Job Interview",
        "name_zh": "求职面试",
        "opening": "Please introduce yourself briefly.",
        "personas": {
            "strict_interviewer": {
                "name": "Alex",
                "system_prompt": "You are a strict interviewer. Keep replies under 40 words. Difficulty: {difficulty}.",
            }
        },
    },
    "restaurant": {
        "name": "Restaurant Order",
        "name_zh": "餐厅点餐",
        "opening": "Welcome, what would you like to order?",
        "personas": {
            "friendly_waiter": {
                "name": "Sam",
                "system_prompt": "You are a friendly waiter. Keep replies under 40 words. Difficulty: {difficulty}.",
            }
        },
    },
    "meeting": {
        "name": "Business Meeting",
        "name_zh": "商务会议",
        "opening": "Let's begin the meeting. Please share your idea.",
        "personas": {
            "colleague": {
                "name": "Jordan",
                "system_prompt": "You are a professional colleague. Keep replies under 40 words. Difficulty: {difficulty}.",
            }
        },
    },
}

