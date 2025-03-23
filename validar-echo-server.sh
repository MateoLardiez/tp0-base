#!/bin/bash

MSG="Mensaje de prueba"

RESPONSE=$(docker run --rm --network=tp0_testing_net busybox sh -c "echo '$MSG' | nc -w 5 server 12345")

if [ "$RESPONSE" = "$MSG" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
