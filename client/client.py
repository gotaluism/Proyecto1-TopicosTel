import os
import sys
import grpc
import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc


# Asegurar que la carpeta 'protos' esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos')))


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

        self.delete_files_in_folder(destination_dir)  # Borrar archivos anteriores en la carpeta

        with open(source_path, 'rb') as file:
            chunk = file.read(chunk_size)  # Lee hasta el tamaño de 64KB
            metadata_table = []

            while chunk:
                chunk_name = os.path.join(destination_dir, f"block{chunk_num:02d}.txt")
                start_byte = (chunk_num - 1) * chunk_size
                end_byte = start_byte + len(chunk)

                # Guardar el bloque en la carpeta
                with open(chunk_name, 'wb') as chunk_file:
                    chunk_file.write(chunk)

                print(f"Created chunk {chunk_name}")
                
                # Añadir metadata a la tabla
                metadata_table.append({
                    "filename": filename,
                    "block_number": chunk_num,
                    "start_byte": start_byte,
                    "end_byte": end_byte,
                    "chunk_name": chunk_name
                })

                chunk_num += 1
                chunk = file.read(chunk_size)

        return metadata_table

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

        # Particionar el archivo en bloques y crear metadata
        metadata = self.partition(filename, file_dir, out_dir, chunk_size)

        # Enviar metadata al NameNode
        metadata_request = file_pb2.FileMetadataRequest(
            filename=filename,
            metadata=[file_pb2.FileBlockMetadata(
                block_number=block['block_number'],
                start_byte=block['start_byte'],
                end_byte=block['end_byte']
            ) for block in metadata]
        )
        response = self.stub.PutFileMetadata(metadata_request)

        if response.success:
            print("Metadata recibida del NameNode con ubicación de DataNodes:")
            for block in response.metadata:
                print(f"Bloque {block.block_number}: Bytes {block.start_byte} - {block.end_byte}, DataNode: {block.datanode}")

            # Enviar los bloques a los DataNodes
            for block, block_metadata in zip(metadata, response.metadata):
                self.send_to_datanode(block_metadata.datanode, block)

        return True

    def send_to_datanode(self, datanode_address, block):
        datanode_channel = grpc.insecure_channel(datanode_address)
        datanode_stub = file_pb2_grpc.DataNodeServiceStub(datanode_channel)

        request = file_pb2.StoreBlockRequest(
            filename=block['filename'],
            block_number=block['block_number'],
            data=open(block['chunk_name'], 'rb').read()
        )

        response = datanode_stub.StoreBlock(request)

        if response.success:
            print(f"Bloque {block['block_number']} enviado exitosamente a {datanode_address}.")
        else:
            print(f"Error al enviar bloque {block['block_number']} a {datanode_address}: {response.message}")

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
        username = input("Ingrese su nombre de usuario para registrarse: ")
        password = input("Ingrese su contraseña: ")
        if client.register(username, password):
            print("Por favor, inicie sesión con sus nuevas credenciales.")
        else:
            print("Error en el registro. Saliendo...")
            exit(1)

    username = input("Ingrese su nombre de usuario: ")
    password = input("Ingrese su contraseña:")

    if client.authenticate(username, password):
        while True:
            client.show_menu()
            command = input("\nIngrese el comando a ejecutar (o 8 para salir): ")
            if not client.execute_command(command):
                break
    else:
        print("Autenticación fallida. Saliendo...")
