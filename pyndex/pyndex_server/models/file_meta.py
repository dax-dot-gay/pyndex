from .base import *


class FileMetadata(BaseSchema, tablename="files_meta"):
    metadata_version = Varchar(length=3)
    name = Varchar()
    version = Varchar()
