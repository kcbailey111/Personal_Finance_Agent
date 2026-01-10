def route_transaction(
    rule_result: dict,
    transaction: dict,
    llm_agent
) -> dict:
    assert isinstance(rule_result, dict), f"rule_result must be dict, got {type(rule_result)}"
    assert "category" in rule_result, "rule_result missing required key: 'category'"
    assert "category_confidence" in rule_result, "rule_result missing required key: 'category_confidence'"

    rule_confidence = rule_result["category_confidence"]

    if rule_confidence >= 0.75:
        return {
            "category": rule_result["category"],
            "confidence": rule_confidence,
            "source": "rule",
            "reason": None
        }

    if 0.40 <= rule_confidence < 0.75:
        try:
            llm_result = llm_agent.categorize(transaction)
            return {
                "category": llm_result["category"],
                "confidence": llm_result["confidence"],
                "source": "llm",
                "reason": llm_result["reason"]
            }
        except Exception as e:
            return {
                "category": "Uncategorized",
                "confidence": 0.0,
                "source": "fallback",
                "reason": str(e)
            }

    return {
        "category": "Uncategorized",
        "confidence": rule_confidence,
        "source": "rule_low_confidence",
        "reason": None
    }
