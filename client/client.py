import os
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

    def partition(self, filename, in_path, out_path, chunk_size):
        
        source_path = os.path.join(in_path, filename)
        chunk_num = 1

        destination_dir = os.path.join(out_path, filename)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)

        self.delete_files_in_folder(destination_dir) #Si ya existía esa carpeta y con bloques adentro los borra para sobre escribirlos

        with open(source_path, 'rb') as file:
            chunk = file.read(chunk_size) #Lee hasta el tamaño de 64KB
            
            while chunk:
                chunk_name = os.path.join(destination_dir, f"block{chunk_num:02d}.txt")
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk) #Lo guarda en la carpeta downloads
                    
                print(f"Created chunk {chunk_name}") 
                
                chunk_num += 1
                chunk = file.read(chunk_size) #Lee desde el 64KB siguiente

    def delete_files_in_folder(self, folder_path):
        files = os.listdir(folder_path)
        
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def put(self, filepath):
        if not os.path.exists(filepath):
            print(f"El archivo {filepath} no existe.")
            return False

        filename = os.path.basename(filepath)
        file_dir = os.path.dirname(filepath)
        out_dir = './downloads' 
        chunk_size = 64 * 1024  # Tamaño de cada bloque 64 KB

        # Particionar el archivo en bloques y guardarlos en la carpeta downloads
        self.partition(filename, file_dir, out_dir, chunk_size)
        
        #Cuando ya se crearon los bloques entonces se envían al servidor en esta parte
        for chunk_filename in os.listdir(os.path.join(out_dir, filename)):
            chunk_path = os.path.join(out_dir, filename, chunk_filename)
            with open(chunk_path, 'rb') as chunk_file:
                data = chunk_file.read()


                request = file_pb2.PutFileRequest(filename=chunk_path, data=data)
                response = self.stub.PutFile(request)

                if response.success:
                    print(f"Bloque {chunk_filename} subido exitosamente.")
                else:
                    print(f"Error al subir el bloque {chunk_filename}: {response.message}")
                    return False

        return True

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
            filepath = input("Ingrese el camino al archivo local que desea subir: ")
            self.put(filepath)

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
