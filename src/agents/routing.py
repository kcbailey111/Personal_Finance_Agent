def route_transaction(
    rule_result: dict,
    transaction: dict,
    llm_agent
) -> dict:

    rule_confidence = rule_result["confidence"]

    if rule_confidence >= 0.75:
        return {
            "final_category": rule_result["category"],
            "final_confidence": rule_confidence,
            "categorization_source": "rule",
            "llm_reason": None
        }

    if 0.40 <= rule_confidence < 0.75:
        try:
            llm_result = llm_agent.categorize(transaction)
            return {
                "final_category": llm_result["category"],
                "final_confidence": llm_result["confidence"],
                "categorization_source": "llm",
                "llm_reason": llm_result["reason"]
            }
        except Exception as e:
            return {
                "final_category": "Uncategorized",
                "final_confidence": 0.0,
                "categorization_source": "fallback",
                "llm_reason": str(e)
            }

    return {
        "final_category": "Uncategorized",
        "final_confidence": rule_confidence,
        "categorization_source": "rule_low_confidence",
        "llm_reason": None
    }
