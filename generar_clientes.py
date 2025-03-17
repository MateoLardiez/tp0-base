import sys

def generar_clientes(n):
    clientes = ""

    for i in range(1,n+1):
        clientes += f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
    """

    return clientes

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("ERROR: No se envian las variables correctamente")
        sys.exit(1)

    num_clientes = int(sys.argv[1])
    print(generar_clientes(num_clientes))