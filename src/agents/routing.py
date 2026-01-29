CONFIDENCE_THRESHOLD = 0.6

def route_transaction(rule_result, transaction, llm_agent):
    if rule_result["confidence"] >= CONFIDENCE_THRESHOLD:
        return {
            **rule_result,
            "source": "rule"
        }

    # Escalate to LLM (if available)
    llm_available = (
        llm_agent is not None
        and hasattr(llm_agent, "categorize")
        and (not hasattr(llm_agent, "is_enabled") or llm_agent.is_enabled())
    )

    if not llm_available:
        return {
            **rule_result,
            "source": "rule_no_llm",
            "reason": "Rule confidence below threshold, but LLM is unavailable/disabled",
        }

    print(f"[ESCALATING TO LLM] {transaction['description']}")
    llm_result = llm_agent.categorize(transaction)

    return {
        **llm_result,
        "source": "llm",
        "rule_confidence": rule_result["confidence"]
    }
