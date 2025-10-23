#!/bin/sh
QUERIES="${1:-${QUERIES:-18}}"  # Default to 30 if unset
CMD="work_queue status"
FIFO_PATH="/tmp/px4_fifo" # FIFO Path
UPDATE_INTERVAL=10 # 10 secs
WARM_UP=5
REPS=20

wq_run(){
	run="$1"
	rm -f "$FIFO_PATH"
	mkfifo "$FIFO_PATH"

	# Start PX4 with input from the FIFO
	echo ">> Run $run"
	printf "\n=========== Starting PX4: Queries = %s =========\n" "$QUERIES"
	./bin/px4 -s pilotpi_mc.config < "$FIFO_PATH" &
	PX4_PID=$!  # Capture PID immediately

	# Wait for PX4 to initialize (adjust sleep time if needed)
	sleep 2

	# Open FIFO for writing in a non-blocking way (using file descriptor 3)
	exec 3>"$FIFO_PATH"  # This keeps the FIFO open for writing

	# For i in QUERIES, run $CMD
	i=0
	while [ "$i" -lt "$QUERIES" ]; do
		echo "$CMD" >&3  # Write to the FIFO via file descriptor 3
		sleep "$UPDATE_INTERVAL"
		i=$((i + 1))
	done

	# Send shutdown command
	echo "shutdown" >&3

	# Close the FIFO and wait for PX4 to exit
	exec 3>&-  # Close file descriptor 3
	wait "$PX4_PID" 2>/dev/null  # Suppress "pid not found" errors

	# Cleanup
	rm -f "$FIFO_PATH"
}

# Seed random generator (if needed)
cat /dev/random | head > /dev/null

# Warmup
perf stat --table -n -r $WARM_UP --timeout=30000 ./bin/px4 -s pilotpi_mc.config
# Run
j=0
while [ "$j" -lt "$REPS" ]; do
	j=$((j + 1))
	wq_run "$j"
done
