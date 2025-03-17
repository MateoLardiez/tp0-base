# Resolucion ejercicio 1

Debo generar un script de bash que genere un docker-compose.yaml que:
1) defina un servidor
2) genere N clientes, siendo N el valor pasado por parametro, con los nombres client1, client2, etc
3) Mantenga la configuracion de red, para que los clientes puedan comunicarse con el servidor

Primero creamos el archivo generar-compose.sh. Le damos todos los permisos (chmod 777 {nombre_script})
Definimos la escritura al yaml del servidor.
Luego utilizamos la funcion generar_clientes.py para que agregue al yaml la parte de los clientes
Finalmente agregamos la parte de red.

Nos queda un docker-compose.yaml ejecutable