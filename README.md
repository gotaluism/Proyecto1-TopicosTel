# Proyecto1-TopicosTel
Vanessa Velez <br>
Santiago Arias <br>
Sara Cardona <br>
Luisa Maria Polanco <br>
Luis Miguel Giraldo <br>

## MARCO TEORICO
El sistema de archivos distribuidos (DFS) ha emergido como una solución esencial para la gestión eficiente de grandes volúmenes de datos en aplicaciones distribuidas. Estos sistemas permiten que múltiples nodos almacenen y accedan a archivos, proporcionando alta disponibilidad y tolerancia a fallos. El presente marco teórico integrará diversas perspectivas sobre sistemas de almacenamiento por bloques y objetos, tomando como base referencias clave como el Google File System (GFS), el Hadoop Distributed File System (HDFS) y otras teorías actuales sobre el manejo de datos históricos.

El almacenamiento basado en bloques divide los archivos en pequeñas unidades que se distribuyen a lo largo de varios nodos. Este enfoque es eficiente para operaciones de lectura y escritura paralelas, ya que permite que diferentes partes de un archivo sean procesadas simultáneamente en diferentes nodos, mejorando el rendimiento del sistema. GFS es uno de los ejemplos más destacados de este modelo, utilizando bloques grandes de 64 MB para reducir la sobrecarga en la comunicación y optimizar la replicación y recuperación de fallos. Cada bloque es replicado en al menos tres servidores, lo que garantiza la durabilidad de los datos incluso en caso de fallos en el hardware.


En el caso de HDFS, desarrollado como parte del proyecto Hadoop, se utiliza un enfoque similar, pero con bloques de 128 MB. Este tamaño mayor responde a las necesidades de procesamiento masivo de datos, donde las operaciones de lectura/escritura secuenciales son más frecuentes. Al igual que GFS, HDFS está diseñado para manejar fallos frecuentes de componentes, replicando los datos en varios nodos para garantizar su disponibilidad. Además, Hadoop, al ser un proyecto open source, se ha convertido en una pieza clave del ecosistema de Big Data, con herramientas como MapReduce y YARN que permiten el procesamiento distribuido eficiente.

![image](https://github.com/user-attachments/assets/1d979cc5-5e71-49a0-9faf-6ddc249417d2)


No obstante, una tendencia emergente en la gestión de datos es evitar la actualización directa de las entidades almacenadas en bases de datos. Históricamente, la motivación para actualizar los datos radicaba en los altos costos del almacenamiento. Sin embargo, con la reducción significativa en los costos del espacio en disco, hoy es factible adoptar un enfoque de registro de cambios. En lugar de sobrescribir entidades, se registra cada nueva entrada como una versión más, manteniendo un historial completo de cambios. Este enfoque ofrece varias ventajas, como la preservación de la línea de tiempo de los datos. Si se desea conocer el origen o las transformaciones de una entidad, se puede revisar su versión anterior. Además, en caso de que ocurra un error con la versión más reciente, se puede restaurar una versión previa sin una pérdida significativa de estado.

Este enfoque de mantener versiones históricas incrementa la resiliencia del sistema, minimizando los riesgos asociados con la pérdida de datos durante actualizaciones. En lugar de sobrescribir las entidades, los sistemas distribuidos actuales se benefician de esta técnica, logrando un equilibrio entre la eficiencia y la fiabilidad.

El almacenamiento basado en objetos, como el utilizado en Amazon S3, también sigue este enfoque de registro de cambios, manteniendo versiones completas de los archivos a lo largo del tiempo. Este modelo es ideal para escenarios donde los datos se escriben una vez y se leen múltiples veces (modelo WORM). Aunque sacrifica la flexibilidad para modificaciones parciales, ofrece escalabilidad y trazabilidad de cambios a gran escala, haciendo de él una solución robusta para necesidades de almacenamiento distribuido.



Palabras clave: Sistemas de archivos distribuidos, GFS, HDFS, almacenamiento por bloques, almacenamiento por objetos, tolerancia a fallos, escalabilidad.

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


### Comando rm (Borrar archivo)
Secuencia:
1. Usuario ejecuta comando rm, el cliente le pide el nombre del archivo y envía una solicitud al NameNode con el nombre del archivo y del usuario.
2. El NameNode verifica si el archivo pertenece al usuario y, si es válido, elimina la metadata asociada al archivo.
3. El NameNod envía solicitudes a los DataNodes involucrados para eliminar los bloques del archivo.
4. Los DataNodes eliminan los bloques y confirman al NameNode.
5. El NameNode informa al cliente que la eliminación fue exitosa en el sistema distribuido.
6. El cliente elimina el archivo localmente en la carpeta downloads y confirma que si sucedió.
