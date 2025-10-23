#!/bin/sh

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

# Final status
post_proc_fps
post_proc_px4
echo ""
echo "All benchmarks completed in $ELAPSED_STR!"
echo "PX4 log: px4.log ($(wc -l < px4.log) lines)"
echo "FPS log: fps.log ($(wc -l < fps.log) lines)"
