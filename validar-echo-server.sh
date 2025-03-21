#!/bin/bash

# docker compose -f docker-compose-levantar-servidor.yaml up -d --build # Levanto red y servidor

# sleep 1

msg="Mensaje de prueba"

respuesta=$(echo "$msg" | nc server 12345)

if [ "$respuesta" == "$mensaje" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi

#make docker-compose-down

