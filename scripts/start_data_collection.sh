#!/usr/bin/env bash

##############
# Parameters #
##############

GELLO_DIR="$HOME/gello/gello_software"
REAL_ROBOT_DIR="$HOME/gello/real_robot"

GELLO_ENV="gello_env"
REAL_ROBOT_ENV="gello_env"


###############
# Definitions #
###############

ask_yes_no() {
    local question="$1"

    while true; do
        read -p "$question (y/n): " answer
        case "$answer" in
            [Yy]) return 0 ;;
            [Nn]) return 1 ;;
            *) echo "Please enter y or n.";;
        esac
    done
}

wait_for_enter() {
    read -p "Press Enter to continue ..."
}

calibrate() {

    cd $GELLO_DIR
    conda run -n "${GELLO_ENV}" --no-capture-output \
        python scripts/gello_get_offset.py \
            --start-joints 0.0604 -0.3634 -0.0957 -2.1662 0.0611 1.6686 -2.4437 \
            --joint-signs 1 -1 1 -1 1 1 1 \
            --port /dev/serial/by-id/usb-FTDI_USB__-__Serial_Converter_FT94ER3L-if00-port0

}

launch_server() {

    cd $GELLO_DIR
    conda run -n "${GELLO_ENV}" \
        python experiments/launch_gello_server.py

}

start_data_collection() {

    cd $REAL_ROBOT_DIR
    conda run -n "${REAL_ROBOT_ENV}" --no-capture-output \
        python ./collect_data.py +collect_data=panda_102_gello

}

cleanup() {

    # Try to close the server nicely
    pkill -TERM -P "$1"  # Make sure to kill child processes due to conda run
    sleep 2

    # Check if the server is still running
    if kill -0 "$1" 2>/dev/null || pgrep -P "$1" > /dev/null; then
        # Forcefully close the server
        pkill -9 -P "$1"
        echo "⌛ Forecully terminated server with PID: $1."
    else
        echo "✨ Gracefully closed server with PID: $1"
    fi

}


#########
# Start #
#########

echo "

 ┌────────────────────────────────────────────────────────┐
 │  ______     ______     __         __         ______    │
 │ /\  ___\   /\  ___\   /\ \       /\ \       /\  __ \   │
 │ \ \ \__ \  \ \  __\   \ \ \____  \ \ \____  \ \ \/\ \  │
 │  \ \_____\  \ \_____\  \ \_____\  \ \_____\  \ \_____\ │
 │   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/ │
 │                                                        │
 └────────────────────────────────────────────────────────┘

"

# Calibration

if ask_yes_no "🔧 Do you want to calibrate GELLO?"; then
    # TODO instructions for gello
    echo "Please place the GELLO arm on its stand and ensure it is straight. If you are unsure, there is a reference picture in the README."
    wait_for_enter
    calibrate
else
    echo "Skipping calibration"
fi

# Launch GELLO server

echo "📡 Launching GELLO server in background ..."
launch_server &
SERVER_PID=$!
trap "cleanup $SERVER_PID" EXIT  # Ensure that server is closed

# Check if server is running

sleep 2
if kill -0 $SERVER_PID 2>/dev/null; then
    echo "✨ Successfully lauched with PID: $SERVER_PID"
else
    echo "🔥 Unsuccessful launch with PID: $SERVER_PID"
fi

# Start data collection

echo "🎬 Starting data collection ..."
start_data_collection
