def infer_intent(query: str):
    q = query.lower()
    tech = any(k in q for k in ["java", "developer", "coding", "software"])
    soft = any(k in q for k in ["communication", "leadership", "behavior"])

    if tech and soft:
        return "balanced"
    elif tech:
        return "technical"
    elif soft:
        return "behavioral"
    return "balanced"


def rerank_results(results, intent, top_n=6):
    final = []

    k_tests = [r for r in results if r["test_type"] == "K"]
    p_tests = [r for r in results if r["test_type"] == "P"]

    # Filter obvious non-assessments
    def is_valid(r):
        return "report" not in r["assessment_name"].lower()

    k_tests = list(filter(is_valid, k_tests))
    p_tests = list(filter(is_valid, p_tests))

    if intent == "balanced":
        final.extend(k_tests[:4])
        final.extend(p_tests[:2])
    elif intent == "technical":
        final.extend(k_tests[:5])
        final.extend(p_tests[:1])
    else:
        final.extend(p_tests[:5])
        final.extend(k_tests[:1])

    return final[:top_n]
