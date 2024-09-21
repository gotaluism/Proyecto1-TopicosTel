import sys
import os
import time
from concurrent import futures
import grpc
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
        self.datanodes = ["127.0.0.1:5001","127.0.0.1:5002","127.0.0.1:5003"]  
        self.user_files = {}
        self.user_directories = {}
        self.datanode_heartbeats = {}
        self.datanode_blocks = {}
        self.active_datanodes = {}
        self.file_metadata = {}
        self.block_locations = {}        

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
    
        # Asegúrate de que cada bloque vaya a un DataNode diferente
        for block in request.metadata:
            datanode_index = (block.block_number - 1) % len(self.datanodes)  # Distribución circular
            datanode = self.datanodes[datanode_index]
            metadata.append(file_pb2.FileBlockMetadata(
                block_number=block.block_number,
                start_byte=block.start_byte,
                end_byte=block.end_byte,
                datanode=datanode
            ))
    
        if username not in self.user_files:
            self.user_files[username] = []
        self.user_files[username].append(filename)
    
        return file_pb2.FileMetadataResponse(success=True, metadata=metadata)


    def PutFile(self, request, context):
        filename = request.filename
        data = request.data
        out_dir = './downloads'

        file_dir = os.path.join(out_dir, os.path.dirname(filename))
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        try:

            file_path = os.path.join(file_dir, os.path.basename(filename))

            with open(file_path, 'wb') as f:
                f.write(data)

            print(f"Bloque recibido y guardado en: {file_path}")
            return file_pb2.PutFileResponse(success=True, message=f"Bloque {file_path} recibido con éxito.")
        
        except Exception as e:
            return file_pb2.PutFileResponse(success=False, message=f"Error al guardar el bloque: {str(e)}")

    def ListFiles(self, request, context):
        username = request.username
        if username in self.user_files:
            return file_pb2.ListFilesResponse(success=True, filenames=self.user_files[username])
        else:
            return file_pb2.ListFilesResponse(success=False, message="El usuario no tiene archivos.")

    
    def Mkdir(self, request, context):
        username = request.username
        new_dir = request.directory
        print(f"Solicitud de mkdir para el usuario: {username}, directorio: {new_dir}")
        
        
        if not username or not new_dir:
            print(f"Error: datos inválidos en la solicitud. Username: '{username}', Directorio: '{new_dir}'")
            return file_pb2.MkdirResponse(success=False, message="Datos inválidos.")
        
        if new_dir in self.user_directories[username]:
            return file_pb2.MkdirResponse(success=False, message="El directorio ya existe.")

        self.user_directories[username].append(new_dir)
        print(f"Directorio '{new_dir}' creado para el usuario '{username}'")
        return file_pb2.MkdirResponse(success=True, message="Directorio creado con éxito.")
    
    
    
    def DeleteFile(self, request, context):
        username = request.username
        filename = request.filename

        # Verifica si el archivo pertenece al usuario
        if filename not in self.user_files.get(username, []):
            return file_pb2.DeleteFileResponse(success=False, message="El archivo no pertenece a este usuario o no existe.")

        self.user_files[username].remove(filename)

        for datanode in self.datanodes:
            datanode_channel = grpc.insecure_channel(datanode)
            datanode_stub = file_pb2_grpc.DataNodeServiceStub(datanode_channel)

            delete_request = file_pb2.DeleteBlockRequest(filename=filename)
            delete_response = datanode_stub.DeleteBlock(delete_request)
            if not delete_response.success:
                print(f"Error al eliminar bloques del archivo '{filename}' en DataNode {datanode}: {delete_response.message}")

        return file_pb2.DeleteFileResponse(success=True, message="Archivo eliminado correctamente.")
    
    def RegisterDataNode(self, request, context):
        datanode_name = request.datanode_name
        if datanode_name in self.active_datanodes:
            return file_pb2.DataNodeRegisterResponse(success=False, message="DataNode ya registrado")
        
        self.active_datanodes[datanode_name] = {
            'ip_address': request.ip_address,
            'port': request.port,
            'last_heartbeat': time.time()
        }
        print(f"Nuevo DataNode registrado: {datanode_name}")
        return file_pb2.DataNodeRegisterResponse(success=True, message="Registro exitoso")

    def Heartbeat(self, request, context):
        datanode_name = request.datanode_name
        
        # Verificar si el DataNode está registrado
        if datanode_name not in self.active_datanodes:
            return file_pb2.HeartbeatResponse(status="ERROR: DataNode no registrado")
        
        # Actualizar el tiempo del último heartbeat
        self.active_datanodes[datanode_name]['last_heartbeat'] = time.time()
        
        # Actualizar la lista de bloques almacenados
        stored_blocks = request.stored_blocks
        self.datanode_blocks[datanode_name] = stored_blocks
        
        # Mostrar la lista de bloques almacenados en este DataNode
        stored_blocks_str = ', '.join(stored_blocks)
        print(f"Heartbeat recibido de {datanode_name} [{stored_blocks_str}]")
        
        return file_pb2.HeartbeatResponse(status="OK")
   
    def check_datanodes(self):
        """Verifica si algún DataNode ha dejado de enviar heartbeats"""
        current_time = time.time()
        for datanode_name in list(self.active_datanodes.keys()):
            last_heartbeat = self.active_datanodes[datanode_name]['last_heartbeat']
            if current_time - last_heartbeat > 10:
                print(f"DataNode {datanode_name} no responde. Último heartbeat hace más de 10 segundos.")
                del self.active_datanodes[datanode_name]
                if datanode_name in self.datanode_blocks:
                    del self.datanode_blocks[datanode_name]

    def BlockReport(self, request, context):
        datanode_name = request.datanode_name
        blocks = request.blocks

        print(f"Recibido Block Report de {datanode_name}")

        # Actualizar la información de los bloques para este DataNode
        self.update_block_information(datanode_name, blocks)

        # Verificar la replicación y la integridad de los bloques
        self.check_replication_and_integrity()

        return file_pb2.BlockReportResponse(message="Block Report procesado correctamente")
    
    def parse_block_id(self, block_id):
        try:
            # Usar os.path.split para manejar correctamente las rutas
            file_path, block_filename = os.path.split(block_id)
            
            # Extraer el número de bloque
            block_number_str = ''.join(filter(str.isdigit, block_filename))
            if not block_number_str:
                raise ValueError(f"No se pudo extraer el número de bloque de: {block_filename}")
            
            block_number = int(block_number_str)
            
            return file_path, block_number
        except (ValueError, IndexError) as e:
            print(f"Error al parsear block_id '{block_id}': {str(e)}")
            return block_id, 0  # Retornamos valores por defecto en caso de error

    def update_block_information(self, datanode_name, blocks):
        for block in blocks:
            block_id = block.block_id
            if block_id not in self.block_locations:
                self.block_locations[block_id] = set()
            self.block_locations[block_id].add(datanode_name)

            file_path, block_number = self.parse_block_id(block_id)
            if file_path not in self.file_metadata:
                self.file_metadata[file_path] = {}
            self.file_metadata[file_path][block_number] = {
                'size': block.size,
                'checksum': block.checksum
            }

        print(f"Información de bloques actualizada para {datanode_name}")

    def check_replication_and_integrity(self):
        for block_id, locations in self.block_locations.items():
            if len(locations) < 3:  # Asumiendo que queremos 3 réplicas
                print(f"El bloque {block_id} necesita más réplicas. Actualmente en: {locations}")
                self.schedule_replication(block_id, locations)

    def schedule_replication(self, block_id, current_locations):
        # Aquí implementarías la lógica para programar la replicación del bloque
        # Por ejemplo, seleccionar un DataNode que tenga el bloque y otro que no lo tenga
        # y enviar una solicitud para replicar el bloque
        print(f"Programando replicación para el bloque {block_id}")

    
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    namenode_servicer = NameNodeServicer()
    file_pb2_grpc.add_NameNodeServiceServicer_to_server(namenode_servicer, server)
    server.add_insecure_port('[::]:5000')
    print("Namenode escuchando en el puerto 5000...")
    server.start()
    server.wait_for_termination()

    # Ejecuta la verificación de los DataNodes cada 10 segundos
    while True:
        namenode_servicer.check_datanodes()
        time.sleep(10)

if __name__ == "__main__":
    serve()
