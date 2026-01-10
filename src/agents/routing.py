def route_transaction(
    rule_result: dict,
    transaction: dict,
    llm_agent
) -> dict:
    # --- Schema guards (fail fast if contract is broken) ---
    assert isinstance(rule_result, dict), f"rule_result must be dict, got {type(rule_result)}"
    assert "category" in rule_result, "rule_result missing required key: 'category'"
    assert "category_confidence" in rule_result, "rule_result missing required key: 'category_confidence'"

    rule_confidence = rule_result.get("category_confidence", 0.0)

    # --- High-confidence rule result ---
    if rule_confidence >= 0.75:
        return {
            "final_category": rule_result["category"],
            "final_confidence": rule_confidence,
            "categorization_source": "rule",
            "llm_reason": None
        }

    # --- Medium-confidence → LLM fallback ---
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

    # --- Low-confidence rule result ---
    return {
        "final_category": "Uncategorized",
        "final_confidence": rule_confidence,
        "categorization_source": "rule_low_confidence",
        "llm_reason": None
    }
