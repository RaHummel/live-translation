#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,too-few-public-methods
#

"""
CTypes mapping between libopus functions and Python.
"""

import array
import ctypes  # type: ignore
import typing

import opuslib
import opuslib.api

__author__ = 'Chris Hold>'
__copyright__ = 'Copyright (c) 2024, Chris Hold'
__license__ = 'BSD 3-Clause License'


class MultiStreamDecoder(ctypes.Structure):
    """Opus multi-stream decoder state.
    This contains the complete state of an Opus decoder.
    """
    pass


MultiStreamDecoderPointer = ctypes.POINTER(MultiStreamDecoder)


libopus_get_size = opuslib.api.libopus.opus_multistream_decoder_get_size
libopus_get_size.argtypes = (ctypes.c_int, ctypes.c_int)
libopus_get_size.restype = ctypes.c_int
libopus_get_size.__doc__ = 'Gets the size of an OpusMSEncoder structure'


libopus_create = opuslib.api.libopus.opus_multistream_decoder_create
libopus_create.argtypes = (
    ctypes.c_int,  # fs
    ctypes.c_int,  # channels
    ctypes.c_int,  # streams
    ctypes.c_int,  # coupled streams
    opuslib.api.c_ubyte_pointer,  # mapping
    opuslib.api.c_int_pointer  # error
)
libopus_create.restype = MultiStreamDecoderPointer


def create_state(fs: int, channels: int, streams: int, coupled_streams: int,
                 mapping: list) -> ctypes.Structure:
    """
    Allocates and initializes a decoder state.
    Wrapper for C opus_decoder_create()

    `fs` must be one of 8000, 12000, 16000, 24000, or 48000.

    Internally Opus stores data at 48000 Hz, so that should be the default
    value for Fs. However, the decoder can efficiently decode to buffers
    at 8, 12, 16, and 24 kHz so if for some reason the caller cannot use data
    at the full sample rate, or knows the compressed data doesn't use the full
    frequency range, it can request decoding at a reduced rate. Likewise, the
    decoder is capable of filling in either mono or interleaved stereo pcm
    buffers, at the caller's request.

    :param fs: Sample rate to decode at (Hz).
    """
    result_code = ctypes.c_int()
    _umapping = (ctypes.c_ubyte * len(mapping))(*mapping)

    decoder_state = libopus_create(
        fs,
        channels,
        streams,
        coupled_streams,
        _umapping,
        ctypes.byref(result_code)
    )

    if result_code.value != opuslib.OK:
        raise opuslib.exceptions.OpusError(result_code.value)

    return decoder_state


libopus_decode = opuslib.api.libopus.opus_multistream_decode
libopus_decode.argtypes = (
    MultiStreamDecoderPointer,
    ctypes.c_char_p,
    ctypes.c_int32,
    opuslib.api.c_int16_pointer,
    ctypes.c_int,
    ctypes.c_int
)
libopus_decode.restype = ctypes.c_int


# FIXME: Remove typing.Any once we have a stub for ctypes
def decode(  # pylint: disable=too-many-arguments
        decoder_state: ctypes.Structure,
        opus_data: bytes,
        length: int,
        frame_size: int,
        decode_fec: bool,
        channels: int = 2
) -> typing.Union[bytes, typing.Any]:
    """
    Decode an Opus Frame to PCM.

    Unlike the `opus_decode` function , this function takes an additional
    parameter `channels`, which indicates the number of channels in the frame.
    """
    _decode_fec = int(decode_fec)
    result = 0

    pcm_size = frame_size * channels * ctypes.sizeof(ctypes.c_int16)
    pcm = (ctypes.c_int16 * pcm_size)()
    pcm_pointer = ctypes.cast(pcm, opuslib.api.c_int16_pointer)

    result = libopus_decode(
        decoder_state,
        opus_data,
        length,
        pcm_pointer,
        frame_size,
        _decode_fec
    )

    if result < 0:
        raise opuslib.exceptions.OpusError(result)

    return array.array('h', pcm_pointer[:result * channels]).tobytes()


libopus_decode_float = opuslib.api.libopus.opus_multistream_decode_float
libopus_decode_float.argtypes = (
    MultiStreamDecoderPointer,
    ctypes.c_char_p,
    ctypes.c_int32,
    opuslib.api.c_float_pointer,
    ctypes.c_int,
    ctypes.c_int
)
libopus_decode_float.restype = ctypes.c_int


# FIXME: Remove typing.Any once we have a stub for ctypes
def decode_float(  # pylint: disable=too-many-arguments
        decoder_state: ctypes.Structure,
        opus_data: bytes,
        length: int,
        frame_size: int,
        decode_fec: bool,
        channels: int = 2
) -> typing.Union[bytes, typing.Any]:
    """
    Decode an Opus Frame.

    Unlike the `opus_decode` function , this function takes an additional
    parameter `channels`, which indicates the number of channels in the frame.
    """
    _decode_fec = int(decode_fec)

    pcm_size = frame_size * channels * ctypes.sizeof(ctypes.c_float)
    pcm = (ctypes.c_float * pcm_size)()
    pcm_pointer = ctypes.cast(pcm, opuslib.api.c_float_pointer)

    result = libopus_decode_float(
        decoder_state,
        opus_data,
        length,
        pcm_pointer,
        frame_size,
        _decode_fec
    )

    if result < 0:
        raise opuslib.exceptions.OpusError(result)

    return array.array('f', pcm[:result * channels]).tobytes()


libopus_ctl = opuslib.api.libopus.opus_multistream_decoder_ctl
libopus_ctl.argtypes = [MultiStreamDecoderPointer, ctypes.c_int,]  # variadic
libopus_ctl.restype = ctypes.c_int


# FIXME: Remove typing.Any once we have a stub for ctypes
def decoder_ctl(
        decoder_state: ctypes.Structure,
        request,
        value=None
) -> typing.Union[int, typing.Any]:
    if value is not None:
        return request(libopus_ctl, decoder_state, value)
    return request(libopus_ctl, decoder_state)


destroy = opuslib.api.libopus.opus_multistream_decoder_destroy
destroy.argtypes = (MultiStreamDecoderPointer,)
destroy.restype = None
destroy.__doc__ = 'Frees an OpusMultistreamDecoder allocated by opus_multistream_decoder_create()'
