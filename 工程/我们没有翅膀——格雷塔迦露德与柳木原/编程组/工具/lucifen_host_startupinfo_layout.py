"""Windows host STARTUPINFOA byte layouts for editor-easy ISSUE-20261011-02.

These constants describe 32-bit and 64-bit host STARTUPINFOA buffer metadata.
Callers validate buffer capacity, guard bytes, copy strings, and map borrowed
handles; the guest startup structure remains 68 bytes. Callers must reject
pointer widths other than 4 or 8.
"""

STARTUPINFOA_LAYOUT_32 = {'size': 68, 'pointer_format': '<I', 'reserved_length_offset': 50, 'reserved_pointer_offset': 52, 'string_offsets': (4, 8, 12), 'scalar_offset': 16, 'word_offset': 48, 'standard_handle_offsets': (56, 60, 64)}
STARTUPINFOA_LAYOUT_64 = {'size': 104, 'pointer_format': '<Q', 'reserved_length_offset': 66, 'reserved_pointer_offset': 72, 'string_offsets': (8, 16, 24), 'scalar_offset': 32, 'word_offset': 64, 'standard_handle_offsets': (80, 88, 96)}
