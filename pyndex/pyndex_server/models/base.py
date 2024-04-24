from piccolo.table import Table
from piccolo.columns import *
from .bootstrap import CONTEXT


class BaseSchema(Table, db=CONTEXT.db):
    id = UUID()
