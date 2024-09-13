import os
from concurrent import futures
import grpc
import protos.file_pb2 as file_pb2
import protos.file_pb2_grpc as file_pb2_grpc


class NameNodeServicer(file_pb2_grpc.NameNodeServiceServicer):
    def __init__(self):
        self.users = {
            "admin": "password123",
            "user1": "pass1",
            "user2": "pass2"
        }

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
    
    def PutFile(self, request, context):
        filename = request.filename
        data = request.data

        # Crear directorios si no existen (según la ruta completa recibida del cliente)
        file_dir = os.path.dirname(filename)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        try:
            # Guardar el bloque en la ruta especificada por el cliente
            with open(filename, 'wb') as f:
                f.write(data)

            print(f"Bloque recibido y guardado en: {filename}")
            return file_pb2.PutFileResponse(success=True, message=f"Bloque {filename} recibido con éxito.")
        
        except Exception as e:
            return file_pb2.PutFileResponse(success=False, message=f"Error al guardar el bloque: {str(e)}")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_NameNodeServiceServicer_to_server(NameNodeServicer(), server)
    server.add_insecure_port('[::]:5000') 
    print("Namenode escuchando en el puerto 5000...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()