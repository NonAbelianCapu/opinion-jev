"""The questions every engine answers about a state.

Believing and sharing are asked separately on purpose: the study is about the gap between them.
"""

BELIEVE = {
    "type": "choice",
    "instructions": "After reading this message, does the person believe the claim is true?",
    "criteria": {
        "believes": "The person accepts the claim as true",
        "doubts": "The person doubts or rejects the claim",
    },
}

TRUST_SOURCE = {
    "type": "score",
    "instructions": "How much does the person trust this source?",
    "criteria": [
        "No trust at all",
        "Little trust",
        "Moderate trust",
        "High trust",
        "Complete trust",
    ],
}

SHARE = {
    "type": "noul",
    "instructions": "Will the person share this message with their own contacts?",
    "criteria": {
        "true": "Forwards or reposts the message",
        "false": "Does not pass it on",
    },
}

# Graded version of believe. The choice above often comes back as exactly 0.0 or 1.0; a yes/no
# question on the same state usually returns a usable probability. Dynamics use this one.
BELIEVE_P = {
    "type": "noul",
    "instructions": "Does the person believe the claim in this message is true?",
    "criteria": {
        "true": "The person thinks the claim is true",
        "false": "The person thinks the claim is false or is not sure",
    },
}

# How a person rewrites the message if they share it. Asked together with share, sampled only
# when the person does share.
MUTATION = {
    "type": "choice",
    "instructions": "If this person forwards the message, how would they change it?",
    "criteria": {
        "verbatim": "Forwards it unchanged",
        "exaggerate": "Makes the claim bigger, more alarming or more certain",
        "soften": "Adds doubt or makes the claim milder",
        "add_detail": "Adds a specific detail that was not in the original",
        "change_source": "Attributes the claim to a different, more convincing source",
    },
}

STANDARD_QUESTIONS = {
    "believe": BELIEVE,
    "believe_p": BELIEVE_P,
    "trust_source": TRUST_SOURCE,
    "share": SHARE,
}
SPREAD_QUESTIONS = {"believe_p": BELIEVE_P, "share": SHARE, "mutation": MUTATION}

# Asked about each new version of the message on its own (the state is just the message text).
VARIANT_QUESTIONS = {
    "emotion": {
        "type": "score",
        "instructions": "How emotionally charged is this message?",
        "criteria": ["Neutral", "Slightly emotional", "Emotional", "Very emotional", "Alarmist"],
    },
    "extremity": {
        "type": "score",
        "instructions": "How extreme or sweeping is the claim in this message?",
        "criteria": ["Mild and limited", "Moderate", "Strong", "Very strong", "Sweeping or absolute"],
    },
}

# Label that counts as the "positive" outcome of each question, used by metrics and sampling.
POSITIVE_LABEL = {"believe": "believes", "believe_p": "true", "share": "true"}
