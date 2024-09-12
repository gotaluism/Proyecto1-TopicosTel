# Proyecto1-TopicosTel
Vanessa Velez <br>
Sara Cardona <br>
Luisa Maria Polanco <br>
Luis Miguel Giraldo <br>

## Arquitectura del Sistema

## Protocolos
o	Cliente <-> NameNode: gRPC (HTTP/2) <br>
o	NameNode <-> NameNode: gRPC (HTTP/2)  <br>
o	NameNode <-> DataNode: gRPC (HTTP/2)   <br>
o	DataNode <-> NameNode: gRPC (HTTP/2)   <br>
o	DataNode <-> DataNode: RPC (HTTP/2)   <br>
