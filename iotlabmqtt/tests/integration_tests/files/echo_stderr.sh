#! /bin/bash

# Usage: echo_stderr.sh
#
# Echo messages read on stdin to stderr

main() {
    local line
    while IFS= read -r line
    do
        echo ${line} >&2
    done
}


main
