#!/bin/bash

if [ $# -ne 2 ]; then
    echo "No se recibieron los parametros correctos"
    exit 1
fi

OUTPUT_FILE=$1
NUM_CLIENTS=$2

# 1) Creo o modifico el archivo yaml definiendo el servidor
cat > $OUTPUT_FILE <<EOL
name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
EOL

# 2) Agrego al yaml la definicion de los n clientes, que se genera en generar_clientes.py
python3 generar_clientes.py $NUM_CLIENTS >> $OUTPUT_FILE

# 3) Agrego la red
cat >> $OUTPUT_FILE <<EOL
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
EOL

echo "Archivo $OUTPUT_FILE generado correctamente con $NUM_CLIENTS clientes."
