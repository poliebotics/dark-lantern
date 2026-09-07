#!/usr/bin/env python3
"""Extract only hash-pinned SP1 Groth16 circuit files from an untrusted tarball."""

from __future__ import annotations

import hashlib
import pathlib
import sys
import tarfile


def read_manifest(path: pathlib.Path) -> dict[str, str]:
    expected: dict[str, str] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        if len(digest) != 64 or pathlib.PurePosixPath(name).name != name:
            raise ValueError("invalid circuit checksum manifest")
        expected[name] = digest
    if not expected:
        raise ValueError("empty circuit checksum manifest")
    return expected


def main() -> int:
    if len(sys.argv) != 4:
        raise SystemExit("usage: prepare_groth16_circuits.py TAR SHA256SUMS OUTPUT_DIR")
    archive = pathlib.Path(sys.argv[1]).resolve(strict=True)
    manifest = pathlib.Path(sys.argv[2]).resolve(strict=True)
    output = pathlib.Path(sys.argv[3])
    if output.exists():
        raise FileExistsError(f"refusing existing output directory: {output}")
    output.mkdir(parents=False, mode=0o700)
    expected = read_manifest(manifest)
    seen: set[str] = set()

    with tarfile.open(archive, mode="r:gz") as bundle:
        for member in bundle:
            name = pathlib.PurePosixPath(member.name).name
            if name not in expected:
                continue
            if name in seen or not member.isfile():
                raise ValueError(f"duplicate or non-regular required member: {name}")
            source = bundle.extractfile(member)
            if source is None:
                raise ValueError(f"could not read required member: {name}")
            target = output / name
            digest = hashlib.sha256()
            with source, target.open("xb") as sink:
                while chunk := source.read(8 * 1024 * 1024):
                    digest.update(chunk)
                    sink.write(chunk)
                sink.flush()
            if digest.hexdigest() != expected[name]:
                raise ValueError(f"SHA-256 mismatch for required member: {name}")
            target.chmod(0o600)
            seen.add(name)

    missing = sorted(set(expected) - seen)
    if missing:
        raise ValueError(f"circuit archive omitted required members: {missing}")
    (output / ".complete").write_bytes(b"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
