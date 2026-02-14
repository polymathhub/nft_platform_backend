from uuid import UUID as Python_UUID
from sqlalchemy import TypeDecorator, CHAR, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        
        if isinstance(value, Python_UUID):
            if dialect.name == "postgresql":
                return str(value)
            return value.hex
        
        if isinstance(value, str):
            if dialect.name == "postgresql":
                return str(value)
            return Python_UUID(value).hex
        
        raise TypeError(f"Cannot convert {type(value)} to UUID")

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        
        if isinstance(value, Python_UUID):
            return value
        
        return Python_UUID(value)
