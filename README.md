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
![Arquitectura HDFS Proyecto Telematica](https://github.com/user-attachments/assets/fe5921cc-a005-47c1-8873-e9f28d6e07d9)


## Protocolos: gRPC (HTTP/2)
#### Cliente <-> NameNode
- Authenticate
- Register
- PutFileMetadata
- ListFiles
- Mkdir
- DeleteFile
- GetFile
- DeleteDirectory
- Metadata table

#### Cliente <-> DataNode
- StoreBlock
- GetBlock
  
#### NameNode <-> DataNode
- Heartbeats
- Handshake
- Block Reports
- Replication Management
- DeleteBlocksDirectory

####	DataNode <-> DataNode
- Blocks Replication

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

### Comando ls (Visualizar archivos en directorio actual)
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

### Comando get (Obtener un archivo especifico)
Secuencia:

1. El cliente ejecuta el comando get y se le pide el nombre del archivo que desea obtener.
2. El cliente envía una solicitud al NameNode solicitando el archivo especificado.
3. El NameNode recibe la solicitud, verifica el acceso del cliente a este archivo, y busca que DataNodes contienen los bloques asociados a este archivo.
4. El NameNode responde al cliente con una lista de las url de los dataNodes que tienen los bloques que forman el archivo y el nombre del recurso que debe buscar en ellos.
5. El cliente recibe la lista de urls y envia una petición a cada DataNode preguntando por el recurso que le dijo el NameNode.
6. Los DataNode responden con el bloque solicitado.
7. El cliente arma el archivo con los bloques enviados por los DataNodes.

### Comando cd (Realizar acciones desde una ruta especifica)
Secuencia:
1. El cliente ejecuta el comando cd y se le pide el nombre del directorio creado al cual quiere ingresar.
2. Esta nueva ruta sera usada para las peticiones de consulta o adición de archivos.

### Comando mkdir (Crear carpeta)
Secuencia:
1. El cliente ejecuta el comando mkdir y se le pide el nombre de la carpeta que desea crear.
2. Esta carpeta se creará en el sistema de archivos del cliente y será usada como ruta para adición de archivos.

### Comando rmdir (Eliminar carpeta)
Secuencia:
1. El cliente ejecuta el comando rmdir y se le pide el nombre de la carpeta que desea eliminar.
2. El cliente envía una solicitud al NameNode con el nombre de la carpeta y del usuario.
3. El NameNode verifica si la carpeta pertenece al usuario y, si es válido, elimina la metadata asociada a la carpeta.
4. El NameNode envía solicitudes a los DataNodes involucrados para eliminar los bloques asociados a la carpeta que desea eliminar.
5. Los DataNodes eliminan los bloques y confirman al NameNode.
6. El NameNode informa al cliente que la eliminación fue exitosa en el sistema distribuido.
7. El cliente elimina la carpeta localmente en la carpeta downloads y confirma que si sucedió.

## Servicios Namenode

### Gestión de tabla metadata
Secuencia:
1. El NameNode gestiona la tabla de metadata, la cual contiene la ubicación de todos los bloques de los archivos distribuidos en los DataNodes.
2. Cada vez que un archivo se agrega, modifica o elimina, el NameNode actualiza la tabla de metadata para reflejar los cambios.
3. El NameNode recibe información periódica de los DataNodes (a través de Block Reports) para verificar que los bloques estén correctamente distribuidos y almacenados.
4. El NameNode utiliza la tabla de metadata para determinar qué bloques enviar o eliminar cuando un cliente solicita operaciones sobre archivos.
5. En caso de pérdida de un DataNode, el NameNode reasigna los bloques perdidos a otros DataNodes y actualiza su tabla de metadata.

### Reporte de bloques (Block Report)
Secuencia:
l. DataNode envía informes periódicos al NameNode con la lista de bloques que está almacenando.
2. NameNode actualiza su tabla de metadata en base a estos informes para garantizar que los bloques estén almacenados correctamente.
3. NameNode usa esta información para gestionar la replicación y detectar fallas en los DataNodes.

### Heartbeat
Secuencia:
1. Los DataNodes envían señales regulares de heartbeat al NameNode para indicar que están activos y en funcionamiento.
2. Si el NameNode deja de recibir heartbeats de un DataNode dentro de un periodo determinado, considera que el DataNode ha fallado.
3. El NameNode reprograma la replicación de los bloques almacenados en ese DataNode en otros nodos disponibles.

### Handshake (inicio de comunicación)
Secuencia:
1. Cuando un DataNode arranca, se registra en el NameNode enviando un mensaje de "handshake".
2. El NameNode verifica la identidad del DataNode y lo registra en su sistema.
3. El DataNode comienza a enviar heartbeats y reportes de bloques al NameNode de manera regular.

## Servicios DataNode

#### Recepción de Bloques:
Secuencia:
1. El DataNode recibe bloques de datos enviados por el cliente.
2. Verifica la integridad del bloque mediante un checksum.
3. Almacena el bloque en el almacenamiento local (disco).
   
#### Actualización de Metadata Local:
Secuencia:
1. Actualiza su propia metadata para reflejar los bloques almacenados y su integridad.
2. Mantiene una lista de los bloques que está almacenando para el reporte al NameNode.

#### Eliminación de Bloques:
Secuencia:
1. Recibe solicitudes del NameNode para eliminar bloques específicos.
2. Elimina los bloques solicitados de su almacenamiento local.
3. Actualiza su metadata para reflejar la eliminación de los bloques.

#### Solicitud de Lectura de Bloques:
Secuencia:
1. Recibe una solicitud de lectura de un cliente para un bloque específico.
2. Verifica que el bloque solicitado esté disponible y no esté dañado.
3. Envía el bloque solicitado al cliente.
   
#### Solicitud de Escritura de Bloques:
Secuencia:
1. Recibe un bloque para almacenar desde un cliente.
2. Verifica la integridad del bloque recibido y lo almacena.
3. Envía una confirmación al cliente de que el bloque ha sido almacenado con éxito.

#### Block Report (Reporte de Bloques):
Secuencia:
1. Envía periódicamente un Block Report al NameNode.
2. El reporte contiene la lista de bloques almacenados, su ubicación, y su estado de integridad.
3. Permite al NameNode actualizar su tabla de metadata y realizar la gestión de replicación.
   
#### Heartbeat (Latido del Corazón):
Secuencia:
1. Envía señales de heartbeat regulares al NameNode para confirmar que está activo y funcionando.
2. Incluye información adicional como el estado de almacenamiento y la capacidad disponible.

#### Handshake (Inicio de Comunicación):
Secuencia:
1. Cuando el DataNode se inicia, realiza un handshake con el NameNode.
2. Envía un mensaje de registro al NameNode con información sobre su identidad y capacidad.
3. El NameNode valida al DataNode y lo incluye en su lista de nodos activos.
   
#### Registro en el Sistema:
Secuencia:
1. Después del handshake, el DataNode se registra oficialmente en el sistema del NameNode.
2. Comienza a enviar heartbeats y block reports según lo requiera el NameNode.

#### Mantenimiento de Integridad de Datos:
Secuencia:
1.Realiza chequeos periódicos de integridad de los bloques almacenados.
2. Detecta y corrige errores si es posible o informa al NameNode sobre bloques dañados.

#### Recuperación ante Fallos:
Secuencia:
1. Participa en el proceso de recuperación de datos en caso de fallo.
2. Reemplaza los bloques que faltan o están dañados según las instrucciones del NameNode.





# Despliegue del Proyecto en AWS

## Descripción General

Este proyecto utiliza 4 instancias EC2 de AWS para simular un sistema distribuido con un *namenode* y 3 *datanodes*. A continuación se detalla el proceso de despliegue, configuración y ejecución de los nodos en las instancias.

---

## 1. Creación de Instancias en AWS

Se crearon 4 instancias EC2 de tipo `t2.nano`, con las siguientes configuraciones:

- **Namenode (Instancia: Proyecto1. Topicos Tel)**:
  - IP Pública: `35.168.147.129`
  
- **Datanode 1**:
  - IP Pública: `98.83.59.27`
  
- **Datanode 2**:
  - IP Pública: `23.23.84.61`
  
- **Datanode 3**:
  - IP Pública: `98.83.74.28`

### Captura de las instancias en ejecución
![image](https://github.com/user-attachments/assets/f1aa4de9-3c62-4106-88ae-cd77e6fb0629)
![image](https://github.com/user-attachments/assets/aa3fb199-3ead-4777-a8bf-178a726f9922)

---

## 2. Conexión a las Instancias

Para conectarse a cada instancia se utiliza SSH con la clave PEM proporcionada al momento de crear las instancias. El comando utilizado para la conexión es:

ssh -i P1.pem ubuntu@[IP_ELÁSTICA]


**Ejemplo** para conectarse a `Datanode3`:

ssh -i P1.pem ubuntu@98.83.74.28


---

## 3. Instalación de Dependencias

Una vez dentro de cada instancia, se realizó la instalación de las dependencias necesarias para ejecutar el proyecto:

1. **Instalar Git** para clonar el repositorio:

    ```bash
    sudo apt-get update
    sudo apt-get install git
    ```

2. **Instalar Python3 y pip**:

    ```bash
    sudo apt-get install python3 python3-pip
    ```

3. **Clonar el repositorio del proyecto**:

    ```bash
    git clone https://github.com/gotaluism/Proyecto1-TopicosTel.git
    ```

4. **Crear y activar un entorno virtual** dentro del directorio del proyecto:

    ```bash
    cd Proyecto1-TopicosTel
    python3 -m venv venv
    source venv/bin/activate
    ```

5. **Instalar gRPC y sus herramientas** dentro del entorno virtual:

    ```bash
    pip install grpcio grpcio-tools
    ```

---

## 4. Modificación de Archivos para configuración de Nodos

### 4.1. Configuración de los Datanodes

En los archivos de los *datanodes*, se modificó la función `serve()` para que escuche en la IP de la instancia correspondiente y en el puerto `5000x`. A continuación se muestra un ejemplo de esta modificación para *Datanode3*:

```python
if __name__ == "__main__":
    node_number = int(input("Ingrese el número del Datanode: "))
    port = 50003
    serve('98.83.74.28', port)
```

### Captura de el cambio realizado en código

![image](https://github.com/user-attachments/assets/cc828faa-7b1a-47c5-90f3-cf50fcb122c8)

En el datanode 1 se realizó con el puerto `50001`
En el datanode 2 se realizó con el puerto `50002`
Además, en cada *datanode*, se configuró el servidor gRPC para que escuche en el puerto `50003` y acepte conexiones de cualquier dirección IP:

```python
server.add_insecure_port('0.0.0.0:50003')

```

### 4.2. Configuración del Cliente

En el archivo del cliente, se modificó la IP para que se conecte al namenode, en lugar de localhost, utilizando la IP pública de la instancia correspondiente. Ejemplo:

```python
if __name__ == "__main__":
    client = DFSClient('35.168.147.129', 5000)
```

### Captura del código con la modificación de la IP para el cliente
![image](https://github.com/user-attachments/assets/55517e7e-6971-4981-8352-67fc43ca71cd)


## 5. Ejecución de los Nodos

Después de realizar las modificaciones en los archivos de configuración, se procede a la ejecución de los nodos.

Ejecución del Namenode:

```bash
python3 namenode.py
```

Ejecución de los Dtanode:

```bash
python3 datanode.py
```

