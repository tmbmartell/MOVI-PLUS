"""MOVI+ encrypted V5 backup verification: READ-ONLY and no customer data output.

Decrypts a local backup into ephemeral memory, validates tar contents and opens
a temporary SQLite copy for PRAGMA quick_check. Never overwrites production files.
"""
import argparse
import io
import json
import sqlite3
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from cryptography.fernet import Fernet, InvalidToken

MAX_ENCRYPTED=300*1024*1024
MAX_SQLITE=350*1024*1024
MAX_UNPACKED=800*1024*1024
MAX_FILES=10000

class UnsafeArchive(ValueError):
    pass

def verify(archive,master_key):
    archive=Path(archive).resolve()
    master_key=Path(master_key).resolve()
    if not archive.is_file() or not master_key.is_file():
        raise UnsafeArchive("Arquivo ou chave de backup não encontrados")
    if archive.stat().st_size>MAX_ENCRYPTED:
        raise UnsafeArchive("Backup criptografado acima do limite de verificação")
    try:
        crypto=Fernet(master_key.read_bytes())
        unsealed=crypto.decrypt(archive.read_bytes())
    except (ValueError,InvalidToken,TypeError):
        raise UnsafeArchive("Backup não autenticado pela chave indicada")
    if len(unsealed)>MAX_UNPACKED:
        raise UnsafeArchive("Backup descompactado maior que o permitido")
    try:
        tar=tarfile.open(fileobj=io.BytesIO(unsealed),mode="r:gz")
    except (tarfile.TarError,EOFError,ValueError):
        raise UnsafeArchive("Pacote de backup comprimido inválido")
    with tar:
        members=tar.getmembers()
        if len(members)>MAX_FILES:
            raise UnsafeArchive("Muitos arquivos no pacote")
        seen=set();total=0;valid_items={}
        for m in members:
            path=PurePosixPath(m.name)
            if (path.is_absolute() or '..' in path.parts or
                    not m.isfile() or m.name in seen or m.size<0):
                raise UnsafeArchive("Entrada inválida ou duplicada no backup")
            if (m.name not in ("database.sqlite3","encryption-key") and
                not m.name.startswith(("documents/","program-media/"))):
                raise UnsafeArchive("Arquivo não previsto no backup")
            if len(path.parts)>2 and m.name not in ("database.sqlite3","encryption-key"):
                raise UnsafeArchive("Caminho inesperado no backup")
            seen.add(m.name)
            total+=m.size
            if total>MAX_UNPACKED:raise UnsafeArchive("Pacote além do limite")
            valid_items[m.name]=m
        for required in ("database.sqlite3","encryption-key"):
            if required not in valid_items:raise UnsafeArchive("Backup incompleto")
        dbentry=valid_items["database.sqlite3"]
        if dbentry.size>MAX_SQLITE:
            raise UnsafeArchive("Banco acima do limite da auditoria")
        keyentry=valid_items["encryption-key"]
        if keyentry.size>4096:
            raise UnsafeArchive("Chave interna com tamanho inválido")
        extracted_key=tar.extractfile(keyentry)
        extracted_db=tar.extractfile(dbentry)
        if extracted_key is None or extracted_db is None:
            raise UnsafeArchive("Arquivo principal ilegível")
        with extracted_key as k:
            try:Fernet(k.read())
            except (ValueError,TypeError):
                raise UnsafeArchive("Chave de criptografia de registros inválida")
        with tempfile.TemporaryDirectory(prefix="movi_restore_verify_") as folder:
            dbfile=Path(folder)/"recovered.sqlite3"
            with extracted_db as inp,dbfile.open("wb") as out:
                total_bytes=0
                while data:=inp.read(1024*1024):
                    total_bytes+=len(data)
                    if total_bytes>MAX_SQLITE:raise UnsafeArchive("Banco excede limite")
                    out.write(data)
            db=sqlite3.connect("file:"+str(dbfile)+"?mode=ro",uri=True,timeout=5)
            try:
                integrity=db.execute("PRAGMA quick_check(1)").fetchone()
                if not integrity or integrity[0]!="ok":
                    raise UnsafeArchive("Integridade SQLite inválida")
                schema={r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if not {"users","transactions","consents"}.issubset(schema):
                    raise UnsafeArchive("Estrutura básica do banco não encontrada")
            except sqlite3.Error:
                raise UnsafeArchive("Falha ao ler banco recuperado")
            finally:db.close()
        return {"verified":True,"sqlite_integrity":"ok",
                "database_present":True,"encrypted_data_key_valid":True,
                "backup_files":len(members),"mode":"read_only_test_restore",
                "external_copy_verified":False,
                "notice":"Esta auditoria não substitui restauração operacional ou cópia externa."}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",required=True)
    parser.add_argument("--master-key",required=True)
    args=parser.parse_args()
    try:
        result=verify(args.archive,args.master_key)
    except (UnsafeArchive,OSError) as e:
        print(json.dumps({"verified":False,"error":str(e)},ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":main()
