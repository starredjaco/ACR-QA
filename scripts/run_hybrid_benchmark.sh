#!/bin/bash
cd /home/ahmeed/Documents/KSIU/GRAD/SOLO
echo "Starting hybrid benchmark at $(date)"
.venv/bin/python scripts/run_realvuln_hybrid.py --all 2>&1 | tee /tmp/hybrid_benchmark_run.log
echo "Finished at $(date)"
