#!/bin/sh
WARM_UP=5
RUNS=20
TIMEOUT_WARM=30 # 30 s
TIMEOUT_RUN=120 # 2 minutes

CMD="gst-launch-1.0 -v v4l2src device=/dev/video0 ! image/jpeg,width=640,height=480,framerate=30/1 ! jpegdec ! videoconvert ! x264enc bitrate=10000 tune=zerolatency ! rtph264pay config-interval=10 pt=96 ! fpsdisplaysink video-sink=\"udpsink host=192.168.1.37 port=5000\" text-overlay=false"

run_fps(){
	run="$1"
	run_nr="$2"
	timeout="$3"

	printf "\n>> %s -> Run %s: Running GST for %s seconds...\n\n" "$run" "$run_nr" "$timeout"
	$CMD & # Run command in the background
	GST_PID=$! # Capture PID immediately
	
	# Wait for application to initialize
	sleep 1

	# Wait for program to run
	sleep $timeout

	# Kill program and wait for it to finish
    kill -TERM $GST_PID
	wait "$GST_PID" 2>/dev/null # Supress PID not found error
}

# Seed random generator (if needed)
cat /dev/random | head > /dev/null

# Warmup
j=0
while [ "$j" -lt "$WARM_UP" ]; do
	j=$((j + 1))
	run_fps "WARM_UP" "$j" "$TIMEOUT_WARM"
done

# Run
j=0
while [ "$j" -lt "$RUNS" ]; do
	j=$((j + 1))
	run_fps "TEST" "$j" "$TIMEOUT_RUN"
done


