"""Run many (state, replicate) decisions through one engine with the budget guard in front."""

from jevsim import budget
from jevsim.engines.jev import JevEngine
from jevsim.logger import JsonlLogger


def run_batch(engine, items: list[dict], questions: dict, logger: JsonlLogger | None = None,
              dry_run: bool = True, confirm: bool = False) -> list[dict]:
    """items: dicts with 'state' (EncodedState), optional 'replicate' and any tags to log.

    For JevEngine, only uncached items count toward the estimate. In dry-run nothing is sent
    and only cached items are returned.
    """
    pending = items
    if isinstance(engine, JevEngine):
        pending = [it for it in items
                   if engine.key(it["state"], questions, it.get("replicate", 0)) not in engine.cache]
        live = budget.check(budget.estimate([(it["state"].text, questions) for it in pending]),
                            dry_run=dry_run, confirm=confirm)
        if not live:
            pending_ids = {id(it) for it in pending}
            items = [it for it in items if id(it) not in pending_ids]

    records = []
    for it in items:
        rep = it.get("replicate", 0)
        decision = engine.decide(it["state"], questions, replicate=rep)
        tags = {k: v for k, v in it.items() if k != "state"}
        if logger is not None:
            records.append(logger.log(it["state"], questions, decision, **tags))
        else:
            records.append({"probs": decision.probs, **decision.meta, **tags})
    return records
