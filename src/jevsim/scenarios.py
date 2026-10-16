"""Starting messages. All invented, local and politically neutral: no real people, parties or events."""

from jevsim.simulator.dynamics import Scenario
from jevsim.state_encoder import Message, Source

SCENARIOS = {
    "bins": Scenario(
        message=Message(
            text="Starting next month the neighborhood council will fine anyone who leaves their "
                 "bins on the sidewalk after 8am.",
            emotion=20,
            direction="for",
            stance_phrases={
                "for": "thinks the council should be stricter about bins on the sidewalk",
                "against": "thinks the council already has too many rules",
            },
        ),
        origin=Source("an anonymous account in the neighborhood chat group", 25),
    ),
    "pool": Scenario(
        message=Message(
            text="The municipal swimming pool will stay closed this summer because a routine "
                 "water test found a problem.",
            emotion=20,
            direction="for",
            stance_phrases={
                "for": "thinks the municipal pool has been badly maintained for years",
                "against": "trusts the staff who run the municipal pool",
            },
        ),
        origin=Source("an anonymous account in the neighborhood chat group", 25),
    ),
}
