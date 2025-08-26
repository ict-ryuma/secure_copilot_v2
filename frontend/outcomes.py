outcome_array = {0:"🟢 成約", 1:"🔴 未成約", 2:"🟡 再商談"}

def display_outcome(val):
    """Return the emoji + text for a given outcome value"""
    try:
        val = int(val)  # convert to int if needed
    except (ValueError, TypeError):
        return "❓ Unknown"
    return outcome_array.get(val, "❓ Unknown")