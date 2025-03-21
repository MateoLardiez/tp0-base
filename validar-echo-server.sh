#!/bin/bash

# docker compose -f docker-compose-levantar-servidor.yaml up -d --build # Levanto red y servidor

# sleep 1

msg="Mensaje de prueba"

SERVER="server:12345"


respuesta=$(echo "$msg" | docker run --rm --network=tp0_testing_net busybox nc server 12345)

if [ "$respuesta" == "$mensaje" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi

#make docker-compose-down

