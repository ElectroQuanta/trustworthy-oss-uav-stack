#!/bin/sh

DURATION="${1:-${DURATION:-30}}" # if unset/empty, set it to 30

# Create a named pipe
FIFO_PATH="/tmp/px4_fifo"
rm -f "$FIFO_PATH"
mkfifo "$FIFO_PATH"

# Start PX4 with input from the FIFO
printf "\n=========== Starting PX4: Duration = $DURATION =========\n"
./bin/px4 -s pilotpi_mc.config < "$FIFO_PATH" &
PX4_PID=$(ps -eo pid,comm | grep '[p]x4' | awk '{print $1}')

# Wait for initialization
sleep 1

# Send "shutdown" to the FIFO after $DURATION seconds
echo "Running the process for $DURATION secs"
(sleep $DURATION; echo "shutdown") > "$FIFO_PATH" &

# Wait for PX4 to exit
wait $PX4_PID

# Cleanup
rm -f "$FIFO_PATH"
