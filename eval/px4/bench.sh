#!/bin/sh
MIBENCH_DIR=$(realpath "$(dirname "$0")")

# Seed random generator (optional)
cat /dev/random | head > /dev/null

benchmark() {
  (
    # Navigate to the benchmark directory (exit on failure)
    cd "$MIBENCH_DIR/automotive/qsort" || exit 1
    echo "-> mibench/automotive/qsort-small"

    warm_up="$1"
    reps="$2"
    events="$3"
    cmd="$4"

    # Warm-up runs (output discarded)
    for _ in $(seq "$warm_up"); do
      "$cmd" input_small.dat > /dev/null
    done

    # Actual benchmark (output saved once)
    perf stat --table -n -r "$reps" "$events" \
      "$cmd" input_small.dat > output_small.txt
  )
}

# Run benchmarks
benchmark 10 35 "-e r08:uk,r08:h,r09:uk,r09:h,r17:uk,r17:h" "./qsort_small"
benchmark 10 35 "-e r02:uk,r02:h,r05:uk,r05:h" "./qsort_small"
