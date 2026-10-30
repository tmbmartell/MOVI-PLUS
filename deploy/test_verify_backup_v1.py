"""Deterministic synthetic backup integrity and malicious archive tests."""
import io
import os
import sqlite3
import sys
import tarfile
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet

sys.path.insert(0,str(Path(__file__).resolve().parent))
from verify_backup_v1 import verify,UnsafeArchive

with tempfile.TemporaryDirectory(prefix="movi_backup_qa_") as td:
    d=Path(td)
    database=d/"sample.sqlite3"
    conn=sqlite3.connect(database)
    for name in ("users","transactions","consents"):
        conn.execute("CREATE TABLE "+name+" (id INTEGER PRIMARY KEY)")
    conn.execute("INSERT INTO users(id) VALUES(1)");conn.commit();conn.close()
    data_key=Fernet.generate_key()
    master=Fernet.generate_key()
    (d/"master").write_bytes(master)
    def build(files):
        mem=io.BytesIO()
        with tarfile.open(fileobj=mem,mode="w:gz") as tar:
            for name,blob in files:
                info=tarfile.TarInfo(name);info.size=len(blob)
                tar.addfile(info,io.BytesIO(blob))
        return Fernet(master).encrypt(mem.getvalue())
    good=build([("database.sqlite3",database.read_bytes()),("encryption-key",data_key)])
    arch=d/"backup.enc";arch.write_bytes(good)
    result=verify(arch,d/"master")
    assert result["verified"] is True
    assert result["sqlite_integrity"]=="ok"
    assert result["external_copy_verified"] is False
    print("01 - encrypted realistic SQLite backup passes read-only test restore: PASS")

    broken=d/"broken.enc";broken.write_bytes(good[:-1]+b"0")
    try:verify(broken,d/"master")
    except UnsafeArchive:pass
    else:raise AssertionError("tampered ciphertext accepted")
    print("02 - authenticated encryption rejects tampered backup: PASS")

    keyfile=d/"wrong-master";keyfile.write_bytes(Fernet.generate_key())
    try:verify(arch,keyfile)
    except UnsafeArchive:pass
    else:raise AssertionError("wrong key accepted")
    print("03 - incorrect backup master key rejected: PASS")

    for badfiles in (
        [("../unsafe",b"x"),("database.sqlite3",database.read_bytes()),("encryption-key",data_key)],
        [("database.sqlite3",database.read_bytes()),("database.sqlite3",database.read_bytes()),("encryption-key",data_key)],
        [("database.sqlite3",database.read_bytes())],
    ):
        arch.write_bytes(build(badfiles))
        try:verify(arch,d/"master")
        except UnsafeArchive:pass
        else:raise AssertionError("unsafe archive accepted")
    print("04 - path traversal, duplicates and missing encryption key rejected: PASS")
print("4/4 synthetic backup verification tests PASS; no client data processed.")
