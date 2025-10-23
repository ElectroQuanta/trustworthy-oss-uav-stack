#!/bin/sh

# Default variables
WIDTH=1280
HEIGHT=720
FRAMERATE=30
ROTATION=180
HOST_IP=192.168.1.37
PORT=5000

# Function to check if a port is in use using netstat
check_port() {
    if netstat -uln | grep -q ":$1\b"; then
        echo "Error: Port $1 is already in use."
        return 1
    fi
    return 0
}

# Parse command-line arguments for HOST_IP and PORT
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --host) HOST_IP="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Check if rpicam-vid is installed
if ! command -v rpicam-vid &> /dev/null; then
    echo "Error: rpicam-vid is not installed or not in PATH."
    exit 1
fi

# Check if gst-launch-1.0 is installed
if ! command -v gst-launch-1.0 &> /dev/null; then
    echo "Error: gst-launch-1.0 is not installed or not in PATH."
    exit 1
fi

# Check if the specified port is already in use
if ! check_port "${PORT}"; then
    echo "Please provide an alternative port using the --port option."
    exit 1
fi

# Define the video capture and streaming commands
video_capture_cmd="rpicam-vid -n --fullscreen=0 --listen=1 \
                  --width=${WIDTH} --height=${HEIGHT} \
                  --bitrate=10000000 --framerate=${FRAMERATE} \
                  --rotation=${ROTATION} -t 0 -o -"

video_streaming_cmd="gst-launch-1.0 -v fdsrc ! queue ! h264parse ! \
                     rtph264pay config-interval=1 pt=96 ! \
                     udpsink host=${HOST_IP} \
                     port=${PORT} auto-multicast=0"

# Execute the video capture and streaming commands
${video_capture_cmd} | ${video_streaming_cmd}
