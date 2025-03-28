# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

 El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de:  **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target  | accion  |
|---|---|
|  `docker-compose-up`  | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers. |
| `docker-compose-down`  | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego  `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
|  `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |
| `docker-image`  | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto. |
| `build` | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_. |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar. 

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.


### Cliente
 se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:
 
1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up`  y luego  `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.  El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc. 

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).


### Ejercicio N°3:
Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `


### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.



#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).


### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). 
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del *batch* fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB. 

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
 (hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación. Respetar las entradas de log planteadas en los ejercicios, pues son las que se chequean en cada uno de los tests.

La corrección personal tendrá en cuenta la calidad del código entregado y casos de error posibles, se manifiesten o no durante la ejecución del trabajo práctico. Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados  [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).



# Resolucion

## Resolucion ejercicio 1

Debo generar un script de bash que genere un docker-compose.yaml que:
1) defina un servidor
2) genere N clientes, siendo N el valor pasado por parametro, con los nombres client1, client2, etc
3) Mantenga la configuracion de red, para que los clientes puedan comunicarse con el servidor

Primero creamos el archivo generar-compose.sh. Le damos todos los permisos (chmod 777 {nombre_script}, o chmod +x {nombre_script})
Definimos la escritura del servidor en el yaml (docker-compose-dev.yaml).
Luego utilizamos la funcion generar_clientes.py para que agregue al yaml la parte de los clientes
Finalmente agregamos la parte de red.

Nos queda un docker-compose.yaml ejecutable.

Para el manejo de errores se analiza que los parametros recibidos sean 2 y que el segundo parametro sea si o si un numero entero positivo.

Su forma de ejecucion es con el comando: `./generar-compose.sh docker-compose-dev.yaml {CANT_CLIENTES}`. Desde la raiz

Se puede observar que pasa todas las pruebas:
![alt text](ImgPruebas/pruebasEj1.png)

## Resolucion ejercicio 2

Se busca separar la configuracion del codigo para que no se tengan que reconstruir las imagenes de Docker cada vez que hay una modificacion en config.ini y config.yaml. Para esto se agrega en cada en el docker-compose-dev.yaml en el servidor el volumen que diriga al config.ini:

- volumes:
    - ./server/config.ini:/config.ini

Y lo mismo para el cliente, se agrega su volumen a cada cliente:
- volumes:
    - ./client/config.yaml:/config.yaml

Tambien para que pasen todas las pruebas se debe eliminar la configuaricon de entorno de logs: CLI_LOG_LEVEL=DEBUG para el cliente y el servidor, ya que en los tests se utiliza tanto INFO con DEBUG.

Se puede observar que pasa todas las pruebas:
![alt text](ImgPruebas/pruebasEj2.png)

## Resolucion ejercicio 3

Se busca verificar que al enviar un mensaje al servidor, el mensaje que devuelva sea el mismo y asi comprobar el echo. Para esto se crea un nuevo archivo validar-echo-server.sh. En este se crea un contenedor temporal busybox para enviar el mensaje al servidor y luego eliminarlo. Si el mensaje que devuelve el servidor es el mismo que el que se envio, el result es success. Caso contrario el result es fail

El nuevoscript de bash se ejecuta de la forma `./validar-echo-server.sh` , sin pasarle ningun parametro

Los tests pasan exitosamente: 
![alt text](ImgPruebas/pruebasEj3.png)

## Resolucion ejercicio 4

Se debe modificar servidor y cliente para que terminen de forma gracefull cuando reciban la señal SIGTERM. Para esto se modifican ambos archivos client.go y server.py.
Vamos por el cliente primero:
Se agrega como variable del Cliente un canal para detectar las señales. Tambien se crea un hilo de ejecucion (goroutine) para que este siempre atento a escuchar y manejar la señal. Esto se hace en la funcion creada handleShutDown(). Esta funcion se bloquea hasta que se reciba la señal y luego mata gracefully al cliente. 

Del lado del cliente se hace algo similar:
Se agrega una variable que pueda detectar la señal y un booleano para parar de escuchar por el puerto conectado, cuando se desconecte. Se almacenan los clientes conectados en una lista. Cuando se recibe la señal, se los desconecta uno por uno y luego se mata el servidor gracefully.

Todas las pruebas de la catedra pasan exitosamente:
![alt text](ImgPruebas/pruebasEj4.png)


## Resolucion ejercicio 5

Se busca armar un protocolo de comunicacion para que los clientes le puedan enviar una apuesta al servidor.
Protocolo de comunicacion:

type Bet struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}


El cliente le envia al servidor 6 enteros, los cuales definen el largo de cada atributo del cliente en orden (AGENCY, NOMBRE, APELLIDO, DOCUMENTO, NACIMIENTO, NUMERO). El servidor procede a recibir la cantidad de bytes como sea la suma de estos 6 valores enteros y luego hace el parseo para cada atributo, sabiendo su tamanio. Los protocolos de comunicacion se manejan en archivos separados al server y client. client_protocol.go para el cliente y server_protocol.py para el servidor. De esta manera ni el cliente ni el servidor conocen el protocolo de comunicacion

Del lado del cliente, la funcion SerializeBet() que se encuentra en el archivo client_protocol.go, se encarca de generar la cadena de bytes correspondientes acorde al protocolo indicado, que se va a enviar al servidor a travez del socket.
Del lado del servidor, la funcion receive_bet() que se encuentra en el archivo server_protocol.py, se encarga de leer todos esos bytes en el orden correspondiente y formar nuevamente la Bet del lado del servidor, para almacenarla.
Para el manejo de los errores short read y short write, el cliente utiliza la funcion sendAll(), la cual se queda en un bucle hasta que haya enviado todos los bytes correspondientes. Del lado del servidor se encuentra la funcion recv_all() la cual se queda en un bucle hasta recibir la cantidad ede bytes correspondientes.

Todas las pruebas de la catedra pasan exitosamente:
![alt text](ImgPruebas/pruebasEj5.png)

## Resolucion ejercicio 6

Ahora el cliente debe poder enviar muchas apuestas a la vez. Las apuestas las lee de un csv. Hay uno por cada agencia. Tambien se debe respetar un limite de apuestas enviadas enunciado en el yaml. 
Para esto se adapta al cliente para que pueda leer todas las apuestas de su csv correspondiente. Se modifica el docker-compose agregando a cada cliente el archivo correspondiente a las bets que debe enviar al servidor. Luego se genera una funcion para leer el csv. Esto lo hace la funcion ReadBetsFromCSV() la cual a partir de un filename, lee y arma todas las Bets de ese csv.

Se modifica levemente el protocolo para que se puedan enviar todas las bets correctamente. Primero se envia un entero que define la cantidad de batches que se van a enviar. Luego se comienza a enviar batch por batch. Cada batch envia al principio la cantidad de bets que va a enviar y luego empieza a enviar los bets con el protocolo ya definido.
El servidor cuando recibe la cantidad de batches que le van a llegar, itera esa cantidad de batches. En cada iteracion lee la cantidad de bets que le van a llegar e itera esa cantidad de veces. Termina cuando recorrio los for anidados.
Tambien, del lado del cliente, se analiza que los batches no superen los 8kb.

Las pruebas de la catedra pasan correctamente:
![alt text](ImgPruebas/pruebasEj6.png)


## Resolucion ejercicio 7

Se debe notificar a las agencias los correspondientes ganadores. Una vez que se almacenan todas las apuestas de todos los ganadores, el servidor recibe el mensaje de que se hicieron todas las apuestas y puede realizar el sorteo, para luego devolver el ganador a su correspondiente apuesta.

Modificaciones del lado del cliente:
Se agrega un primer mensaje del cliente al servidor cuando se logra conectar, el cual es un entero de 4 bytes que significa el ID de la agencia de ese cliente. Esto es para que el servidor asocie el client_socket con el agency_id determinado.
Luego de enviar todas las bets, se envia un mensaje de END y se espera a recibir los ganadores, que los enviara el servidor cuando todas las agencias envien END

Modificaciones del lado del servidor:
Se modifica la forma en que se guardan los clientes que se conectaron. El primer mensaje que recibe el servidor es el agency_id, entonces guarda los valores en un diccionario de clientes conectados, siendo la clave la agency_id y el valor el client_sock. Tambien en el diccionario winners se guarda como clave el agency_id y como valor una lista vacia que se va a rellenar de los ganadores de esa agencia.
Cuando se reciban todas las bets y el mensaje end, el contador de notificaciones de agencias se sumara a 1. Cuando este llegue a clients_amount (variable de entorno que se agrega al docker-compose-yaml) se hace load_bets() y has_won() por cada bet. Las bets que ganaron se almacenan en un diccionario winners el cual contiene como clave el id de la agencia y como valor una lista de los ganadores de esa agencia.
Cuando se obtienen todos los ganadores, se procede a enviar los correspondientes a cada agencia. Para esto se utiliza el mismo protocolo de comunicacion, pero de forma inversa:
Se envia primero un entero de 4 bytes que define la cantidad de winners que tiene esa agencia. Luego se envia por cada ganador, la cantidad de numeros que tiene el dni de ese ganador. Luego se envian todos los dnis de todos los ganadores de esa agencia. El cliente, al conocer el protocolo, puede rearmar la lista de ganadores correctamente.

Al enviarse todos los ganadores a todas las agencias, el servidor procede a cerrar la conexion con el cliente.

Las pruebas de la catedra pasan correctamente:
![alt text](ImgPruebas/pruebasEj7.png)

## Resolucion ejercicio 8

El ejercicio pide modificar el servidor para ejecutar los clientes en pararelo. Como usar threads en python trae complicaciones, combiene utilizar procesos. Para esto se utiliza la libreria multiprocessing, utilizando Process, Manager, Lock, Barrier y Value.

Por cada cliente se lanza un Process que maneja toda la recepcion de bets por parte de ese cliente particular, y el futuro envio de gandores a esa agencia particular.
Hay distintos recursos compartidos que deben manejarse correctamente, los cuales son:
- El entero notified_agencies. Se maneja con Values para que persista el cambio de su valor en los distintos procesos
- El diccionario de winners. Se maneja con Manager.dict()
- El archivo donde se guardan las bets. Se maneja con un lock solo para este, el cual es bet_file_lock
- El booleano lotery_run que define cuando se sortearon las bets. Se maneja con Values para que persista en los distintos procesos.
Para acceder a cada una de estas variables compartidas, el proceso debe obtener el variables_lock.

Luego se utiliza una barrera winners_barrier para sincronizar todos los procesos en un mismo punto el cual es esperar a que todos hayan mandado las bets, para que el servidor pueda hacer las apuestas.

Hay un cambio en el envio de las apuestas a cada cliente. Un proceso solo es el que va a ejecutar el sorteo de apuestas, obteniendo el variables_lock. Pero luego cada proceso va a ser el responsable de enviarle los winners al cliente/agencia que le corresponda (la que este "conectada"). Para esto nuevamente debe obtener el variables_lock antes.

Las pruebas de la catedra pasan correctamente:
![alt text](ImgPruebas/pruebasEj8.png)



Todas las pruebas de todos los ejercicios pasan correctamente:
![alt text](ImgPruebas/pruebasEjercicios.png)

