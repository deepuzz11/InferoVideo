#!/usr/bin/env python3
"""
InferaVideo Pipeline CLI
========================
Usage:
    python run_pipeline.py --url "https://youtu.be/dQw4w9WgXcQ"
    python run_pipeline.py --url <url> --whisper small --search embeddings
    python run_pipeline.py --job <job_id> --stages transcribe segment
    python run_pipeline.py --job <job_id> --query "what is machine learning"
"""
from __future__ import annotations
import argparse, os, sys, time, logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("cli")


def _bar(pct: int, w: int = 28) -> str:
    f = int(w * pct / 100)
    return f"[{'█'*f}{'░'*(w-f)}] {pct:3d}%"


def _banner():
    print("""
  ╔════════════════════════════════════╗
  ║    InferaVideo  ·  Pipeline CLI    ║
  ╚════════════════════════════════════╝
""")


def main():
    p = argparse.ArgumentParser(description="InferaVideo pipeline runner")
    p.add_argument("--url",    help="Video URL to process")
    p.add_argument("--job",    help="Resume an existing job by ID")
    p.add_argument("--stages", nargs="+",
                   choices=["ingest","transcribe","segment","highlight","summarise"],
                   default=["ingest","transcribe","segment","highlight","summarise"])
    p.add_argument("--whisper",  default="base")
    p.add_argument("--search",   choices=["tfidf","embeddings"], default="tfidf")
    p.add_argument("--summarise",choices=["extractive","transformers"], default="extractive")
    p.add_argument("--query",    help="Run a search query after pipeline completes")
    p.add_argument("--top-k",    type=int, default=5)
    args = p.parse_args()

    os.environ.setdefault("INFRA_WHISPER_MODEL",    args.whisper)
    os.environ.setdefault("INFRA_SEARCH_BACKEND",   args.search)
    os.environ.setdefault("INFRA_SUMMARISE_BACKEND", args.summarise)

    from backend.app.services.pipeline import PipelineService
    from backend.app.models.video_job import StageStatus

    svc = PipelineService()
    _banner()

    if args.job:
        try:
            job = svc.get_job(args.job)
            print(f"  Resuming  {job.job_id}\n")
        except FileNotFoundError:
            logger.error("Job '%s' not found", args.job); sys.exit(1)
    elif args.url:
        job = svc.create_job()
        print(f"  New job   {job.job_id}\n")
    else:
        p.error("Provide --url or --job")

    stage_fns = {
        "ingest":     lambda: svc.run_ingest(job, args.url),
        "transcribe": lambda: svc.run_transcribe(job),
        "segment":    lambda: svc.run_segment(job),
        "highlight":  lambda: svc.run_highlight(job),
        "summarise":  lambda: svc.run_summarise(job),
    }

    for stage in args.stages:
        print(f"  ▶  {stage.upper():<12}", end=" ", flush=True)
        t0 = time.time()
        try:
            stage_fns[stage]()
            print(f"✓  {time.time()-t0:.1f}s")
        except Exception as exc:
            print(f"✗  FAILED  ({exc})")
            break

    job = svc.get_job(job.job_id)
    print(f"\n  {_bar(job.progress_pct)}  {job.overall_status.upper()}")
    print(f"\n  Job ID    {job.job_id}")
    if job.meta.title:           print(f"  Title     {job.meta.title}")
    if job.meta.duration_seconds:
        from backend.app.utils.time import seconds_to_hms
        print(f"  Duration  {seconds_to_hms(job.meta.duration_seconds)}")
    if job.meta.segment_count:   print(f"  Segments  {job.meta.segment_count}")
    if job.meta.chapter_count:   print(f"  Chapters  {job.meta.chapter_count}")
    if job.meta.highlight_count: print(f"  Clips     {job.meta.highlight_count}")
    if job.error: print(f"\n  ✗ Error [{job.error_stage}]: {job.error}")

    if args.query and job.transcript_path:
        print(f"\n  Search: '{args.query}'\n")
        from backend.app.utils.time import seconds_to_hms
        for i, r in enumerate(svc.search(job.job_id, args.query, args.top_k, args.search), 1):
            print(f"  {i}. [{seconds_to_hms(r['start'])}]  {r['text'][:100]}")
    print()


if __name__ == "__main__":
    main()
