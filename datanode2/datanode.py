import sys
import os
import grpc
import time
from concurrent import futures
import threading

# Asegurar que la carpeta 'protos' esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'protos')))


import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc

class DataNodeServicer(file_pb2_grpc.DataNodeServiceServicer):
    def __init__(self, ip_address, port, namenode_stub):
        self.ip_address = ip_address
        self.port = port
        self.datanode_name = f"{ip_address}:{port}"
        self.namenode_stub = namenode_stub
        self.stored_blocks = []
        self.registered = False

    def register_with_namenode(self):
        while not self.registered:
            try:
                register_request = file_pb2.DataNodeRegisterRequest(
                    datanode_name=self.datanode_name,
                    ip_address=self.ip_address,
                    port=self.port
                )
                response = self.namenode_stub.RegisterDataNode(register_request)
                if response.success:
                    print(f"Registro exitoso con NameNode: {response.message}")
                    self.registered = True
                else:
                    print(f"Fallo en el registro con NameNode: {response.message}")
                    time.sleep(5)
            except Exception as e:
                print(f"Error durante el registro con NameNode: {str(e)}")
                time.sleep(5)

    def send_heartbeat(self):
        while True:
            if not self.registered:
                print("DataNode no registrado. Intentando registrar...")
                self.register_with_namenode()
                continue

            try:
                heartbeat_request = file_pb2.HeartbeatRequest(
                    datanode_name=self.datanode_name,
                    stored_blocks=self.get_stored_blocks()
                )
                response = self.namenode_stub.Heartbeat(heartbeat_request)
                print(f"Heartbeat enviado desde {self.datanode_name}. Respuesta del NameNode: {response.status}")
            except Exception as e:
                print(f"Error al enviar heartbeat: {str(e)}")
                self.registered = False
            time.sleep(5)

    def get_storage_directory(self):
        """Devuelve el directorio de almacenamiento para este DataNode."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, 'downloads')

    def get_stored_blocks(self):
        """Obtiene la lista de bloques almacenados en este DataNode"""
        storage_dir = self.get_storage_directory()
        stored_blocks = []
        for dirpath, dirnames, filenames in os.walk(storage_dir):
            for filename in filenames:
                if 'block' in filename:
                    relative_path = os.path.relpath(os.path.join(dirpath, filename), storage_dir)
                    stored_blocks.append(relative_path)
        return stored_blocks

    def send_block_report(self):
        while True:
            if not self.registered:
                time.sleep(5)
                continue

            try:
                block_info = self.get_block_info()
                report_request = file_pb2.BlockReportRequest(
                    datanode_name=self.datanode_name,
                    blocks=block_info
                )
                response = self.namenode_stub.BlockReport(report_request)
                print(f"Block Report enviado desde {self.datanode_name}. Respuesta del NameNode: {response.message}")
            except Exception as e:
                print(f"Error al enviar Block Report: {str(e)}")
            time.sleep(60)  # Enviar Block Report cada 60 segundos

    def get_block_info(self):
        storage_dir = self.get_storage_directory()
        block_info = []
        for dirpath, dirnames, filenames in os.walk(storage_dir):
            for filename in filenames:
                if 'block' in filename:
                    # Extraer el número de bloque del nombre del archivo
                    try:
                        block_number_str = filename.split('_')[1].split('.')[0]
                        block_number = int(block_number_str)
                    except (IndexError, ValueError):
                        print(f"Formato de bloque inválido: {filename}")
                        continue

                    original_filename = os.path.basename(dirpath)
                    block_id = f"{original_filename}::block::{block_number}"
                    file_size = os.path.getsize(os.path.join(dirpath, filename))
                    block_info.append(file_pb2.BlockInfo(
                        block_id=block_id,
                        size=file_size
                    ))
        return block_info


    def StoreBlock(self, request, context):
        filename = request.filename
        block_number = request.block_number
        data = request.data
        storage_dir = self.get_storage_directory()
        file_dir = os.path.join(storage_dir, filename)

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        block_path = os.path.join(file_dir, f'block_{block_number}.txt')

        try:
            with open(block_path, 'wb') as f:
                f.write(data)

            # Actualizar la lista de bloques almacenados con el nuevo formato de block_id
            block_id = f"{filename}::block::{block_number}"
            if block_id not in self.stored_blocks:
                self.stored_blocks.append(block_id)

            print(f"Bloque {block_number} del archivo '{filename}' almacenado en {self.datanode_name}.")
            return file_pb2.StoreBlockResponse(success=True, message=f"Bloque {block_number} guardado correctamente.")
        except Exception as e:
            return file_pb2.StoreBlockResponse(success=False, message=f"Error al guardar el bloque: {str(e)}")

    def DeleteBlock(self, request, context):
        filename = request.filename
        block_number = request.block_number

        storage_dir = self.get_storage_directory()
        file_dir = os.path.join(storage_dir, filename)
        block_path = os.path.join(file_dir, f'block_{block_number}.txt')

        if os.path.exists(block_path):
            try:
                os.remove(block_path)

                block_entry = os.path.join(filename, f'block_{block_number}.txt')
                if block_entry in self.stored_blocks:
                    self.stored_blocks.remove(block_entry)

                print(f"Bloque '{block_number}' del archivo '{filename}' eliminado exitosamente del DataNode {self.datanode_name}.")
                return file_pb2.DeleteBlockResponse(success=True, message="Bloque eliminado correctamente.")
            except Exception as e:
                print(f"Error al eliminar el bloque '{block_number}' del archivo '{filename}' en DataNode {self.datanode_name}: {str(e)}")
                return file_pb2.DeleteBlockResponse(success=False, message=f"Error al eliminar bloque: {str(e)}")
        else:
            print(f"El bloque '{block_number}' del archivo '{filename}' no existe en DataNode {self.datanode_name}.")
            return file_pb2.DeleteBlockResponse(success=False, message="El bloque no existe en este DataNode.")

    def RetrieveBlock(self, request, context):
        filename = request.filename
        block_number = request.block_number
        storage_dir = self.get_storage_directory()
        file_dir = os.path.join(storage_dir, filename)
        block_path = os.path.join(file_dir, f'block_{block_number}.txt')

        if not os.path.exists(block_path):
            return file_pb2.RetrieveBlockResponse(success=False, message=f"Bloque {block_number} no encontrado.")

        try:
            with open(block_path, 'rb') as f:
                data = f.read()
            print(f"Bloque {block_number} del archivo '{filename}' enviado desde DataNode {self.datanode_name}.")
            return file_pb2.RetrieveBlockResponse(success=True, data=data)
        except Exception as e:
            return file_pb2.RetrieveBlockResponse(success=False, message=f"Error al leer el bloque: {str(e)}")

def serve(ip_address, port):
    # Conectar con el NameNode
    channel = grpc.insecure_channel('localhost:5000')
    stub = file_pb2_grpc.NameNodeServiceStub(channel)
    
    datanode_servicer = DataNodeServicer(ip_address, port, stub)

    # Registrar el DataNode con el NameNode
    datanode_servicer.register_with_namenode()
    
    # Iniciar el servidor para recibir bloques
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_DataNodeServiceServicer_to_server(datanode_servicer, server)
    server.add_insecure_port(f'{ip_address}:{port}')
    print(f"DataNode escuchando en {ip_address}:{port}...")
    server.start()

    # Iniciar el envío de heartbeats en un hilo separado
    heartbeat_thread = threading.Thread(target=datanode_servicer.send_heartbeat)
    heartbeat_thread.start()

    block_report_thread = threading.Thread(target=datanode_servicer.send_block_report)
    block_report_thread.start()

    server.wait_for_termination()

if __name__ == "__main__":
    # Solicitar al usuario el número del DataNode
    node_number = int(input("Ingrese el número del DataNode (por ejemplo, 1 para el DataNode1): "))
    port = 5000 + node_number
    serve('127.0.0.1', port)
