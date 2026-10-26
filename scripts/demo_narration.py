"""The spoken track for the demo video.

One entry per scene. `say` turns each `text` into audio, the recorder marks where
that scene starts and ends in the raw screen capture, and the assembler squeezes
the capture to fit the narration. So the voice is the clock: change a line here
and the picture re-times itself around it.

Every number spoken aloud is a measured one. Keep it that way -- the score and
the run cost are read off the screen, not asserted here, because they depend on
the answers given in `record_demo.py`.
"""

# Samantha is the only en_US voice on this machine that reads as a person rather
# than a novelty. 170 wpm is a touch under her default; it survives compression.
VOICE = "Samantha"
RATE = 170

# `hold` keeps the last N seconds of a scene at natural speed, for the moments
# worth actually watching. `max_speed` caps how hard the rest may be compressed;
# chat scenes spend most of their wall clock on a typing indicator, so they take
# a lot of squeezing before they look hurried.
SCENES = [
    dict(
        id="intro",
        max_speed=1.0,
        text="This is ReadyHome. It asks a family a few questions, tells them how "
        "ready they are for an emergency, and gives them three small steps to "
        "get readier.",
    ),
    dict(
        id="why",
        max_speed=1.0,
        text="I grew up in a multi-generational household. In an emergency, a "
        "toddler, a grandparent with a walker, and a dog each need something "
        "completely different. The official guidance for each of them lives in a "
        "different P D F, and nothing tells one family where they actually stand.",
    ),
    dict(
        id="start",
        max_speed=5.0,
        text="Sunny runs the survey. One short question at a time, with tappable "
        "answers, or your own words.",
    ),
    dict(
        id="injection",
        max_speed=3.0,
        hold=2.5,
        text="Before the real answers, let me try to break it. A prompt injection "
        "is caught before it ever reaches the model, so the attack costs nothing. "
        "No prompt leaks, and the survey picks up where it left off.",
    ),
    dict(
        id="sensitive",
        max_speed=4.0,
        hold=3.0,
        text="Here is the part I care about most. When the questions get personal, "
        "about mobility, medical equipment, or needing help to evacuate, Sunny "
        "pushes the sunglasses up and drops the emoji. The app decides that in "
        "plain code, not by asking the model to be tactful.",
    ),
    dict(
        id="state",
        max_speed=5.0,
        text="The state question is a searchable list, so nobody has to guess a "
        "format.",
    ),
    dict(
        id="rest",
        max_speed=12.0,
        text="The rest of the questions cover what the household already has. "
        "Water, medication, backup power, and a way to get out.",
    ),
    dict(
        id="score",
        max_speed=1.0,
        text="There is the score, out of ten. It only counts what applies to this "
        "household, so a family with no pets loses no points for pet supplies. The "
        "breakdown underneath shows exactly where the gaps are.",
    ),
    dict(
        id="steps",
        max_speed=2.0,
        text="Three steps at a time, biggest win first. Each one says what it is "
        "worth, what it costs, and links to the official source it came from. The "
        "app cannot invent a step or a link. Both come from a fixed knowledge base, "
        "and a verifier drops anything that is not in it.",
    ),
    dict(
        id="complete",
        max_speed=2.0,
        hold=4.0,
        # The score does climb here (4.5 -> 5, and the database agrees), but the
        # page is scrolled to the cards, so it happens off camera. Claim only
        # what the frame actually shows.
        text="And when you actually do one, you tick off what you did, and the "
        "next best step moves up to take its place.",
    ),
    dict(
        id="cost",
        max_speed=1.5,
        text="Every session reports what it cost to run. This one is about fourteen "
        "cents: the token counts are measured, the dollar rate is an assumption. "
        "The scoring and the ranking are plain Python, so they cost nothing at all. "
        "ReadyHome. One small step at a time.",
    ),
]
