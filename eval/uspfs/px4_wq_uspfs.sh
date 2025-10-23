#!/bin/sh
#QUERIES="${1:-${QUERIES:-18}}"  # Default to 18 if unset
QUERIES=18  # Default to 18 if unset
CMD="work_queue status"
FIFO_PATH="/tmp/px4_fifo" # FIFO Path
UPDATE_INTERVAL=10 # 10 secs
WARM_UP=5 # 5 
REPS=20 # 20
BATCH_DELAY=30
TIMEOUT_PERF=30000 # 30 secs

wq_run(){
    run="$1"
    rm -f "$FIFO_PATH"
    mkfifo "$FIFO_PATH"

    # Individual log file for this run
    log_file="px4_${run}.log"
    
    # Start PX4 and redirect output
    ./bin/px4 -s pilotpi_mc.config < "$FIFO_PATH" >> "$log_file" 2>&1 &
    PX4_PID=$!
    # echo "PX4_PID {$PX4_PID}"
#    taskset -p 0x2 "$PX4_PID" # does not work.. not enough cores available

    # Open FIFO for writing *before* launching PX4.
    # Option 1: Open for writing only (if you only need to write)
    # exec 3>"$FIFO_PATH"
    # Option 2: Open for both reading and writing (prevents blocking on both ends)
    exec 3<>"$FIFO_PATH"

    # Send queries
    i=0
    while [ "$i" -lt "$QUERIES" ]; do
        echo "$CMD" >&3
        sleep "$UPDATE_INTERVAL"
        i=$((i + 1))
    done

    # Cleanup
    echo "shutdown" >&3
    exec 3>&- # close file descriptor 3
	sleep 2
	kill -s KILL "$PX4_PID"
    # wait "$PX4_PID" 2>/dev/null
    rm -f "$FIFO_PATH"
}

# Seed random generator
cat /dev/random | head > /dev/null

# Warmup (output not captured)
j=0
while [ "$j" -lt "$WARM_UP" ]; do
    j=$((j + 1))
	./bin/px4 -s pilotpi_mc.config > /dev/null &
	WPID=$!
	sleep 30
	kill -s KILL $WPID 2>/dev/null
	wait "$WPID" 2>/dev/null # Supress PID not found
done

sleep "$BATCH_DELAY"

# Main runs
j=0
while [ "$j" -lt "$REPS" ]; do
    j=$((j + 1))
    wq_run "$j"
	if [ "$((j % 4))" -eq 0  ]; then
		echo "IF branch: $j"
		sleep "$BATCH_DELAY"
	fi
done


#echo "Combined log created: px4.log"

# for file in $(ls px4_*.log | sort -V); do
#     IFS='_' read -ra parts <<< "${file%.log}"
#     run_number="${parts[1]}"
# 	echo "$run_number"
# 	echo "$file"
# done
