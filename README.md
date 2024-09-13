# Proyecto1-TopicosTel
Vanessa Velez <br>
Sara Cardona <br>
Luisa Maria Polanco <br>
Luis Miguel Giraldo <br>

## Arquitectura del Sistema

## Protocolos
o	Cliente <-> NameNode: gRPC (HTTP/2) <br>
o	NameNode <-> NameNode: gRPC (HTTP/2)  <br>
o	NameNode <-> DataNode: gRPC (HTTP/2)   <br>
o	DataNode <-> NameNode: gRPC (HTTP/2)   <br>
o	DataNode <-> DataNode: RPC (HTTP/2)   <br>



# Diseño detallado


## Servicios cliente

### Autenticación (login)
Secuencia:
1. El cliente envía una solicitud al NameNode que contiene usuario y contraseña.
2. El NameNode recibe las credenciales y las valida.
3. Si las credenciales son correctas, el NameNode envía una respuesta al cliente diciendo que la autenticación fue exitosa y le da acceso al sistema.
4. Si las credenciales no son válidas, el NameNode envía un mensaje de error indicando que el inicio de sesión ha fallado.

### Comando put (subir archivo)
Secuencia:
1. El cliente ejecuta el comando put y después recibe la ruta del archivo (local) que se desea subir.
2. El cliente divide el archivo en bloques de tamaño fijo (64kb) y se prepara para enviarlos.
3. El cliente envía una solicitud al NameNode indicando que desea subir los bloques del archivo.
4. El NameNode responde con la información necesaria para proceder, indicando que los bloques pueden ser almacenados.
5. El cliente envía cada bloque directamente a los DataNodes indicados por el NameNode.
6. Cada nodo confirma al cliente la recepción exitosa de los bloques.
7. Una vez que todos los bloques han sido enviados y confirmados, el cliente notifica al NameNode que la operación ha finalizado.
8. El NameNode actualiza su metadata para registrar los bloques del archivo y su ubicación en los DataNodes.

### Comando ls (Visualizar archivos en directorio arctual)
Secuencia:
1. El cliente envía una solicitud al NameNode solicitando la lista de archivos del directorio actual.
2. El NameNode recibe la solicitud, verifica el directorio del cliente, y busca los archivos y directorios correspondientes.
3. El NameNode responde al cliente con una lista de los archivos y directorios que se encuentran en el directorio actual.
4. El cliente recibe la lista de archivos y puede ver los resultados en su terminal o interfaz.
