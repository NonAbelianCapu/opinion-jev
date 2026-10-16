"""Run the mutating spread for one or more seeds and save the results as JSON.

  uv run python scripts/run_spread.py --scenario pool --engine jev --seeds $(seq 0 19) --live
  uv run python scripts/run_spread.py --scenario pool --engine jev --seeds $(seq 0 19)  # cache only
"""

import argparse
import json
from pathlib import Path

from jevsim.cache import DiskCache
from jevsim.engines import HttpTransport, JevEngine, StandInEngine
from jevsim.logger import JsonlLogger
from jevsim.rewriter import OpenRouterRewriter
from jevsim.scenarios import SCENARIOS
from jevsim.simulator.dynamics import simulate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["jev", "standin"], default="jev")
    ap.add_argument("--scenario", choices=sorted(SCENARIOS), default="bins")
    ap.add_argument("--graph-seed", type=int, default=0)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0],
                    help="run seeds; 'a-b' style ranges are not supported, list them or use seq")
    ap.add_argument("--max-steps", type=int, default=20)
    ap.add_argument("--live", action="store_true", help="allow API calls (otherwise cache only)")
    ap.add_argument("--confirm", action="store_true", help="needed when the estimate is above $1")
    ap.add_argument("--out", default="results/spread")
    args = ap.parse_args()

    cache = DiskCache("results/cache")
    jev = JevEngine(HttpTransport() if args.live else None, cache, offline=not args.live)
    engine = jev if args.engine == "jev" else StandInEngine()
    rewriter = OpenRouterRewriter(cache, offline=not args.live)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for seed in args.seeds:
        name = f"{args.scenario}_{args.engine}_g{args.graph_seed}_r{seed}"
        (out_dir / f"{name}.jsonl").unlink(missing_ok=True)  # one log per run, not appended replays
        result = simulate(engine, rewriter, SCENARIOS[args.scenario], graph_seed=args.graph_seed, run_seed=seed,
                          max_steps=args.max_steps, scorer=jev,
                          logger=JsonlLogger(out_dir / f"{name}.jsonl"),
                          dry_run=False, confirm=args.confirm)
        result["scenario"]["name"] = args.scenario
        (out_dir / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))
        last = result["metrics"][-1]
        print(f"{name}: steps={last['step']} shared={last['shared']:.0%} "
              f"believe={last['believe']:.0%} versions={last['variants']}")


if __name__ == "__main__":
    main()
