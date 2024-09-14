import sys
import os
import grpc
from concurrent import futures

# Asegurar que la carpeta 'protos' esté en el PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protos')))

import file_pb2 as file_pb2
import file_pb2_grpc as file_pb2_grpc

class DataNodeServicer(file_pb2_grpc.DataNodeServiceServicer):
    def StoreBlock(self, request, context):
        filename = request.filename
        block_number = request.block_number
        data = request.data
        out_dir = './datanode/downloads'
        file_dir = os.path.join(out_dir, filename)

        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
            

        block_path = os.path.join(file_dir, f'block_{block_number}.txt')

        try:
            with open(block_path, 'wb') as f:
                f.write(data)
            return file_pb2.StoreBlockResponse(success=True, message=f"Bloque {block_number} guardado correctamente.")
        except Exception as e:
            return file_pb2.StoreBlockResponse(success=False, message=f"Error al guardar el bloque: {str(e)}")
        
        
    def DeleteBlock(self, request, context):
        filename = request.filename

        # Definir la ruta a la carpeta donde se guardan los bloques del archivo
        out_dir = './datanode/downloads'
        file_dir = os.path.join(out_dir, filename)

        # Verifica si la carpeta del archivo existe
        if os.path.exists(file_dir):
            try:
                # Elimina todos los bloques dentro de la carpeta del archivo
                for block_file in os.listdir(file_dir):
                    block_path = os.path.join(file_dir, block_file)
                    os.remove(block_path)

                # Elimina la carpeta vacía del archivo
                os.rmdir(file_dir)

                print(f"Bloques del archivo '{filename}' eliminados exitosamente.")
                return file_pb2.DeleteBlockResponse(success=True, message="Bloques eliminados correctamente.")
            except Exception as e:
                return file_pb2.DeleteBlockResponse(success=False, message=f"Error al eliminar bloques: {str(e)}")
        else:
            return file_pb2.DeleteBlockResponse(success=False, message="El archivo no existe en este DataNode.")
def serve(datanode_name, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_pb2_grpc.add_DataNodeServiceServicer_to_server(DataNodeServicer(), server)
    server.add_insecure_port(f'[::]:{port}')
    print(f"{datanode_name} escuchando en el puerto {port}...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    # Cambiar a DataNode2 para el segundo nodo
    #serve('DataNode1', 5001)  
    #serve('DataNode2', 5002)
    serve('127.0.0.1',5001)
    #serve('127.0.0.1',5002)
