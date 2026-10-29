import argparse, json
from model import run_phase

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["development", "held"])
    p.add_argument("--root", default=".")
    p.add_argument("--output", default="results")
    a = p.parse_args()
    if a.phase == "held":
        from verify_freeze import verify

        verify(a.root)
    print(json.dumps(run_phase(a.root, a.phase, a.output)))
