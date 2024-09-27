import os
import sys
import grpc
import shutil

# Asegurar que la carpeta 'protos' esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos')))

import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc


class DFSClient:
    def __init__(self, namenode_host, namenode_port):
        self.channel = grpc.insecure_channel(f'{namenode_host}:{namenode_port}')
        self.stub = file_pb2_grpc.NameNodeServiceStub(self.channel)
        self.username = None
        self.path = None

    def authenticate(self, username, password):
        request = file_pb2.LoginRequest(username=username, password=password)
        response = self.stub.Authenticate(request)
        if response.success:
            print(f"Autenticación exitosa: {response.message}")
            self.username = username
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

    def partition(self, filename, in_path, chunk_size):
        source_path = os.path.join(in_path, filename)
        chunk_num = 1

        # Directorio temporal para almacenar los bloques
        temp_dir = './temp'
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        self.delete_files_in_folder(temp_dir)  # Borrar archivos anteriores en la carpeta

        with open(source_path, 'rb') as file:
            chunk = file.read(chunk_size)  # Lee hasta el tamaño de 64KB
            metadata_table = []

            while chunk:
                chunk_name = os.path.join(temp_dir, f"{filename}_block{chunk_num:02d}.txt")
                start_byte = (chunk_num - 1) * chunk_size
                end_byte = start_byte + len(chunk)

                # Guardar el bloque en la carpeta temporal
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
        if os.path.exists(folder_path):
            files = os.listdir(folder_path)
            for file_name in files:
                file_path = os.path.join(folder_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

    def put(self, filepath):
        if not os.path.exists(filepath):
            print(f"El archivo {filepath} no existe.")
            return False

        filename = os.path.basename(filepath)
        file_dir = os.path.dirname(filepath)

        chunk_size = 64 * 1024  # Tamaño de cada bloque 64 KB

        # Particionar el archivo en bloques y crear metadata
        metadata = self.partition(filename, file_dir, chunk_size)

        if self.path:
            filename = os.path.join(self.path, filename)     
        # Enviar metadata al NameNode
        metadata_request = file_pb2.FileMetadataRequest(
            filename=filename,
            username=self.username,
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
                print(f"Bloque {block.block_number}: Bytes {block.start_byte} - {block.end_byte}, DataNodes: {block.datanodes}")

            # Enviar los bloques a los DataNodes
            for block_info, block_metadata in zip(metadata, response.metadata):
                for datanode in block_metadata.datanodes:
                    self.send_to_datanode(datanode, block_info)

            # Limpiar directorio temporal
            self.delete_files_in_folder('./temp')

        return True
    
    def get(self, filename):
        if self.username is None:
            print("No hay un usuario autenticado.")
            return False

        metadata_request = file_pb2.FileMetadataRequest(
            filename=filename,
            username=self.username
        )
        response = self.stub.GetFileMetadata(metadata_request)
        # print(response.metadata)

        if not response.success:
            print(f"Error al obtener metadata del archivo {filename}: {response.message}")
            return False

        # Crear la carpeta de salida 'recovered' si no existe
        out_dir = './recovered'
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        # Asegurarnos de que no exista un directorio con el mismo nombre del archivo
        file_path = os.path.join(out_dir, os.path.basename(filename))
        if os.path.isdir(file_path):
            print(f"Error: Existe un directorio con el mismo nombre del archivo '{filename}' en 'recovered'.")
            return False

        # Descargar cada bloque desde los DataNodes correspondientes
        file_blocks = []
        for block in response.metadata:
            block_data = None
            for datanode in block.datanodes:
                block_data = self.retrieve_from_datanode(datanode, filename, block.block_number)
                if block_data:
                    print(f"Bloque {block.block_number} descargado desde {datanode}.")
                    break  # Si se obtiene el bloque, no se intenta con otros DataNodes
                else:
                    print(f"DataNode {datanode} no disponible o bloque no encontrado.")
            if block_data:
                file_blocks.append((block.block_number, block_data))
            else:
                print(f"Error al descargar bloque {block.block_number}: no se pudo recuperar de ningún DataNode.")
                return False

        # Ordenar los bloques por número para reconstruir el archivo
        file_blocks.sort(key=lambda x: x[0])

        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        # Ensamblar el archivo en la carpeta 'recovered'
        with open(file_path, 'wb') as file:
            for _, block_data in file_blocks:
                file.write(block_data)

        print(f"Archivo '{filename}' ensamblado correctamente en '{file_path}'.")
        return True

    def retrieve_from_datanode(self, datanode_address, filename, block_number):
        try:
            datanode_channel = grpc.insecure_channel(datanode_address)
            datanode_stub = file_pb2_grpc.DataNodeServiceStub(datanode_channel)

            request = file_pb2.RetrieveBlockRequest(
                filename=filename,
                block_number=block_number
            )

            response = datanode_stub.RetrieveBlock(request)

            if response.success:
                return response.data
            else:
                print(f"DataNode {datanode_address} respondió pero no encontró el bloque {block_number}.")
                return None
        except grpc.RpcError:
            # Manejar errores de conexión de manera silenciosa
            return None

    def ls(self):
        if self.username is None:
            print("No hay un usuario autenticado.")
            return
        
        request = file_pb2.ListFilesRequest(username=self.username)
        response = self.stub.ListFiles(request)

        if response.success:
            print("Archivos del usuario:")
            for filename in response.filenames:
                print(filename)
            print("Carpetas del usuario:")
            for directoryname in response.directorynames:
                print(directoryname)
        else:
            print(f"Error al obtener lista de archivos: {response.message}")
        
    def mkdir(self, directory):
        directory = directory.strip()

        if not directory:
            print("Error: El nombre del directorio no puede estar vacío.")
            return

        if self.path:
            directory = os.path.join(self.path, directory)

        request = file_pb2.MkdirRequest(username=self.username, directory=directory)
        response = self.stub.Mkdir(request)

        if response.success:
            print(f"Directorio '{directory}' creado con éxito.")
        else:
            print(f"Error al crear el directorio: {response.message}")

    def rmdir(self, directory):

        if not directory:
            print("Error: El nombre del directorio no puede estar vacío.")
            return

        if self.path:
            directory = os.path.join(self.path, directory)

        request = file_pb2.RmdirRequest(username=self.username, directory=directory)
        response = self.stub.Rmdir(request)

        if response.success:
            print(f"Directorio '{directory}' eliminado con éxito.")
        else:
            print(f"Error al eliminar el directorio: {response.message}")
    
    def rm(self, filename):
        if self.path:
            filename = os.path.join(self.path, filename)

        request = file_pb2.DeleteFileRequest(username=self.username, filename=filename)
        response = self.stub.DeleteFile(request)

        if response.success:
            print(f"Archivo '{filename}' eliminado con éxito del sistema distribuido.")
        else:
            print(f"Error al eliminar el archivo: {response.message}")
            
    def send_to_datanode(self, datanode_address, block):
        try:
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
        except Exception as e:
            print(f"Excepción al enviar bloque {block['block_number']} a {datanode_address}: {str(e)}")

    def cd(self):
        if self.username is None:
            print("No hay un usuario autenticado.")
            return
        
        print("Ingrese el nombre del directorio que desea usar: ")
        directoryName = input()

        if directoryName == "..":
            if self.path:
                self.path = "/".join(self.path.split("/")[:-1]) if self.path else None
                print(f"Directorio actual: {self.path if self.path else 'root'}")
            else:
                print("Ya estás en el directorio raíz.")
        else:    
            request = file_pb2.ListFilesRequest(username=self.username)
            response = self.stub.ListFiles(request)

            if directoryName in response.directorynames:
                self.path = self._get_full_path(directoryName)
                print(f"Directorio actual: {self.path}")
            else:
                print("Esta carpeta no existe")


    def _get_full_path(self, name):
        """Devuelve la ruta completa concatenando el directorio actual y el nombre."""
        if self.path:
            return f"{self.path}/{name}"
        return name
            

    def show_menu(self):
        if self.path:
            print("Tu ruta actual es: " + self.path)
        else:
            print("Estás en el directorio raíz.")
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
            self.ls()
        elif command == "cd": 
            self.cd()
        elif command == "get":
            filename = input("Ingrese el nombre del archivo que desea descargar: ")
            if self.path:
                filename = os.path.join(self.path, filename)
            self.get(filename)
        elif command == "put":
            filepath = input("Ingrese la ruta al archivo local que desea subir: ")
            self.put(filepath)
        elif command == "mkdir":
            directory = input("Ingrese el nombre del directorio a crear: ")
            self.mkdir(directory)
        elif command == "rmdir":
            directory = input("Ingrese el nombre del directorio a eliminar: ")
            self.rmdir(directory)
        elif command == "rm":
            filename = input("Ingrese el nombre del archivo a eliminar: ")
            self.rm(filename)
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
