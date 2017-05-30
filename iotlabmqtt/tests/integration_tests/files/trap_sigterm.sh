#!/bin/bash

trap "echo 'Process caught SIGTERM'" SIGTERM

while sleep 1
do
    :
done
exit($?)
