#!/bin/sh

exec 3>&1 # FD3 points to original stdout (console)

WARM_UP_FPS=5 # 5
RUNS=20 # 20
TIMEOUT_WARM=30 # 30 s (in secs)
TIMEOUT_RUN=120 # 2 minutes (in secs)
B_DELAY=30

VIDEO_DEV=/dev/video2

CMD_CAM="gst-launch-1.0 -v v4l2src device=$VIDEO_DEV ! image/jpeg,width=640,height=480,framerate=30/1 ! jpegdec ! videoconvert ! x264enc bitrate=10000 tune=zerolatency ! rtph264pay config-interval=10 pt=96 ! fpsdisplaysink video-sink=\"udpsink host=192.168.1.37 port=5000\" text-overlay=false"

run_fps(){
	run="$1"
	run_nr="$2"
	timeout="$3"

	$CMD_CAM >> "fps_${run}_${run_nr}_${timeout}.log" 2>&1 & # Run command in the background
	GST_PID=$!

	# # Wait for application to initialize
	#sleep 1

	#GST_PID=$(ps -eo pid,comm | grep 'gst-launch' | awk '{print $1}')
	# printf "\n>> %s -> Run %s: Running GST (PID = %s) for %s seconds...\n\n" "$run" "$run_nr" "$GST_PID" "$timeout" >&3

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
while [ "$j" -lt "$WARM_UP_FPS" ]; do
	j=$((j + 1))
	run_fps "WARM_UP_FPS" "$j" "$TIMEOUT_WARM"
done

sleep "$B_DELAY"

# Run
j=0
while [ "$j" -lt "$RUNS" ]; do
	j=$((j + 1))
	run_fps "TEST" "$j" "$TIMEOUT_RUN"
	if [ "$((j % 3))" -eq 0  ]; then
		echo "IF branch: $j"
		sleep "$B_DELAY"
	fi
done

