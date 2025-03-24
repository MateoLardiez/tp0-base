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
    networks:
      - testing_net
    volumes:
      - ./client/config.yaml:/config.yaml
    depends_on:
      - server
    """

    return clientes

if len(sys.argv) != 2:
  raise Exception("ERROR: Se deben recibir exactamente 2 parametros")
    
try:  
  num_clientes = int(sys.argv[1])
except:
  raise Exception("No se esta pasando un entero como parametro")

if num_clientes < 0:
  raise Exception("La cantidad de clientes debe ser un numero positivo")    

print(generar_clientes(num_clientes))