from pathlib import Path
import uuid
class LocalStorageProvider:
    name = "local"
    def __init__(self, root):
        self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def put(self, stream, filename, mime_type):
        key=uuid.uuid4().hex; p=self.root/key; size=0
        with p.open("wb") as out:
            while chunk:=stream.read(1024*1024):
                out.write(chunk); size+=len(chunk)
        return {"storage_key":key,"size":size}
    def open(self,key):
        p=self.root/key
        if not p.exists(): raise FileNotFoundError(key)
        return p.open("rb")
    def delete(self,key):
        p=self.root/key
        if p.exists(): p.unlink()
