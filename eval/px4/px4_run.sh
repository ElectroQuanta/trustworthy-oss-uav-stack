#!/bin/sh
WARM_UP=5
REPS=20
TIMEOUT=30000 # ms

# Seed random generator (if needed)
cat /dev/random | head > /dev/null

px4_bench(){
	events="$1"
	reps="$2"
	timeout="$3"

	printf "\n--- EVENTS: ${events}: RUNS=$reps; timeout=$timeout ---\n"
	printf "-> mibench/automotive/5Warm-20Runs\n"
	perf stat --table -n -r $reps "$events" --timeout=$timeout ./bin/px4 -s pilotpi_mc.config
}

# Run benchmarks for each event set
EVENTS="-e r08:uk,r08:h,r09:uk,r09:h,r17:uk,r17:h"
px4_bench "$EVENTS" $WARM_UP $TIMEOUT
px4_bench "$EVENTS" $REPS $TIMEOUT

EVENTS="-e r02:uk,r02:h,r05:uk,r05:h"
px4_bench "$EVENTS" $WARM_UP $TIMEOUT
px4_bench "$EVENTS" $REPS $TIMEOUT
