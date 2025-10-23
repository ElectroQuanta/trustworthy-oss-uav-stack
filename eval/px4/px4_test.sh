#!/bin/sh
REPS=2  # Number of repetitions per event set
WARM_UP=10
DURATION=30     # Run duration in seconds
FORK_DURATION=2
CMD="./bin/px4 -s pilotpi_mc.config"

warmup_px4(){
    echo "Profile: warm up..."
    for _ in $(seq "$WARM_UP"); do
      "$CMD" &
      sleep $FORK_DURATION    # Allow time for process to fork properly
      # Find PX4 PID using ps/grep (POSIX-compliant)
      PX4_PID=$(ps -eo pid,comm | grep '[p]x4' | awk '{print $1}')
      if [ -z "$PX4_PID" ]; then
          echo "Error: PX4 process not found!"
          exit 1
      fi
      sleep 10

      echo "Profile: killing process"
      kill -TERM $PX4_PID
    done
    echo "Profile: warm up done..."
}

benchmark() {
    event=$1  # Accept event set as argument
    event_set="$2"  # Accept event set as argument
    echo "=== Benchmarking with events: $event ==="

    warmup_px4
    
    echo "Profile: Start..."
    perf stat --table -n -r $REPS $event "$CMD" > "perf_${event_set}_${i}.log" 2>&1 &
    sleep $FORK_DURATION    # Allow time for process to fork properly
    
    # Find PX4 PID using ps/grep (POSIX-compliant)
    PX4_PID=$(ps -eo pid,comm | grep '[p]x4' | awk '{print $1}')
    PERF_PID=$(ps -eo pid,comm | grep '[p]erf' | awk '{print $1}')
    echo "PX4_PID: $PX4_PID;   PERF_PID: $PERF_PID"
    
    if [ -z "$PX4_PID" ]; then
        echo "Error: PX4 process not found!"
        exit 1
    fi

    if [ -z "$PERF_PID" ]; then
        echo "Error: PERF process not found!"
        exit 1
    fi
    
    sleep $DURATION

    echo "Profile: killing processes"
    kill -TERM $PX4_PID
    kill -TERM $PERF_PID
    
    echo "Completed run $i/$REPETITIONS"
}

# Seed random generator (if needed)
cat /dev/random | head > /dev/null

# Run benchmarks for each event set
benchmark "-e r08:uk,r08:h,r09:uk,r09:h,r17:uk,r17:h" A
#benchmark "-e r02:uk,r02:h,r05:uk,r05:h"
