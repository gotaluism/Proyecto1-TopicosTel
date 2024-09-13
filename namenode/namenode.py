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

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_NameNodeServiceServicer_to_server(NameNodeServicer(), server)
    server.add_insecure_port('[::]:5000') 
    print("NameNode escuchando en el puerto 5000...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()