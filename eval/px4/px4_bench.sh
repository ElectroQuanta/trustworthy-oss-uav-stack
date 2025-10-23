#!/bin/sh
WARM_UP=5
REPS=20

# Seed random generator (if needed)
cat /dev/random | head > /dev/null

# Run benchmarks for each event set
DURATION=10
seq $WARM_UP | xargs -Iz ./px4_wrapper.sh $DURATION
EVENT="-e r08:uk,r08:h,r09:uk,r09:h,r17:uk,r17:h"
# DURATION=30
TIMEOUT=30000 # ms
perf stat --table -n -r $REPS $EVENT --timeout=$TIMEOUT ./bin/px4 -s pilotpi_mc.config 

DURATION=10
seq $WARM_UP | xargs -Iz ./px4_wrapper.sh $DURATION
EVENT="-e r02:uk,r02:h,r05:uk,r05:h"
# DURATION=30
TIMEOUT=30000 # ms
perf stat --table -n -r $REPS $EVENT --timeout=$TIMEOUT ./bin/px4 -s pilotpi_mc.config 
# perf stat --table -n -r $REPS $EVENT ./px4_wrapper.sh $DURATION
