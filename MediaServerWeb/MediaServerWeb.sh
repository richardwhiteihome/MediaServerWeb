#!/bin/bash


# Define constants
readonly BASE_DIR="/home/adm-user/MediaServerTool/"
readonly LOG_FILE="${BASE_DIR}/log/MediaServerWeb.run.log"
readonly SCRIPT_DIR="${BASE_DIR}"
readonly PYTHON_SCRIPT="MediaServerWeb.py"
readonly LOCK_FILE="${BASE_DIR}/mediaserverweb.lock"
readonly TEMP_DIR="${BASE_DIR}/temp"


# Function to log messages with timestamps
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] - $message" >> "$LOG_FILE"
}

# Function to cleanup resources
cleanup() {
    log_message "INFO" "Cleaning up resources"
    stop_media_gui
    rm -f "$LOCK_FILE"
}

# Function to check and create directories
ensure_directories() {
    local dirs=("$TEMP_DIR" "$(dirname "$LOG_FILE")")
    for dir in "${dirs[@]}"; do
        if ! [[ -d "$dir" ]]; then
            mkdir -p "$dir" || {
                log_message "ERROR" "Failed to create directory: $dir"
                return 1
            }
        fi
    done
}


# Function to create lock file
create_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid
        pid=$(cat "$LOCK_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 1
        fi
        # Remove stale lock
        rm -f "$LOCK_FILE"
    fi
    echo $$ > "$LOCK_FILE"
    return 0
}

stop_media_gui(){

    # Kill timeout enforcer
    
    pkill -9 -f "MediaServerWeb"
    log_message "INFO" "MediaLoader process completed successfully"

}

# Main execution block
main() {
    # Ensure required directories exist
    ensure_directories || exit 1

    # Change to script directory
    cd "$SCRIPT_DIR" || {
        log_message "ERROR" "Failed to change to script directory"
        exit 1
    }

    # Create lock file
    if ! create_lock ; then
        log_message "ERROR" "Script is already running. Exiting."
        exit 1
    fi

    # # Set up cleanup trap
    # #trap cleanup EXIT
    # #trap 'log_message "ERROR" "Script terminated unexpectedly"; exit 1' ERR SIGINT SIGTERM

    # # Start timeout enforcer
    # #enforce_timeout

    # Log start
    log_message "INFO" "Starting MediaLoader process"


    # Execute main script with error handling
    if ! python3 "$PYTHON_SCRIPT"; then
        log_message "ERROR" "Python script execution failed"
        exit 1
    fi

}





function usage {


    echo "    _  _  ____  ____  __   __   ____  ____  ____  _  _  ____  ____  _  _  ____  ____ "
    echo "   ( \/ )(  __)(    \(  ) / _\ / ___)(  __)(  _ \/ )( \(  __)(  _ \/ )( \(  __)(  _ \" "
    echo "   / \/ \ ) _)  ) D ( )( /    \\___ \ ) _)  )   /\ \/ / ) _)  )   /\ /\ / ) _)  ) _ ("
    echo "   \_)(_/(____)(____/(__)\_/\_/(____/(____)(__\_) \__/ (____)(__\_)(_/\_)(____)(____/"
    echo " "                                                                  

    echo "Usage: start|restart|stop|status"
    echo
}

if [ $# -lt 1 ]; 
then
  usage 
  exit 1
fi
if [ $1 == "start" ]
then
  main
elif [ $1 == "restart" ]
then
  cleanup
  main
elif [ $1 == "stop" ]
then
  echo 'stopping'
  cleanup
else
  usage 
  exit 1
fi
