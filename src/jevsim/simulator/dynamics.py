"""Spread a message over the contact network while each sharer rewrites it.

Per step, every node that shared in the previous step exposes its contacts to the version it
forwarded. An exposed node that has not shared yet:
  1. sees one of the versions it was just sent (chosen at random if several contacts sent one),
  2. gets a belief probability from the engine (believe_p) and samples whether it believes,
  3. samples whether it shares (once per node),
  4. if it shares, samples how it changes the message (mutation) and the rewriter writes the
     new version. A new version is scored for emotion and extremity.
All sampling uses the run's RNG. Engines and the rewriter only return probabilities and text.
"""

from dataclasses import asdict, dataclass, field

import numpy as np

from jevsim import budget
from jevsim.engines.jev import JevEngine
from jevsim.probs import binary_entropy, expected_score
from jevsim.questions import SPREAD_QUESTIONS, VARIANT_QUESTIONS
from jevsim.simulator.network import build_network, highest_degree_node
from jevsim.simulator.sampling import sample_label
from jevsim.state_encoder import EncodedState, Message, Person, Source, encode, persona_sentence

NAMES = [
    "Marta", "Luis", "Ana", "Jorge", "Carmen", "Pablo", "Lucía", "Diego", "Elena", "Tomás",
    "Sofía", "Raúl", "Inés", "Martín", "Rosa", "Hugo", "Julia", "Andrés", "Paula", "Iván",
    "Clara", "Sergio", "Noelia", "Gabriel", "Laura", "Héctor", "Valeria", "Óscar", "Irene",
    "Manuel", "Beatriz", "Felipe", "Alicia", "Ramón", "Silvia", "Emilio", "Teresa", "Nicolás",
    "Patricia", "Ricardo", "Lorena", "Javier", "Celia", "Mateo", "Adriana", "Rubén", "Gloria",
    "Daniel", "Mónica", "Alberto", "Victoria", "Ernesto", "Pilar", "Gustavo", "Natalia",
    "Fernando", "Olga", "Ignacio", "Susana", "Ángel", "Marina", "Esteban", "Eva", "Bruno",
]


@dataclass
class Scenario:
    message: Message
    origin: Source  # where the seed node first saw the message
    contact_trust: float = 50.0  # stand-in trust for a message forwarded by a contact
    prior_range: tuple = (0.15, 0.5)
    stance_options: tuple = ("for", "against", None)


@dataclass
class Variant:
    id: int
    parent: int | None
    text: str
    author: int | None  # node that wrote it; None for the original
    step: int
    mutation: str
    emotion: float | None = None
    extremity: float | None = None


@dataclass
class NodeState:
    name: str
    prior: float
    stance: str | None
    belief: float
    believes: bool = False
    exposed_step: int | None = None
    shared_step: int | None = None
    received: int | None = None  # variant id last seen
    forwarded: int | None = None  # variant id it shared
    times_seen: int = 0
    history: list = field(default_factory=list)  # (step, belief) after each exposure


def make_people(scenario: Scenario, n: int, rng: np.random.Generator) -> list[Person]:
    lo, hi = scenario.prior_range
    people = []
    for i in range(n):
        stance = scenario.stance_options[int(rng.integers(len(scenario.stance_options)))]
        people.append(Person(NAMES[i % len(NAMES)], float(rng.uniform(lo, hi)), stance))
    return people


def persona(person: Person, message: Message) -> str:
    text = f"{person.name}, who {persona_sentence(person.prior_belief)}."
    if person.stance and person.stance in message.stance_phrases:
        text += f" {person.name} {message.stance_phrases[person.stance]}."
    return text


def upper_bound_estimate(n_nodes: int, scenario: Scenario, max_steps: int) -> dict:
    """Worst case: every node decides once per step. Real runs use far fewer calls."""
    probe = encode(Person("Probe", 0.3, "for"), scenario.message,
                   Source("Probe, a contact of Probe in the neighborhood chat", 50), shared_by=3,
                   times_seen=3)
    return budget.estimate([(probe.text, SPREAD_QUESTIONS)] * (n_nodes * max_steps)
                           + [(scenario.message.text, VARIANT_QUESTIONS)] * n_nodes)


def simulate(engine, rewriter, scenario: Scenario, graph_seed: int = 0, run_seed: int = 0,
             max_steps: int = 20, scorer=None, seed_node: int | None = None, logger=None,
             dry_run: bool = True, confirm: bool = False) -> dict | None:
    """Run one spread. scorer: a JevEngine that rates each new version (None skips scoring).

    Live API calls need dry_run=False. With a cache-only (offline) JevEngine nothing is billed,
    so the dry-run gate is skipped.
    """
    g = build_network(graph_seed)
    n = g.number_of_nodes()
    live_engines = [e for e in (engine, scorer) if isinstance(e, JevEngine) and not e.offline]
    if live_engines and not budget.check(upper_bound_estimate(n, scenario, max_steps),
                                         dry_run=dry_run, confirm=confirm):
        return None

    rng = np.random.default_rng(run_seed)
    people = make_people(scenario, n, rng)
    nodes = [NodeState(p.name, p.prior_belief, p.stance, p.prior_belief) for p in people]
    seed = highest_degree_node(g) if seed_node is None else seed_node
    tag = f"g{graph_seed}:r{run_seed}"

    variants = [Variant(0, None, scenario.message.text, None, 0, "original")]
    events: list[dict] = []

    def score(v: Variant):
        if scorer is None:
            return
        d = scorer.decide(EncodedState(text=v.text, features={}), VARIANT_QUESTIONS)
        v.emotion = expected_score(d.probs["emotion"])
        v.extremity = expected_score(d.probs["extremity"])

    score(variants[0])
    # The seed node starts the spread: it read the original and forwards it unchanged.
    s0 = nodes[seed]
    s0.exposed_step = s0.shared_step = 0
    s0.received = s0.forwarded = 0
    s0.times_seen = 1
    s0.believes, s0.belief = True, 0.9  # the seed starts the rumor, so it is taken to believe it
    events.append({"step": 0, "node": seed, "from": None, "variant": 0, "kind": "seed"})

    metrics = [_metrics(0, nodes, variants, [0])]
    for step in range(1, max_steps + 1):
        sharers = [i for i, s in enumerate(nodes) if s.shared_step == step - 1]
        if not sharers:
            break
        exposures: dict[int, list[int]] = {}
        for i in sharers:
            for j in sorted(g.neighbors(i)):
                if nodes[j].shared_step is None:
                    exposures.setdefault(j, []).append(i)

        circulating = []
        for j in sorted(exposures):
            senders = exposures[j]
            sender = senders[int(rng.integers(len(senders)))]
            node, person = nodes[j], people[j]
            node.times_seen += len(senders)
            node.exposed_step = step if node.exposed_step is None else node.exposed_step
            vid = nodes[sender].forwarded
            message = Message(variants[vid].text, scenario.message.emotion,
                              scenario.message.direction, scenario.message.stance_phrases)
            source = Source(f"{nodes[sender].name}, a contact of {person.name} in the "
                            "neighborhood chat", scenario.contact_trust)
            state = encode(person, message, source, shared_by=len(senders),
                           times_seen=node.times_seen,
                           belief=None if node.times_seen == len(senders) else node.belief)
            decision = engine.decide(state, SPREAD_QUESTIONS, replicate=f"{tag}:s{step}:n{j}")

            node.belief = decision.probs["believe_p"]["true"]
            node.believes = sample_label(decision.probs["believe_p"], rng) == "true"
            node.received = vid
            node.history.append((step, node.belief))
            shares = sample_label(decision.probs["share"], rng) == "true"
            event = {"step": step, "node": j, "from": sender, "variant": vid,
                     "belief": node.belief, "believes": node.believes,
                     "p_share": decision.probs["share"]["true"], "shares": shares,
                     "mutation_probs": decision.probs["mutation"]}
            if shares:
                mutation = sample_label(decision.probs["mutation"], rng)
                out = rewriter.rewrite(variants[vid].text, mutation, persona(person, message),
                                       replicate=f"{tag}:s{step}:n{j}")
                if out["text"] != variants[vid].text:
                    new = Variant(len(variants), vid, out["text"], j, step, mutation)
                    score(new)
                    variants.append(new)
                    vid = new.id
                node.shared_step, node.forwarded = step, vid
                circulating.append(vid)
                event.update(mutation=mutation, forwarded=vid)
            events.append(event)
            if logger is not None:
                logger.log(state, SPREAD_QUESTIONS, decision, run=tag, step=step, node=j,
                           sender=sender, variant=event["variant"], shares=shares,
                           mutation=event.get("mutation"))
        metrics.append(_metrics(step, nodes, variants, circulating))

    pos = {v: g.nodes[v]["pos"] for v in g.nodes}
    return {
        "engine": engine.name,
        "graph_seed": graph_seed,
        "run_seed": run_seed,
        "seed_node": seed,
        "scenario": {"message": scenario.message.text, "origin": scenario.origin.description},
        "graph": {"nodes": [{"id": v, "x": pos[v][0], "y": pos[v][1]} for v in g.nodes],
                  "edges": [{"a": a, "b": b, "kind": d["kind"]} for a, b, d in g.edges(data=True)]},
        "nodes": [asdict(s) for s in nodes],
        "variants": [asdict(v) for v in variants],
        "events": events,
        "metrics": metrics,
    }


def _metrics(step: int, nodes: list[NodeState], variants: list[Variant], circulating: list[int]):
    n = len(nodes)
    em = [variants[v].emotion for v in circulating if variants[v].emotion is not None]
    ex = [variants[v].extremity for v in circulating if variants[v].extremity is not None]
    return {
        "step": step,
        "shared": sum(s.shared_step is not None for s in nodes) / n,
        "exposed": sum(s.exposed_step is not None for s in nodes) / n,
        "believe": sum(s.belief > 0.5 for s in nodes) / n,
        # Jev often answers 0.0 or 1.0; after clipping those count as ~0.05 bits.
        "uncertainty": float(np.mean([binary_entropy(s.belief) for s in nodes])),
        "variants": len(variants),
        "new_shares": len(circulating),
        "emotion": float(np.mean(em)) if em else None,
        "extremity": float(np.mean(ex)) if ex else None,
    }
