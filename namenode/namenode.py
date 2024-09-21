import sys
import os
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
        self.datanodes = ["127.0.0.1:5001"]  # Cambia DataNode1 y DataNode2 por IPs locales
        self.user_files = {}
        self.user_directories = {}


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


        for block in request.metadata:
            datanode = self.datanodes[block.block_number % len(self.datanodes)]
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
        print(self.user_directories)
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

        for datanode in self.datanodes:
            datanode_channel = grpc.insecure_channel(datanode)
            datanode_stub = file_pb2_grpc.DataNodeServiceStub(datanode_channel)

            delete_request = file_pb2.DeleteBlockRequest(filename=filename)
            delete_response = datanode_stub.DeleteBlock(delete_request)
            if not delete_response.success:
                print(f"Error al eliminar bloques del archivo '{filename}' en DataNode {datanode}: {delete_response.message}")

        return file_pb2.DeleteFileResponse(success=True, message="Archivo eliminado correctamente.")
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_NameNodeServiceServicer_to_server(NameNodeServicer(), server)
    server.add_insecure_port('[::]:5000') 
    print("Namenode escuchando en el puerto 5000...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()

