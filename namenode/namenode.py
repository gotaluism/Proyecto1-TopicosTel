import sys
import os
import time
from concurrent import futures
import grpc
import threading

# Agregar la ruta de la carpeta 'protos' al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos')))

# Ahora importa ambos módulos
import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc

class NameNodeServicer(file_pb2_grpc.NameNodeServiceServicer):
    def __init__(self):
        self.users = {
            "admin": "password123",
            "user1": "pass1",
            "user2": "pass2"
        }
        self.datanodes = {}  # Cambiamos a diccionario para manejar DataNodes activos
        self.user_files = {}
        self.user_directories = {}
        self.datanode_heartbeats = {}
        self.datanode_blocks = {}
        self.file_metadata = {}  # Estructura: {filename: {block_number: [datanodes]}}
        self.block_locations = {}  # Estructura: {block_id: set(datanodes)}       

        for user in self.users:
            self.user_directories[user] = []
            
    def Authenticate(self, request, context):
        username = request.username
        password = request.password
        if username in self.users and self.users[username] == password:
            return file_pb2.LoginResponse(success=True, message="Autenticación exitosa")
        else:
            return file_pb2.LoginResponse(success=False, message="Credenciales inválidas")

    def Register(self, request, context):
        if request.username in self.users:
            return file_pb2.RegisterResponse(success=False, message="Usuario ya registrado")
        self.users[request.username] = request.password
        return file_pb2.RegisterResponse(success=True, message="Registro exitoso")

    def PutFileMetadata(self, request, context):
        filename = request.filename
        username = request.username
        metadata = []
        block_locations = []

        print(f"Recibida solicitud de almacenamiento para el archivo: {filename} del usuario: {username}")
    
        # Verificar si hay suficientes DataNodes activos
        if len(self.datanodes) < 2:
            return file_pb2.FileMetadataResponse(success=False, message="No hay suficientes DataNodes disponibles.")

        # Asignar DataNodes para cada bloque con replicación
        datanode_list = list(self.datanodes.keys())
        for block in request.metadata:
            assigned_datanodes = self.select_datanodes_for_block(block.block_number)
            metadata.append(file_pb2.FileBlockMetadata(
                block_number=block.block_number,
                start_byte=block.start_byte,
                end_byte=block.end_byte,
                datanodes=assigned_datanodes
            ))

            # Actualizar metadata de bloques
            block_id = f"{filename}_block_{block.block_number}"
            self.block_locations[block_id] = set(assigned_datanodes)

            # Actualizar metadata del archivo
            if filename not in self.file_metadata:
                self.file_metadata[filename] = {}
            self.file_metadata[filename][block.block_number] = assigned_datanodes

        if username not in self.user_files:
            self.user_files[username] = []
        if filename not in self.user_files[username]:
            self.user_files[username].append(filename)
    
        return file_pb2.FileMetadataResponse(success=True, metadata=metadata)

    def select_datanodes_for_block(self, block_number):
        # Seleccionar dos DataNodes diferentes para replicación
        datanode_list = list(self.datanodes.keys())
        # Distribuir los bloques de manera uniforme
        datanode1 = datanode_list[block_number % len(datanode_list)]
        datanode2 = datanode_list[(block_number + 1) % len(datanode_list)]
        return [datanode1, datanode2]

    def GetFileMetadata(self, request, context):
        filename = request.filename
        username = request.username

        # Verifica si el archivo existe para el usuario
        if username not in self.user_files or filename not in self.user_files[username]:
            return file_pb2.FileMetadataResponse(success=False, message="Archivo no encontrado.")

        # Recuperar la metadata de los bloques y los DataNodes correspondientes
        file_metadata = []
        if filename in self.file_metadata:
            for block_number, datanodes in self.file_metadata[filename].items():
                file_metadata.append(file_pb2.FileBlockMetadata(
                    block_number=block_number,
                    start_byte=0,
                    end_byte=0,
                    datanodes=datanodes
                ))
            return file_pb2.FileMetadataResponse(success=True, metadata=file_metadata)
        else:
            return file_pb2.FileMetadataResponse(success=False, message="Metadata del archivo no encontrada.")

    def ListFiles(self, request, context):
        username = request.username
    
        if username in self.user_files:
            if username in self.user_directories:
                return file_pb2.ListFilesResponse(success=True, filenames=self.user_files[username], directorynames=self.user_directories[username])
            else:
                return file_pb2.ListFilesResponse(success=True, filenames=self.user_files[username], directorynames=[])
        elif username in self.user_directories:
            if username in self.user_files:
                return file_pb2.ListFilesResponse(success=True, filenames=self.user_files[username], directorynames=self.user_directories[username])
            else:
                return file_pb2.ListFilesResponse(success=True, filenames=[], directorynames=self.user_directories[username])
        else:
            return file_pb2.ListFilesResponse(success=False, message="El usuario no tiene archivos.")

    
    def Mkdir(self, request, context):
        username = request.username
        new_dir = request.directory
        print(f"Solicitud de mkdir para el usuario: {username}, directorio: {new_dir}")       
    
        if not username or not new_dir:
            print(f"Error: datos inválidos en la solicitud. Username: '{username}', Directorio: '{new_dir}'")
            return file_pb2.MkdirResponse(success=False, message="Datos inválidos.")
        
        if username not in self.user_directories:
            self.user_directories[username] = []

        if new_dir in self.user_directories[username]:
            return file_pb2.MkdirResponse(success=False, message="El directorio ya existe.")
        
        self.user_directories[username].append(new_dir)
        print(f"Directorio '{new_dir}' creado para el usuario '{username}'")
        return file_pb2.MkdirResponse(success=True, message="Directorio creado con éxito.")

    def Rmdir(self, request, context):
        username = request.username
        dir = request.directory
        print(f"Solicitud de rmdir para el usuario: {username}, directorio: {dir}")    

        if not username or not dir:
            print(f"Error: datos inválidos en la solicitud. Username: '{username}', Directorio: '{dir}'")
            return file_pb2.MkdirResponse(success=False, message="Datos inválidos.")

        if dir not in self.user_directories[username]:
            return file_pb2.MkdirResponse(success=False, message="El directorio no existe.")

        # Remover archivos dentro del directorio
        files_to_remove = [f for f in self.user_files.get(username, []) if f.startswith(dir + '/')]
        for filename in files_to_remove:
            self.DeleteFile(file_pb2.DeleteFileRequest(username=username, filename=filename), None)
            print(f"Archivo '{filename}' eliminado del directorio '{dir}'")

        self.user_directories[username].remove(dir)
        print(f"Directorio '{dir}' eliminado para el usuario '{username}'")
        return file_pb2.MkdirResponse(success=True, message="Directorio eliminado con éxito.")
    
    def DeleteFile(self, request, context):
        username = request.username
        filename = request.filename

        # Verifica si el archivo pertenece al usuario
        if filename not in self.user_files.get(username, []):
            return file_pb2.DeleteFileResponse(success=False, message="El archivo no pertenece a este usuario o no existe.")

        self.user_files[username].remove(filename)

        # Eliminar bloques del archivo en los DataNodes correspondientes
        if filename in self.file_metadata:
            for block_number, datanodes in self.file_metadata[filename].items():
                for datanode in datanodes:
                    try:
                        datanode_channel = grpc.insecure_channel(datanode)
                        datanode_stub = file_pb2_grpc.DataNodeServiceStub(datanode_channel)

                        delete_request = file_pb2.DeleteBlockRequest(filename=filename, block_number=block_number)
                        delete_response = datanode_stub.DeleteBlock(delete_request)
                        if not delete_response.success:
                            print(f"Error al eliminar bloque {block_number} del archivo '{filename}' en DataNode {datanode}: {delete_response.message}")
                    except Exception as e:
                        print(f"Excepción al conectar con DataNode {datanode}: {str(e)}")

            # Remover metadata del archivo
            del self.file_metadata[filename]

        return file_pb2.DeleteFileResponse(success=True, message="Archivo eliminado correctamente.")
    
    def RegisterDataNode(self, request, context):
        datanode_name = request.datanode_name
        if datanode_name in self.datanodes:
            return file_pb2.DataNodeRegisterResponse(success=False, message="DataNode ya registrado")
        
        self.datanodes[datanode_name] = {
            'ip_address': request.ip_address,
            'port': request.port,
            'last_heartbeat': time.time()
        }
        print(f"Nuevo DataNode registrado: {datanode_name}")
        return file_pb2.DataNodeRegisterResponse(success=True, message="Registro exitoso")

    def Heartbeat(self, request, context):
        datanode_name = request.datanode_name
        
        # Verificar si el DataNode está registrado
        if datanode_name not in self.datanodes:
            return file_pb2.HeartbeatResponse(status="ERROR: DataNode no registrado")
        
        # Actualizar el tiempo del último heartbeat
        self.datanodes[datanode_name]['last_heartbeat'] = time.time()
        
        # Actualizar la lista de bloques almacenados
        stored_blocks = request.stored_blocks
        self.datanode_blocks[datanode_name] = stored_blocks
        
        # Mostrar la lista de bloques almacenados en este DataNode
        stored_blocks_str = ', '.join(stored_blocks)
        print(f"Heartbeat recibido de {datanode_name} [{stored_blocks_str}]")
        
        return file_pb2.HeartbeatResponse(status="OK")
   
    def check_datanodes(self):
        """Verifica si algún DataNode ha dejado de enviar heartbeats"""
        while True:
            current_time = time.time()
            for datanode_name in list(self.datanodes.keys()):
                last_heartbeat = self.datanodes[datanode_name]['last_heartbeat']
                if current_time - last_heartbeat > 10:
                    print(f"DataNode {datanode_name} no responde. Último heartbeat hace más de 10 segundos.")
                    self.handle_datanode_failure(datanode_name)
            time.sleep(5)

    def handle_datanode_failure(self, datanode_name):
        print(f"DataNode {datanode_name} ha fallado porque no se detectó el heartbeat. Procediendo a redistribuir los bloques.")
        # Remover DataNode de la lista de activos
        del self.datanodes[datanode_name]
        if datanode_name in self.datanode_blocks:
            del self.datanode_blocks[datanode_name]

        # Iniciar proceso de replicación de bloques afectados
        affected_blocks = []
        for block_id, datanodes in self.block_locations.items():
            if datanode_name in datanodes:
                datanodes.remove(datanode_name)
                if len(datanodes) < 2:
                    affected_blocks.append((block_id, datanodes))

        for block_id, datanodes in affected_blocks:
            self.replicate_block(block_id, datanodes)

    def replicate_block(self, block_id, current_datanodes):
        # Seleccionar un nuevo DataNode para replicar el bloque
        available_datanodes = set(self.datanodes.keys()) - set(current_datanodes)
        if not available_datanodes:
            print(f"No hay DataNodes disponibles para replicar el bloque {block_id}")
            return

        source_datanode = list(current_datanodes)[0]
        target_datanode = min(available_datanodes, key=lambda dn: len(self.datanode_blocks.get(dn, [])))

        # Iniciar la replicación
        try:
            # Obtener el bloque del DataNode fuente
            source_channel = grpc.insecure_channel(source_datanode)
            source_stub = file_pb2_grpc.DataNodeServiceStub(source_channel)

            filename, block_number = block_id.rsplit('_block_', 1)
            retrieve_request = file_pb2.RetrieveBlockRequest(
                filename=filename,
                block_number=int(block_number)
            )
            retrieve_response = source_stub.RetrieveBlock(retrieve_request)

            if retrieve_response.success:
                # Enviar el bloque al DataNode de destino
                target_channel = grpc.insecure_channel(target_datanode)
                target_stub = file_pb2_grpc.DataNodeServiceStub(target_channel)

                store_request = file_pb2.StoreBlockRequest(
                    filename=filename,
                    block_number=int(block_number),
                    data=retrieve_response.data
                )
                store_response = target_stub.StoreBlock(store_request)

                if store_response.success:
                    print(f"Bloque {block_id} replicado exitosamente a {target_datanode}")
                    # Actualizar metadata
                    self.block_locations[block_id].add(target_datanode)
                    self.update_file_metadata(filename, int(block_number), target_datanode)
                else:
                    print(f"Error al almacenar bloque en {target_datanode}: {store_response.message}")
            else:
                print(f"Error al recuperar bloque de {source_datanode}: {retrieve_response.message}")
        except Exception as e:
            print(f"Excepción durante la replicación del bloque {block_id}: {str(e)}")

    def update_file_metadata(self, filename, block_number, datanode):
        if filename in self.file_metadata:
            if block_number in self.file_metadata[filename]:
                if datanode not in self.file_metadata[filename][block_number]:
                    self.file_metadata[filename][block_number].append(datanode)
            else:
                self.file_metadata[filename][block_number] = [datanode]
        else:
            self.file_metadata[filename] = {block_number: [datanode]}

    def BlockReport(self, request, context):
        datanode_name = request.datanode_name
        blocks = request.blocks

        print(f"Recibido Block Report de {datanode_name}")

        # Actualizar la información de los bloques para este DataNode
        self.update_block_information(datanode_name, blocks)

        return file_pb2.BlockReportResponse(message="Block Report procesado correctamente")
    
    def update_block_information(self, datanode_name, blocks):
        for block in blocks:
            block_id = block.block_id
            if block_id not in self.block_locations:
                self.block_locations[block_id] = set()
            self.block_locations[block_id].add(datanode_name)

        print(f"Información de bloques actualizada para {datanode_name}")
    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    namenode_servicer = NameNodeServicer()
    file_pb2_grpc.add_NameNodeServiceServicer_to_server(namenode_servicer, server)
    server.add_insecure_port('[::]:5000')
    print("NameNode escuchando en el puerto 5000...")
    server.start()

    # Iniciar hilo para verificar DataNodes
    threading.Thread(target=namenode_servicer.check_datanodes).start()

    server.wait_for_termination()

if __name__ == "__main__":
    serve()
