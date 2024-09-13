import grpc
import protos.file_pb2 as file_pb2
import protos.file_pb2_grpc as file_pb2_grpc

class DFSClient:
    def __init__(self, namenode_host, namenode_port):
        self.channel = grpc.insecure_channel(f'{namenode_host}:{namenode_port}')
        self.stub = file_pb2_grpc.NameNodeServiceStub(self.channel)

    def authenticate(self, username, password):
        request = file_pb2.LoginRequest(username=username, password=password)
        response = self.stub.Authenticate(request)
        if response.success:
            print(f"Autenticación exitosa: {response.message}")
            return True
        else:
            print(f"Autenticación fallida: {response.message}")
            return False

    def register(self, username, password):
        request = file_pb2.RegisterRequest(username=username, password=password)
        response = self.stub.Register(request)
        if response.success:
            print(f"Registro exitoso: {response.message}")
            return True
        else:
            print(f"Registro fallido: {response.message}")
            return False

    def show_menu(self):
        print("\nMenú de Comandos:")
        print("1. ls")
        print("2. cd")
        print("3. get")
        print("4. put")
        print("5. mkdir")
        print("6. rmdir")
        print("7. rm")
        print("8. Salir")
        
    def execute_command(self, command):
        if command == "ls":
            print("Ejecutando comando 'ls'...")
        elif command == "cd":
            print("Ejecutando comando 'cd'...")
        elif command == "get":
            print("Ejecutando comando 'get'...")
        elif command == "put":
            print("Ejecutando comando 'put'...")
        elif command == "mkdir":
            print("Ejecutando comando 'mkdir'...")
        elif command == "rmdir":
            print("Ejecutando comando 'rmdir'...")
        elif command == "rm":
            print("Ejecutando comando 'rm'...")
        elif command == "8":
            print("Saliendo...")
            return False
        else:
            print("Comando no reconocido.")
        return True

if __name__ == "__main__":
    client = DFSClient('localhost', 5000)
    
    registrado = input("¿Ya está registrado? (s/n): ").lower()
    
    if registrado == 'n':
        # Registro de nuevo usuario
        username = input("Ingrese su nombre de usuario para registrarse: ")
        password = input("Ingrese su contraseña: ")
        if client.register(username, password):
            print("Por favor, inicie sesión con sus nuevas credenciales.")
        else:
            print("Error en el registro. Saliendo...")
            exit(1)
            
    # Si ya está registrado o se acaba de registrar correctamente
    username = input("Ingrese su nombre de usuario: ")
    password = input("Ingrese su contraseña: ")

    if client.authenticate(username, password):
        while True:
            client.show_menu()
            command = input("\nIngrese el comando a ejecutar (o 8 para salir): ")
            if not client.execute_command(command):
                break
    else:
        print("Autenticación fallida. Saliendo...")
