def evaluate_function_quality(function_code):
    score = 0
    reasons = []

    lines = function_code.splitlines()

    # Rule 1: Shorter function is better
    length = len(lines)
    if length <= 3:
        score += 4
        reasons.append("very short and concise")
    elif length <= 6:
        score += 2
        reasons.append("moderately short")
    else:
        score += 1

    # Rule 2: Penalize loops heavily
    if "for " in function_code:
        score -= 3
        reasons.append("uses manual loop")

    # Rule 3: Detect accumulator pattern (total += ...)
    if "+=" in function_code:
        score -= 2
        reasons.append("uses manual accumulation")

    # Rule 4: Simplicity (less assignments)
    assignments = function_code.count("=")
    if assignments <= 1:
        score += 2
        reasons.append("simple logic")

    return score, reasons


def compare_functions(func1, func2):
    score1, reasons1 = evaluate_function_quality(func1["code"])
    score2, reasons2 = evaluate_function_quality(func2["code"])

    if score1 > score2:
        return func1["name"], reasons1
    elif score2 > score1:
        return func2["name"], reasons2
    else:
        # FINAL tie-breaker (IMPORTANT)
        if len(func1["code"]) < len(func2["code"]):
            return func1["name"], ["shorter implementation"]
        elif len(func2["code"]) < len(func1["code"]):
            return func2["name"], ["shorter implementation"]
        else:
            return "equal", ["Both functions have similar quality"]