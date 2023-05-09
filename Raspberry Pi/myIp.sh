#!/bin/sh -e

IP=$(hostname -I) || true
if [ "$IP" ]; then
        echo "\nMy IP address is $IP\n"
else
        echo "\nSorry, no IP address yet\n"
fi
