# -*- coding: utf-8 -*-
"""Decode a 32-bit little-endian pointer table without executing anything.

This module is deliberately narrow.  It imports only ``struct``, never
touches the filesystem, knows nothing about PE images, and contains no
game-specific data.  It simply turns raw table bytes plus the virtual
address the table lives at plus a set of executable virtual-address ranges
into one plain descriptor record per 4-byte slot.

Guarantees:

* ``data`` must be a real ``bytes`` object whose length is a multiple of 4.
* ``table_va`` must be a plain (non-``bool``) ``int`` in ``0..2**32-1``,
  4-byte aligned, with ``table_va + len(data) <= 2**32``.
* ``executable_ranges`` must be a finite ``list``/``tuple`` of ``(lo, hi)``
  pairs; every ``lo``/``hi`` must be a plain (non-``bool``) ``int`` with
  ``0 <= lo < hi <= 2**32``.
* Every slot is reported, in input order -- nulls, duplicates and values
  that fall outside every range are all preserved.  Nothing is filtered,
  reordered, collapsed, dereferenced, or executed.

Illegal arguments raise ``TypeError`` (wrong kind of object) or
``ValueError`` (right kind, impossible value).  A zero-length table yields
an empty list.
"""

import struct

__all__ = ["decode_pointer_table32"]

_U32_MAX = 0xFFFFFFFF
_U32_MOD = 0x100000000
_SLOT_SIZE = 4


def _is_plain_int(value):
    """True only for real ``int`` values; ``bool`` is rejected on purpose."""
    return type(value) is int


def _validate_table_va(table_va, data_len):
    """Validate the base address of the table; return it unchanged."""
    if not _is_plain_int(table_va):
        raise TypeError(
            "table_va must be a plain int (bool is not accepted), got %s"
            % type(table_va).__name__
        )
    if table_va < 0 or table_va > _U32_MAX:
        raise ValueError(
            "table_va must satisfy 0 <= table_va <= 0xFFFFFFFF, got %d" % table_va
        )
    if table_va % _SLOT_SIZE:
        raise ValueError("table_va must be 4-byte aligned, got 0x%08X" % table_va)
    end = table_va + data_len
    if end > _U32_MOD:
        raise ValueError(
            "table_va + len(data) must not exceed 2**32, got %d" % end
        )
    return table_va


def _validate_ranges(executable_ranges):
    """Validate the executable ranges and return a list of ``(lo, hi)`` tuples."""
    if not isinstance(executable_ranges, (list, tuple)):
        raise TypeError(
            "executable_ranges must be a list or tuple of (lo, hi) pairs, got %s"
            % type(executable_ranges).__name__
        )

    normalized = []
    for index, pair in enumerate(executable_ranges):
        if not isinstance(pair, (list, tuple)):
            raise TypeError(
                "executable_ranges[%d] must be a (lo, hi) pair, got %s"
                % (index, type(pair).__name__)
            )
        if len(pair) != 2:
            raise TypeError(
                "executable_ranges[%d] must contain exactly 2 items, got %d"
                % (index, len(pair))
            )

        lo, hi = pair
        if not _is_plain_int(lo):
            raise TypeError(
                "executable_ranges[%d][0] (lo) must be a plain int, got %s"
                % (index, type(lo).__name__)
            )
        if not _is_plain_int(hi):
            raise TypeError(
                "executable_ranges[%d][1] (hi) must be a plain int, got %s"
                % (index, type(hi).__name__)
            )
        if not (0 <= lo <= _U32_MAX):
            raise ValueError(
                "executable_ranges[%d][0] (lo) must satisfy 0 <= lo <= 0xFFFFFFFF, got %d"
                % (index, lo)
            )
        if not (0 <= hi <= _U32_MOD):
            raise ValueError(
                "executable_ranges[%d][1] (hi) must satisfy 0 <= hi <= 2**32, got %d"
                % (index, hi)
            )
        if lo >= hi:
            raise ValueError(
                "executable_ranges[%d] must satisfy lo < hi, got (%d, %d)"
                % (index, lo, hi)
            )

        normalized.append((lo, hi))

    return normalized


def decode_pointer_table32(data, table_va, executable_ranges):
    """Describe every 4-byte slot of a 32-bit little-endian pointer table.

    :param data: raw table bytes; length must be a multiple of 4.
    :param table_va: virtual address of the first slot (u32, 4-byte aligned).
    :param executable_ranges: finite list/tuple of ``(lo, hi)`` pairs marking
        executable virtual-address windows; each pair is half-open, ``lo``
        inclusive and ``hi`` exclusive.
    :returns: a list of ``dict`` records, one per slot, in slot order::

            {
                "slot": table_va + 4 * i,
                "value": <u32 read from bytes 4*i .. 4*i+3>,
                "is_null": value == 0,
                "is_executable": value != 0 and lo <= value < hi for some range,
            }

    The returned list is a fresh, caller-owned object graph; the function
    keeps no state, performs no I/O, and never dereferences a pointer.
    """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes, got %s" % type(data).__name__)

    data_len = len(data)
    if data_len % _SLOT_SIZE:
        raise ValueError(
            "len(data) must be a multiple of 4, got %d" % data_len
        )

    _validate_table_va(table_va, data_len)
    ranges = _validate_ranges(executable_ranges)

    slot_count = data_len // _SLOT_SIZE
    if slot_count == 0:
        return []

    values = struct.unpack("<%dI" % slot_count, data)

    records = []
    append = records.append
    slot = table_va

    for value in values:
        is_null = value == 0
        is_executable = False
        if not is_null:
            for lo, hi in ranges:
                if lo <= value < hi:
                    is_executable = True
                    break

        append(
            {
                "slot": slot,
                "value": value,
                "is_null": is_null,
                "is_executable": is_executable,
            }
        )
        slot += _SLOT_SIZE

    return records
