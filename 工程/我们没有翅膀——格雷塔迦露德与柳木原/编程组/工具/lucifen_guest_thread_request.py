import struct

SIX_DWORD_LAYOUT = '<6I'
CREATE_THREAD_REQUEST_SIZE = struct.calcsize(SIX_DWORD_LAYOUT)


def decode_create_thread_request(data):
    security_attributes, stack_size, start_address, parameter, creation_flags, thread_id_out = struct.unpack(
        SIX_DWORD_LAYOUT, data
    )
    return {
        'security_attributes': security_attributes,
        'stack_size': stack_size,
        'start_address': start_address,
        'parameter': parameter,
        'creation_flags': creation_flags,
        'thread_id_out': thread_id_out,
    }
