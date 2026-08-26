from abc import ABC, abstractmethod
class StorageProvider(ABC):
    name = "base"
    @abstractmethod
    def put(self, stream, filename, mime_type): raise NotImplementedError
    @abstractmethod
    def open(self, storage_key): raise NotImplementedError
    @abstractmethod
    def delete(self, storage_key): raise NotImplementedError
