#!/bin/sh

UPDT_INTERVAL=30 # 30 secs

# Clear previous logs
rm -f *.log

kill_proc() {
	proc="$1"
	KILL_PID=$(ps -eo pid,args | grep "$proc" | awk '{print $1}')
	kill -s KILL $KILL_PID 2>/dev/null # supress PID not found error
	sleep 2
}

post_proc_fps() {
	# Clear existing log
	> fps.log

	# Add this to the end of your script
	echo "========== Building Combined Log"

	# Process files in run order
	for file in $(ls fps_TEST_*_*.log | sort -V); do
		# Parse filename components
		file_stem="${file%.log}"
		old_IFS="$IFS"
		IFS='_'
		set -- $file_stem
		IFS="$old_IFS"
		
		run_number="$3"
		timeout="$4"
		
		# Add header
		printf "\n>> TEST -> Run %s: Running for %s seconds...\n\n" "$run_number" "$timeout" >> fps.log
		
		# Append content
		cat "$file" >> fps.log
	done

	echo "========== Combined log created: fps.log"
}

post_proc_px4() {
	# Combine logs with headers
	> px4.log  # Clear combined log

	# Process files in run order
	for file in $(ls px4_*.log | sort -V); do
		# Parse filename components
		file_stem="${file%.log}"
		old_IFS="$IFS"
		IFS='_'
		set -- $file_stem
		IFS="$old_IFS"
		run_number="$2"  # Now $2 is the run number
		
		# Add header
		printf "\n>> Run %s\n\n" "$run_number" >> px4.log
		
		# Append content
		cat "$file" >> px4.log
	done
}

kill_proc '[p]x4_wq'
kill_proc '[c]am_fps'
kill_proc '[p]x4 -s'
kill_proc '[gst]-launch'

# Run both benchmarks in parallel
./px4_wq_uspfs.sh > px4.log 2>&1 &
PX4_WQ_PID=$!
./cam_fps_uspfs.sh > fps.log 2>&1 &
CAM_PID=$!

# # Wait for application to initialize
# sleep 2

# # Wait for completion and show exit status
# PX4_WQ_PID=$(ps -eo pid,comm | grep '[p]x4_wq' | awk '{print $1}')
# # Wait for completion and show exit status
# CAM_PID=$(ps -eo pid,comm | grep '[c]am_fps' | awk '{print $1}')

# Store start time
START_TIME=$(date +%s)

# Initial status
echo "Benchmarks started at $(date)"
echo "PX4 PID: $PX4_WQ_PID | FPS PID: $CAM_PID"
echo "---------------------------------------"

# Progress monitoring loop
while true; do
    # Check if processes are still running
    PX4_RUNNING=0
    CAM_RUNNING=0
    kill -0 $PX4_WQ_PID 2>/dev/null && PX4_RUNNING=1
    kill -0 $CAM_PID 2>/dev/null && CAM_RUNNING=1
    
    # Calculate elapsed time
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))
    ELAPSED_STR=$(printf "%02d:%02d" $((ELAPSED/60)) $((ELAPSED%60)))
    
    # Print status
    echo "[$ELAPSED_STR] | PX4: $( [ $PX4_RUNNING -eq 1 ] && echo "On " || echo "Off" ) | FPS: $( [ $CAM_RUNNING -eq 1 ] && echo "On " || echo "Off" )"
    
    # Exit condition
    [ $PX4_RUNNING -eq 0 ] && [ $CAM_RUNNING -eq 0 ] && break
    
    # Wait for next update
    sleep $UPDT_INTERVAL
done

# Final status
post_proc_fps
post_proc_px4
echo ""
echo "All benchmarks completed in $ELAPSED_STR!"
echo "PX4 log: px4.log ($(wc -l < px4.log) lines)"
echo "FPS log: fps.log ($(wc -l < fps.log) lines)"
