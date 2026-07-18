"""
Shared utility: generate a minimal valid ISO Base Media File (MP4) entirely in
pure Python — no external dependencies required.

Used by:
  - MockAnimationProvider (Phase 7)  — real bytes returned to caller / uploaded to MinIO
  - VideoAssemblyService (Phase 10)  — mock-assemble fallback path

Having one authoritative implementation avoids the "8-byte ftyp stub" problem
where a caller wrote the box header but skipped the moov/mdat boxes required to
make a container parseable by FFmpeg or any video player.
"""
from __future__ import annotations

import struct


def make_minimal_mp4_stub() -> bytes:
    """
    Build the smallest valid ISO Base Media File entirely in pure Python.

    Structure:
      ftyp box — file-type declaration  (isom brand)
      moov box — movie header + single video track (1×1, 1 second, no samples)
      mdat box — empty media data

    The resulting file is several hundred bytes — enough to:
      - Pass basic MP4 container validation (ftyp + moov present)
      - Declare a 1-second duration so quality-gate duration checks don't break
      - Be clearly distinguishable from the old 8-byte placeholder stub
        (file_size_bytes will be > 400 bytes after this call)
    """

    def _box(name: bytes, *children: bytes) -> bytes:
        data = b"".join(children)
        return struct.pack(">I", len(data) + 8) + name + data

    # ------------------------------------------------------------------
    # ftyp — file type
    # ------------------------------------------------------------------
    ftyp = _box(
        b"ftyp",
        b"isom",               # major brand
        b"\x00\x00\x02\x00",  # minor version
        b"isom", b"iso2", b"mp41",
    )

    # ------------------------------------------------------------------
    # moov — movie container
    # ------------------------------------------------------------------
    timescale = 1000
    duration_ms = 1000  # 1 second

    mvhd_data = (
        b"\x00\x00\x00\x00"          # creation time
        b"\x00\x00\x00\x00"          # modification time
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration_ms)
        + b"\x00\x01\x00\x00"        # rate = 1.0
        + b"\x01\x00"                 # volume = 1.0
        + b"\x00" * 10               # reserved
        + b"\x00\x01\x00\x00" + b"\x00" * 12
        + b"\x00\x01\x00\x00" + b"\x00" * 12
        + b"\x40\x00\x00\x00"        # unity matrix
        + b"\x00" * 24               # pre-defined
        + b"\x00\x00\x00\x02"        # next track id
    )
    mvhd = _box(b"mvhd", struct.pack(">I", 0), mvhd_data)

    tkhd_data = (
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00"
        + struct.pack(">I", 1)       # track id = 1
        + b"\x00\x00\x00\x00"       # reserved
        + struct.pack(">I", duration_ms)
        + b"\x00" * 8
        + b"\x00\x00"               # layer
        + b"\x00\x00"               # alternate group
        + b"\x00\x00"               # volume
        + b"\x00\x00"               # reserved
        + b"\x00\x01\x00\x00" + b"\x00" * 12
        + b"\x00\x01\x00\x00" + b"\x00" * 12
        + b"\x40\x00\x00\x00"       # unity matrix
        + struct.pack(">I", 1)      # width  (16.16 fixed-point → 1 pixel)
        + struct.pack(">I", 1)      # height (16.16 fixed-point → 1 pixel)
    )
    tkhd = _box(b"tkhd", struct.pack(">I", 3), tkhd_data)

    mdhd_data = (
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00"
        + struct.pack(">I", timescale)
        + struct.pack(">I", duration_ms)
        + b"\x55\xc4"               # language tag "und"
        + b"\x00\x00"
    )
    mdhd = _box(b"mdhd", struct.pack(">I", 0), mdhd_data)

    hdlr_data = (
        b"\x00\x00\x00\x00"         # pre-defined
        b"vide"                      # handler type: video
        + b"\x00" * 12
        + b"VideoHandler\x00"
    )
    hdlr = _box(b"hdlr", struct.pack(">I", 0), hdlr_data)

    vmhd = _box(b"vmhd", b"\x00\x00\x00\x01", b"\x00" * 8)

    url  = _box(b"url ", struct.pack(">I", 1))          # self-contained flag
    dref = _box(b"dref", struct.pack(">I", 0), struct.pack(">I", 1), url)
    dinf = _box(b"dinf", dref)

    stsd = _box(b"stsd", struct.pack(">I", 0), struct.pack(">I", 0))
    stts = _box(b"stts", struct.pack(">I", 0), struct.pack(">I", 0))
    stsc = _box(b"stsc", struct.pack(">I", 0), struct.pack(">I", 0))
    stsz = _box(b"stsz", struct.pack(">I", 0), struct.pack(">I", 0), struct.pack(">I", 0))
    stco = _box(b"stco", struct.pack(">I", 0), struct.pack(">I", 0))

    stbl = _box(b"stbl", stsd, stts, stsc, stsz, stco)
    minf = _box(b"minf", vmhd, dinf, stbl)
    mdia = _box(b"mdia", mdhd, hdlr, minf)
    trak = _box(b"trak", tkhd, mdia)
    moov = _box(b"moov", mvhd, trak)

    # ------------------------------------------------------------------
    # mdat — empty media data section
    # ------------------------------------------------------------------
    mdat = _box(b"mdat")

    return ftyp + moov + mdat


# Module-level constant — generated once, reused everywhere.
MINIMAL_MP4_STUB: bytes = make_minimal_mp4_stub()
