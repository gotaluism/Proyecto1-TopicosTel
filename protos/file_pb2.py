# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: file.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'file.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nfile.proto\x12\x03\x64\x66s\"2\n\x0cLoginRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"1\n\rLoginResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"5\n\x0fRegisterRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"4\n\x10RegisterResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"a\n\x11\x46ileBlockMetadata\x12\x14\n\x0c\x62lock_number\x18\x01 \x01(\x05\x12\x12\n\nstart_byte\x18\x02 \x01(\x03\x12\x10\n\x08\x65nd_byte\x18\x03 \x01(\x03\x12\x10\n\x08\x64\x61tanode\x18\x04 \x01(\t\"c\n\x13\x46ileMetadataRequest\x12\x10\n\x08\x66ilename\x18\x01 \x01(\t\x12\x10\n\x08username\x18\x02 \x01(\t\x12(\n\x08metadata\x18\x03 \x03(\x0b\x32\x16.dfs.FileBlockMetadata\"Q\n\x14\x46ileMetadataResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12(\n\x08metadata\x18\x02 \x03(\x0b\x32\x16.dfs.FileBlockMetadata\"I\n\x11StoreBlockRequest\x12\x10\n\x08\x66ilename\x18\x01 \x01(\t\x12\x14\n\x0c\x62lock_number\x18\x02 \x01(\x05\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\x0c\"6\n\x12StoreBlockResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"$\n\x10ListFilesRequest\x12\x10\n\x08username\x18\x01 \x01(\t\"`\n\x11ListFilesResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x11\n\tfilenames\x18\x02 \x03(\t\x12\x16\n\x0e\x64irectorynames\x18\x03 \x03(\t\x12\x0f\n\x07message\x18\x04 \x01(\t\"3\n\x0cMkdirRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\tdirectory\x18\x02 \x01(\t\"1\n\rMkdirResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"3\n\x0cRmdirRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x11\n\tdirectory\x18\x02 \x01(\t\"1\n\rRmdirResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"7\n\x11\x44\x65leteFileRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08\x66ilename\x18\x02 \x01(\t\"6\n\x12\x44\x65leteFileResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"&\n\x12\x44\x65leteBlockRequest\x12\x10\n\x08\x66ilename\x18\x01 \x01(\t\"7\n\x13\x44\x65leteBlockResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"\"\n\x0eGetFileRequest\x12\x10\n\x08\x66ilepath\x18\x01 \x01(\t2\xa4\x03\n\x0fNameNodeService\x12\x35\n\x0c\x41uthenticate\x12\x11.dfs.LoginRequest\x1a\x12.dfs.LoginResponse\x12\x37\n\x08Register\x12\x14.dfs.RegisterRequest\x1a\x15.dfs.RegisterResponse\x12\x46\n\x0fPutFileMetadata\x12\x18.dfs.FileMetadataRequest\x1a\x19.dfs.FileMetadataResponse\x12:\n\tListFiles\x12\x15.dfs.ListFilesRequest\x1a\x16.dfs.ListFilesResponse\x12.\n\x05Mkdir\x12\x11.dfs.MkdirRequest\x1a\x12.dfs.MkdirResponse\x12.\n\x05Rmdir\x12\x11.dfs.RmdirRequest\x1a\x12.dfs.RmdirResponse\x12=\n\nDeleteFile\x12\x16.dfs.DeleteFileRequest\x1a\x17.dfs.DeleteFileResponse2\x92\x01\n\x0f\x44\x61taNodeService\x12=\n\nStoreBlock\x12\x16.dfs.StoreBlockRequest\x1a\x17.dfs.StoreBlockResponse\x12@\n\x0b\x44\x65leteBlock\x12\x17.dfs.DeleteBlockRequest\x1a\x18.dfs.DeleteBlockResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'file_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_LOGINREQUEST']._serialized_start=19
  _globals['_LOGINREQUEST']._serialized_end=69
  _globals['_LOGINRESPONSE']._serialized_start=71
  _globals['_LOGINRESPONSE']._serialized_end=120
  _globals['_REGISTERREQUEST']._serialized_start=122
  _globals['_REGISTERREQUEST']._serialized_end=175
  _globals['_REGISTERRESPONSE']._serialized_start=177
  _globals['_REGISTERRESPONSE']._serialized_end=229
  _globals['_FILEBLOCKMETADATA']._serialized_start=231
  _globals['_FILEBLOCKMETADATA']._serialized_end=328
  _globals['_FILEMETADATAREQUEST']._serialized_start=330
  _globals['_FILEMETADATAREQUEST']._serialized_end=429
  _globals['_FILEMETADATARESPONSE']._serialized_start=431
  _globals['_FILEMETADATARESPONSE']._serialized_end=512
  _globals['_STOREBLOCKREQUEST']._serialized_start=514
  _globals['_STOREBLOCKREQUEST']._serialized_end=587
  _globals['_STOREBLOCKRESPONSE']._serialized_start=589
  _globals['_STOREBLOCKRESPONSE']._serialized_end=643
  _globals['_LISTFILESREQUEST']._serialized_start=645
  _globals['_LISTFILESREQUEST']._serialized_end=681
  _globals['_LISTFILESRESPONSE']._serialized_start=683
  _globals['_LISTFILESRESPONSE']._serialized_end=779
  _globals['_MKDIRREQUEST']._serialized_start=781
  _globals['_MKDIRREQUEST']._serialized_end=832
  _globals['_MKDIRRESPONSE']._serialized_start=834
  _globals['_MKDIRRESPONSE']._serialized_end=883
  _globals['_RMDIRREQUEST']._serialized_start=885
  _globals['_RMDIRREQUEST']._serialized_end=936
  _globals['_RMDIRRESPONSE']._serialized_start=938
  _globals['_RMDIRRESPONSE']._serialized_end=987
  _globals['_DELETEFILEREQUEST']._serialized_start=989
  _globals['_DELETEFILEREQUEST']._serialized_end=1044
  _globals['_DELETEFILERESPONSE']._serialized_start=1046
  _globals['_DELETEFILERESPONSE']._serialized_end=1100
  _globals['_DELETEBLOCKREQUEST']._serialized_start=1102
  _globals['_DELETEBLOCKREQUEST']._serialized_end=1140
  _globals['_DELETEBLOCKRESPONSE']._serialized_start=1142
  _globals['_DELETEBLOCKRESPONSE']._serialized_end=1197
  _globals['_GETFILEREQUEST']._serialized_start=1199
  _globals['_GETFILEREQUEST']._serialized_end=1233
  _globals['_NAMENODESERVICE']._serialized_start=1236
  _globals['_NAMENODESERVICE']._serialized_end=1656
  _globals['_DATANODESERVICE']._serialized_start=1659
  _globals['_DATANODESERVICE']._serialized_end=1805
# @@protoc_insertion_point(module_scope)
