#! /bin/bash

# Usage: print_stdout.sh [NUM] [STEP]
#    NUM: number of iterations
#    STEP: delay between each print ('sleep' command syntax)
#
# Print NUM messages on stdout every STEP

main() {
    local num=$1
    local delay=$2
    local i

    for i in $(seq ${num})
    do
        sleep ${delay}
        echo "Message $i"
    done
}


main $@
