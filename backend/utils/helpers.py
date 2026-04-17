"""
Shared helper functions used across the backend.
"""


def format_ltpc(lectures, tutorials, labs, credits):
    """
    Format L-T-P-C credit components into a display string.

    Examples:
        format_ltpc(3, 0, 2, 4)   -> "3-0-2-4"
        format_ltpc(3, 0, 3, 4.5) -> "3-0-3-4.5"
    """
    # Format credits: drop the decimal if it's a whole number
    if isinstance(credits, float) and credits == int(credits):
        credits_str = str(int(credits))
    else:
        credits_str = str(credits)

    return f"{lectures}-{tutorials}-{labs}-{credits_str}"


def build_batch_label(program, semester, branch=None, section=None):
    """
    Build a human-readable batch label matching the university format.

    Examples:
        build_batch_label("BTech", 4, "ICT + CS", "A")
            -> "BTech Sem-IV (ICT + CS) Sec-A"

        build_batch_label("BTech", 2, "MnC")
            -> "BTech Sem-II (MnC)"
    """
    # Convert semester number to Roman numeral for display
    roman = _to_roman(semester)
    parts = [program, f"Sem-{roman}"]

    if branch:
        parts.append(f"({branch})")

    if section:
        parts.append(f"Sec-{section}")

    return " ".join(parts)


def _to_roman(num):
    """
    Convert an integer (1-10) to a Roman numeral string.
    Covers the typical semester range.
    """
    mapping = [
        (10, "X"), (9, "IX"), (8, "VIII"), (7, "VII"),
        (6, "VI"), (5, "V"), (4, "IV"), (3, "III"),
        (2, "II"), (1, "I"),
    ]

    result = ""
    for value, numeral in mapping:
        while num >= value:
            result += numeral
            num -= value

    return result


# Day ordering for consistent sorting throughout the app
DAY_ORDER = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def sort_key_for_slot(slot_dict):
    """
    Return a sort key for a slot dictionary so that slots
    are ordered by day of week first, then by start time.
    """
    day_rank = DAY_ORDER.get(slot_dict["day_of_week"], 99)
    return (day_rank, slot_dict["start_time"])
