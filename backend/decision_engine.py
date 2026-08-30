"""
Decision Engine for DisputeShield.

Converts model confidence into a bounded business action.

The AI recommends actions:
- contest when evidence is strong
- avoid contesting when evidence is weak
- send uncertain cases for human review
"""


def decide_action(defensibility_score: float) -> dict:
    """
    Route dispute based on model confidence.

    Thresholds:
    >= 0.65  -> Recommend contest
    <= 0.35  -> Recommend not contesting
    between  -> Human review
    """

    if defensibility_score >= 0.65:

        return {
            "action": "RECOMMEND_CONTEST",
            "reason": (
                "High confidence that retrieved evidence "
                "supports a merchant dispute response."
            ),
            "requires_human_review": False
        }


    elif defensibility_score <= 0.35:

        return {
            "action": "RECOMMEND_NOT_CONTESTING",
            "reason": (
                "Evidence strength is insufficient to justify "
                "spending resources contesting this dispute."
            ),
            "requires_human_review": False
        }


    else:

        return {
            "action": "HUMAN_REVIEW",
            "reason": (
                "Model confidence is uncertain. "
                "Additional manual investigation required."
            ),
            "requires_human_review": True
        }



if __name__ == "__main__":

    test_scores = [
        0.87,
        0.21,
        0.52
    ]

    for score in test_scores:

        print("\nScore:", score)

        decision = decide_action(score)

        print(decision)