import sys
import os
import grpc
import time
from concurrent import futures

# Asegurar que la carpeta 'protos' esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos')))

import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc

class DataNodeServicer(file_pb2_grpc.DataNodeServiceServicer):
    def __init__(self, datanode_name, namenode_stub):
        self.datanode_name = datanode_name
        self.namenode_stub = namenode_stub
        self.stored_blocks = []  

    def send_heartbeat(self, port):
        while True:
            try:
                # Envía el heartbeat con la lista de bloques
                heartbeat_request = file_pb2.HeartbeatRequest(
                    datanode_name=f"{self.datanode_name}:{port}",
                    stored_blocks=self.stored_blocks  # Envía la lista de bloques almacenados
                )
                response = self.namenode_stub.Heartbeat(heartbeat_request)
                print(f"Heartbeat enviado desde {self.datanode_name} en el puerto {port}. Respuesta del NameNode: {response.status}")

            except Exception as e:
                print(f"Error al enviar heartbeat desde {self.datanode_name} en el puerto {port}: {str(e)}")

            time.sleep(5)  # Enviar heartbeat cada 5 segundos


    # def get_available_storage(self):
    #     # Simular almacenamiento disponible (en GB)
    #     return 100  # Ejemplo: 100 GB disponibles

    def get_storage_directory(self):
        """Utiliza la ruta de almacenamiento existente en la carpeta 'downloads'."""
        return './downloads'
    
    def get_stored_blocks(self):
        """Obtiene la lista de bloques almacenados en este DataNode"""
        storage_dir = self.get_storage_directory()
        stored_blocks = []
        for dirpath, dirnames, filenames in os.walk(storage_dir):
            for filename in filenames:
                relative_path = os.path.relpath(os.path.join(dirpath, filename), storage_dir)
                stored_blocks.append(relative_path)
        return stored_blocks

    def StoreBlock(self, request, context):
        filename = request.filename
        block_number = request.block_number
        data = request.data
        storage_dir = self.get_storage_directory()  # Usa la carpeta común 'downloads'
        file_dir = os.path.join(storage_dir, filename)

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        block_path = os.path.join(file_dir, f'block_{block_number}.txt')

        try:
            with open(block_path, 'wb') as f:
                f.write(data)

            # Actualizar la lista de bloques almacenados
            block_entry = f'{filename}\\block_{block_number}.txt'
            if block_entry not in self.stored_blocks:
                self.stored_blocks.append(block_entry)

            return file_pb2.StoreBlockResponse(success=True, message=f"Bloque {block_number} guardado correctamente.")
        except Exception as e:
            return file_pb2.StoreBlockResponse(success=False, message=f"Error al guardar el bloque: {str(e)}")

    def DeleteBlock(self, request, context):
        filename = request.filename

        # Definir la ruta a la carpeta donde se guardan los bloques del archivo
        storage_dir = self.get_storage_directory()
        file_dir = os.path.join(storage_dir, filename)

        # Verifica si la carpeta del archivo existe
        if os.path.exists(file_dir):
            try:
                # Elimina todos los bloques dentro de la carpeta del archivo
                for block_file in os.listdir(file_dir):
                    block_path = os.path.join(file_dir, block_file)
                    os.remove(block_path)

                    # Remover el bloque de la lista de bloques almacenados
                    block_entry = f'{filename}\\{block_file}'
                    if block_entry in self.stored_blocks:
                        self.stored_blocks.remove(block_entry)  # ACTUALIZAR LA LISTA DE BLOQUES

                # Elimina la carpeta vacía del archivo
                os.rmdir(file_dir)

                print(f"Bloques del archivo '{filename}' eliminados exitosamente.")
                return file_pb2.DeleteBlockResponse(success=True, message="Bloques eliminados correctamente.")
            except Exception as e:
                return file_pb2.DeleteBlockResponse(success=False, message=f"Error al eliminar bloques: {str(e)}")
        else:
            return file_pb2.DeleteBlockResponse(success=False, message="El archivo no existe en este DataNode.")


def serve(datanode_name, port):
    # Conectar con el NameNode
    channel = grpc.insecure_channel('localhost:5000')
    stub = file_pb2_grpc.NameNodeServiceStub(channel)
    
    datanode_servicer = DataNodeServicer(datanode_name, stub)
    
    # Iniciar el servidor para recibir bloques
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_DataNodeServiceServicer_to_server(datanode_servicer, server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"{datanode_name} escuchando en el puerto {port}...")
    server.start()

    # Enviar heartbeats periódicamente al NameNode
    datanode_servicer.send_heartbeat(port)
    server.wait_for_termination()

if __name__ == "__main__":
    # Cambiar a DataNode2 para el segundo nodo
    #serve('DataNode1', 5001)  
    #serve('DataNode2', 5002)
    
    serve('127.0.0.1',5001)
    #serve('127.0.0.1',5002)
    #serve('127.0.0.1',5003)
