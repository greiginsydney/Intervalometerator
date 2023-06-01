#!/bin/sh -e

# Thank you kaanw on the Pi forums for this one:
# https://forums.raspberrypi.com/viewtopic.php?t=122145&sid=f81d3c032658e2961f4ad3f85cb32f91&start=25

for i in 'seq 1 10';
do
        IP=$(hostname -I) || true
        if [ "$IP" ];
        then
                echo "\nMy IP address is $IP\n"
                break
        else
                echo "\nSorry, no IP address yet\n"
                /bin/sleep 2
        fi
done
