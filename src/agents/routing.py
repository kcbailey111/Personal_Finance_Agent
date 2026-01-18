CONFIDENCE_THRESHOLD = 0.6

def route_transaction(rule_result, transaction, llm_agent):
    if rule_result["confidence"] >= CONFIDENCE_THRESHOLD:
        return {
            **rule_result,
            "source": "rule"
        }

    # Escalate to LLM
    print(f"[ESCALATING TO LLM] {transaction['description']}")
    llm_result = llm_agent.categorize(transaction)

    return {
        **llm_result,
        "source": "llm",
        "rule_confidence": rule_result["confidence"]
    }
