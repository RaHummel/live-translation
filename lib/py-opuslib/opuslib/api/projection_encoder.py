#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=invalid-name
#

"""
CTypes mapping between libopus functions and Python.
"""

import array
import ctypes  # type: ignore
import typing

import opuslib
import opuslib.api

__author__ = 'Chris Hold'
__copyright__ = 'Copyright (c) 2024, Chris Hold'
__license__ = 'BSD 3-Clause License'


class ProjectionEncoder(ctypes.Structure):  # pylint: disable=too-few-public-methods
    """Opus projection encoder state.
    This contains the complete state of an Opus encoder.
    """
    pass


ProjectionEncoderPointer = ctypes.POINTER(ProjectionEncoder)


libopus_get_size = opuslib.api.libopus.opus_projection_ambisonics_encoder_get_size
libopus_get_size.argtypes = (ctypes.c_int, ctypes.c_int)
libopus_get_size.restype = ctypes.c_int


# FIXME: Remove typing.Any once we have a stub for ctypes
def get_size(channels: int, mapping_family: int) -> typing.Union[int, typing.Any]:
    """Gets the size of an ProjectionOpusEncoder structure."""
    return libopus_get_size(channels, mapping_family)


libopus_create = opuslib.api.libopus.opus_projection_ambisonics_encoder_create
libopus_create.argtypes = (
    ctypes.c_int,  # fs
    ctypes.c_int,  # channels
    ctypes.c_int,  # mapping_family
    opuslib.api.c_int_pointer,  # streams
    opuslib.api.c_int_pointer,  # coupled streams
    ctypes.c_int,  # application
    opuslib.api.c_int_pointer  # error
)
libopus_create.restype = ProjectionEncoderPointer


def create_state(fs: int, channels: int, mapping_family: int, streams: int,
                 coupled_streams: int, application: int) -> ctypes.Structure:
    """Allocates and initializes a projection encoder state."""
    result_code = ctypes.c_int()
    streams_ = ctypes.c_int(streams)
    coupled_streams_ = ctypes.c_int(coupled_streams)

    encoder_state = libopus_create(
        fs,
        channels,
        mapping_family,
        streams_,
        coupled_streams_,
        application,
        ctypes.byref(result_code)
    )

    if result_code.value != opuslib.OK:
        raise opuslib.OpusError(result_code.value)

    return encoder_state


libopus_projection_encode = opuslib.api.libopus.opus_projection_encode
libopus_projection_encode.argtypes = (
    ProjectionEncoderPointer,
    opuslib.api.c_int16_pointer,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int32
)
libopus_projection_encode.restype = ctypes.c_int32


# FIXME: Remove typing.Any once we have a stub for ctypes
def encode(
        encoder_state: ctypes.Structure,
        pcm_data: bytes,
        frame_size: int,
        max_data_bytes: int
) -> typing.Union[bytes, typing.Any]:
    """
    Encodes an Opus Frame.

    Returns string output payload.

    Parameters:
    [in]	st	OpusEncoder*: Encoder state
    [in]	pcm	opus_int16*: Input signal (interleaved if 2 channels). length
        is frame_size*channels*sizeof(opus_int16)
    [in]	frame_size	int: Number of samples per channel in the input signal.
        This must be an Opus frame size for the encoder's sampling rate. For
            example, at 48 kHz the permitted values are 120, 240, 480, 960,
            1920, and 2880. Passing in a duration of less than 10 ms
            (480 samples at 48 kHz) will prevent the encoder from using the
            LPC or hybrid modes.
    [out]	data	unsigned char*: Output payload. This must contain storage
        for at least max_data_bytes.
    [in]	max_data_bytes	opus_int32: Size of the allocated memory for the
        output payload. This may be used to impose an upper limit on the
        instant bitrate, but should not be used as the only bitrate control.
        Use OPUS_SET_BITRATE to control the bitrate.
    """
    pcm_pointer = ctypes.cast(pcm_data, opuslib.api.c_int16_pointer)
    opus_data = (ctypes.c_char * max_data_bytes)()

    result = libopus_projection_encode(
        encoder_state,
        pcm_pointer,
        frame_size,
        opus_data,
        max_data_bytes
    )

    if result < 0:
        raise opuslib.OpusError(
            'Opus Encoder returned result="{}"'.format(result))

    return array.array('b', opus_data[:result]).tobytes()


libopus_projection_encode_float = opuslib.api.libopus.opus_projection_encode_float
libopus_projection_encode_float.argtypes = (
    ProjectionEncoderPointer,
    opuslib.api.c_float_pointer,
    ctypes.c_int,
    ctypes.c_char_p,
    ctypes.c_int32
)
libopus_projection_encode_float.restype = ctypes.c_int32


# FIXME: Remove typing.Any once we have a stub for ctypes
def encode_float(
        encoder_state: ctypes.Structure,
        pcm_data: bytes,
        frame_size: int,
        max_data_bytes: int
) -> typing.Union[bytes, typing.Any]:
    """Encodes an Opus frame from floating point input"""
    pcm_pointer = ctypes.cast(pcm_data, opuslib.api.c_float_pointer)
    opus_data = (ctypes.c_char * max_data_bytes)()

    result = libopus_projection_encode_float(
        encoder_state,
        pcm_pointer,
        frame_size,
        opus_data,
        max_data_bytes
    )

    if result < 0:
        raise opuslib.OpusError(
            'Encoder returned result="{}"'.format(result))

    return array.array('b', opus_data[:result]).tobytes()


def get_demixing_matrix(
        encoder_state: ctypes.Structure,
        matrix_size
) -> typing.Union[int, typing.Any]:
    matrix = (ctypes.c_ubyte * matrix_size)()
    pmatrix = ctypes.cast(matrix, opuslib.api.c_ubyte_pointer)
    ret = libopus_ctl(
        encoder_state,
        opuslib.OPUS_PROJECTION_GET_DEMIXING_MATRIX_REQUEST,
        pmatrix,
        matrix_size)
    if ret != opuslib.OK:
        raise opuslib.OpusError(ret)
    return matrix


libopus_ctl = opuslib.api.libopus.opus_projection_encoder_ctl
libopus_ctl.argtypes = [ProjectionEncoderPointer, ctypes.c_int,]  # variadic
libopus_ctl.restype = ctypes.c_int


# FIXME: Remove typing.Any once we have a stub for ctypes
def encoder_ctl(
        encoder_state: ctypes.Structure,
        request,
        value=None
) -> typing.Union[int, typing.Any]:
    if value is not None:
        return request(libopus_ctl, encoder_state, value)
    return request(libopus_ctl, encoder_state)


destroy = opuslib.api.libopus.opus_projection_encoder_destroy
destroy.argtypes = (ProjectionEncoderPointer,)  # must be sequence (,) of types!
destroy.restype = None
destroy.__doc__ = "Frees an OpusEncoder allocated by opus_projection_encoder_create()"
