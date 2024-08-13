#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""High-level interface to a Opus decoder functions"""

import typing

import opuslib
import opuslib.api
import opuslib.api.ctl
import opuslib.api.decoder
import opuslib.api.encoder
import opuslib.api.multistream_encoder
import opuslib.api.multistream_decoder
import opuslib.api.projection_encoder
import opuslib.api.projection_decoder


__author__ = 'Никита Кузнецов <self@svartalf.info>'
__copyright__ = 'Copyright (c) 2012, SvartalF'
__license__ = 'BSD 3-Clause License'


class Encoder(object):

    """High-Level Encoder Object."""

    def __init__(self, fs, channels, application) -> None:
        """
        Parameters:
            fs : sampling rate
            channels : number of channels
        """
        # Check to see if the Encoder Application Macro is available:
        if application in list(opuslib.APPLICATION_TYPES_MAP.keys()):
            application = opuslib.APPLICATION_TYPES_MAP[application]
        elif application in list(opuslib.APPLICATION_TYPES_MAP.values()):
            pass  # Nothing to do here
        else:
            raise ValueError(
                "`application` value must be in 'voip', 'audio' or "
                "'restricted_lowdelay'")

        self._fs = fs
        self._channels = channels
        self._application = application
        self.encoder_state = opuslib.api.encoder.create_state(
            fs, channels, application)

    def __del__(self) -> None:
        if hasattr(self, 'encoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.encoder.destroy(self.encoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.encoder.encoder_ctl(
            self.encoder_state, opuslib.api.ctl.reset_state)

    def encode(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.encoder.encode(
            self.encoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )

    def encode_float(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.encoder.encode_float(
            self.encoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )

    # CTL interfaces

    def _get_final_range(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state,
        opuslib.api.ctl.get_final_range
    )

    final_range = property(_get_final_range)

    def _get_bandwidth(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_bandwidth)

    bandwidth = property(_get_bandwidth)

    def _get_pitch(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_pitch)

    pitch = property(_get_pitch)

    def _get_lsb_depth(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_lsb_depth)

    def _set_lsb_depth(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_lsb_depth, x)

    lsb_depth = property(_get_lsb_depth, _set_lsb_depth)

    def _get_complexity(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_complexity)

    def _set_complexity(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_complexity, x)

    complexity = property(_get_complexity, _set_complexity)

    def _get_bitrate(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_bitrate)

    def _set_bitrate(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_bitrate, x)

    bitrate = property(_get_bitrate, _set_bitrate)

    def _get_vbr(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_vbr)

    def _set_vbr(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_vbr, x)

    vbr = property(_get_vbr, _set_vbr)

    def _get_vbr_constraint(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_vbr_constraint)

    def _set_vbr_constraint(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_vbr_constraint, x)

    vbr_constraint = property(_get_vbr_constraint, _set_vbr_constraint)

    def _get_force_channels(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_force_channels)

    def _set_force_channels(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_force_channels, x)

    force_channels = property(_get_force_channels, _set_force_channels)

    def _get_max_bandwidth(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_max_bandwidth)

    def _set_max_bandwidth(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_max_bandwidth, x)

    max_bandwidth = property(_get_max_bandwidth, _set_max_bandwidth)

    def _set_bandwidth(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_bandwidth, x)

    bandwidth = property(None, _set_bandwidth)

    def _get_signal(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_signal)

    def _set_signal(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_signal, x)

    signal = property(_get_signal, _set_signal)

    def _get_application(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_application)

    def _set_application(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_application, x)

    application = property(_get_application, _set_application)

    def _get_sample_rate(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_sample_rate)

    sample_rate = property(_get_sample_rate)

    def _get_lookahead(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_lookahead)

    lookahead = property(_get_lookahead)

    def _get_inband_fec(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_inband_fec)

    def _set_inband_fec(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_inband_fec, x)

    inband_fec = property(_get_inband_fec, _set_inband_fec)

    def _get_packet_loss_perc(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_packet_loss_perc)

    def _set_packet_loss_perc(self, x): return opuslib.api.encoder.encoder_ctl(
            self.encoder_state, opuslib.api.ctl.set_packet_loss_perc, x)

    packet_loss_perc = property(_get_packet_loss_perc, _set_packet_loss_perc)

    def _get_dtx(self): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.get_dtx)

    def _set_dtx(self, x): return opuslib.api.encoder.encoder_ctl(
        self.encoder_state, opuslib.api.ctl.set_dtx, x)

    dtx = property(_get_dtx, _set_dtx)


class Decoder(object):

    """High-Level Decoder Object."""

    def __init__(self, fs: int, channels: int) -> None:
        """
        :param fs: Sample Rate.
        :param channels: Number of channels.
        """
        self._fs = fs
        self._channels = channels
        self.decoder_state = opuslib.api.decoder.create_state(fs, channels)

    def __del__(self) -> None:
        if hasattr(self, 'decoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.decoder.destroy(self.decoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.decoder.decoder_ctl(
            self.decoder_state,
            opuslib.api.ctl.reset_state
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.decoder.decode(
            self.decoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode_float(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.decoder.decode_float(
            self.decoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

    # CTL interfaces

    def _get_final_range(self): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.get_final_range
    )

    final_range = property(_get_final_range)

    def _get_bandwidth(self): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.get_bandwidth
    )

    bandwidth = property(_get_bandwidth)

    def _get_pitch(self): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.get_pitch
    )

    pitch = property(_get_pitch)

    def _get_lsb_depth(self): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.get_lsb_depth
    )

    def _set_lsb_depth(self, x): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.set_lsb_depth,
        x
    )

    lsb_depth = property(_get_lsb_depth, _set_lsb_depth)

    def _get_gain(self): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.get_gain
    )

    def _set_gain(self, x): return opuslib.api.decoder.decoder_ctl(
        self.decoder_state,
        opuslib.api.ctl.set_gain,
        x
    )

    gain = property(_get_gain, _set_gain)


class MultiStreamEncoder(object):
    """High-Level MultiStreamEncoder Object."""

    def __init__(self, fs: int, channels: int, streams: int,
                 coupled_streams: int, mapping: list,
                 application: int) -> None:
        """
        Parameters:
            fs : sampling rate
            channels : number of channels
        """
        # Check to see if the Encoder Application Macro is available:
        if application in list(opuslib.APPLICATION_TYPES_MAP.keys()):
            application = opuslib.APPLICATION_TYPES_MAP[application]
        elif application in list(opuslib.APPLICATION_TYPES_MAP.values()):
            pass  # Nothing to do here
        else:
            raise ValueError(
                "`application` value must be in 'voip', 'audio' or "
                "'restricted_lowdelay'")

        self._fs = fs
        self._channels = channels
        self._streams = streams
        self._coupled_streams = coupled_streams
        self._mapping = mapping
        self._application = application
        self.msencoder_state = opuslib.api.multistream_encoder.create_state(
            self._fs, self._channels, self._streams, self._coupled_streams,
            self._mapping, self._application)

    def __del__(self) -> None:
        if hasattr(self, 'msencoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.multistream_encoder.destroy(self.msencoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.multistream_encoder.encoder_ctl(
            self.msencoder_state, opuslib.api.ctl.reset_state)

    def encode(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.multistream_encoder.encode(
            self.msencoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )

    def encode_float(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.multistream_encoder.encode_float(
            self.msencoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )

    # CTL interfaces

    def _get_final_range(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state,
        opuslib.api.ctl.get_final_range
    )

    final_range = property(_get_final_range)

    def _get_bandwidth(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_bandwidth)

    bandwidth = property(_get_bandwidth)

    def _get_pitch(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_pitch)

    pitch = property(_get_pitch)

    def _get_lsb_depth(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_lsb_depth)

    def _set_lsb_depth(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_lsb_depth, x)

    lsb_depth = property(_get_lsb_depth, _set_lsb_depth)

    def _get_complexity(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_complexity)

    def _set_complexity(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_complexity, x)

    complexity = property(_get_complexity, _set_complexity)

    def _get_bitrate(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_bitrate)

    def _set_bitrate(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_bitrate, x)

    bitrate = property(_get_bitrate, _set_bitrate)

    def _get_vbr(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_vbr)

    def _set_vbr(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_vbr, x)

    vbr = property(_get_vbr, _set_vbr)

    def _get_vbr_constraint(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_vbr_constraint)

    def _set_vbr_constraint(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_vbr_constraint, x)

    vbr_constraint = property(_get_vbr_constraint, _set_vbr_constraint)

    def _get_force_channels(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_force_channels)

    def _set_force_channels(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_force_channels, x)

    force_channels = property(_get_force_channels, _set_force_channels)

    def _get_max_bandwidth(self): return \
        opuslib.api.encoder.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_max_bandwidth)

    def _set_max_bandwidth(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_max_bandwidth, x)

    max_bandwidth = property(_get_max_bandwidth, _set_max_bandwidth)

    def _set_bandwidth(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_bandwidth, x)

    bandwidth = property(None, _set_bandwidth)

    def _get_signal(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_signal)

    def _set_signal(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_signal, x)

    signal = property(_get_signal, _set_signal)

    def _get_application(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_application)

    def _set_application(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_application, x)

    application = property(_get_application, _set_application)

    def _get_sample_rate(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_sample_rate)

    sample_rate = property(_get_sample_rate)

    def _get_lookahead(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_lookahead)

    lookahead = property(_get_lookahead)

    def _get_inband_fec(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_inband_fec)

    def _set_inband_fec(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_inband_fec, x)

    inband_fec = property(_get_inband_fec, _set_inband_fec)

    def _get_packet_loss_perc(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_packet_loss_perc)

    def _set_packet_loss_perc(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_packet_loss_perc, x)

    packet_loss_perc = property(_get_packet_loss_perc, _set_packet_loss_perc)

    def _get_dtx(self): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.get_dtx)

    def _set_dtx(self, x): return \
        opuslib.api.multistream_encoder.encoder_ctl(
        self.msencoder_state, opuslib.api.ctl.set_dtx, x)

    dtx = property(_get_dtx, _set_dtx)


class MultiStreamDecoder(object):
    """High-Level MultiStreamDecoder Object."""

    def __init__(self, fs: int, channels: int, streams: int,
                 coupled_streams: int, mapping: list) -> None:
        """
        :param fs: Sample Rate.
        :param channels: Number of channels.
        """
        self._fs = fs
        self._channels = channels
        self._streams = streams
        self._coupled_streams = coupled_streams
        self._mapping = mapping
        self.msdecoder_state = opuslib.api.multistream_decoder.create_state(
            self._fs, self._channels, self._streams, self._coupled_streams,
            self._mapping)

    def __del__(self) -> None:
        if hasattr(self, 'msdecoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.multistream_decoder.destroy(self.msdecoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.multistream_decoder.decoder_ctl(
            self.msdecoder_state,
            opuslib.api.ctl.reset_state
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.multistream_decoder.decode(
            self.msdecoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode_float(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.multistream_decoder.decode_float(
            self.msdecoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

    # CTL interfaces

    def _get_final_range(self): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.get_final_range)

    final_range = property(_get_final_range)

    def _get_bandwidth(self): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.get_bandwidth)

    bandwidth = property(_get_bandwidth)

    def _get_pitch(self): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.get_pitch)

    pitch = property(_get_pitch)

    def _get_lsb_depth(self): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.get_lsb_depth)

    def _set_lsb_depth(self, x): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.set_lsb_depth, x)

    lsb_depth = property(_get_lsb_depth, _set_lsb_depth)

    def _get_gain(self): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.get_gain)

    def _set_gain(self, x): return \
        opuslib.api.multistream_decoder.decoder_ctl(
        self.msdecoder_state, opuslib.api.ctl.set_gain, x)

    gain = property(_get_gain, _set_gain)


class ProjectionEncoder(object):
    """High-Level ProjectionEncoder Object."""

    def __init__(self, fs: int, channels: int, mapping_family: int,
                 streams: int, coupled_streams: int, application: int) -> None:
        """
        Parameters:
            fs : sampling rate
            channels : number of channels
        """
        # Check to see if the Encoder Application Macro is available:
        if application in list(opuslib.APPLICATION_TYPES_MAP.keys()):
            application = opuslib.APPLICATION_TYPES_MAP[application]
        elif application in list(opuslib.APPLICATION_TYPES_MAP.values()):
            pass  # Nothing to do here
        else:
            raise ValueError(
                "`application` value must be in 'voip', 'audio' or "
                "'restricted_lowdelay'")

        self._fs = fs
        self._channels = channels
        self._mapping_family = mapping_family
        self._streams = streams
        self._coupled_streams = coupled_streams
        self._application = application
        self.projencoder_state = opuslib.api.projection_encoder.create_state(
            self._fs, self._channels, self._mapping_family, self._streams,
            self._coupled_streams, self._application)

    def __del__(self) -> None:
        if hasattr(self, 'projencoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.projection_encoder.destroy(self.projencoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.projection_encoder.encoder_ctl(
            self.projencoder_state, opuslib.api.ctl.reset_state)

    def encode(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.projection_encoder.encode(
            self.projencoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )

    def encode_float(self, pcm_data: bytes, frame_size: int) -> bytes:
        """
        Encodes given PCM data as Opus.
        """
        return opuslib.api.projection_encoder.encode_float(
            self.projencoder_state,
            pcm_data,
            frame_size,
            len(pcm_data)
        )


    # CTL interfaces

    def _get_final_range(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state,
        opuslib.api.ctl.get_final_range
    )

    final_range = property(_get_final_range)

    def _get_bandwidth(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_bandwidth)

    bandwidth = property(_get_bandwidth)

    def _get_pitch(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_pitch)

    pitch = property(_get_pitch)

    def _get_lsb_depth(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_lsb_depth)

    def _set_lsb_depth(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_lsb_depth, x)

    lsb_depth = property(_get_lsb_depth, _set_lsb_depth)

    def _get_complexity(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_complexity)

    def _set_complexity(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_complexity, x)

    complexity = property(_get_complexity, _set_complexity)

    def _get_bitrate(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_bitrate)

    def _set_bitrate(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_bitrate, x)

    bitrate = property(_get_bitrate, _set_bitrate)

    def _get_vbr(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_vbr)

    def _set_vbr(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_vbr, x)

    vbr = property(_get_vbr, _set_vbr)

    def _get_vbr_constraint(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_vbr_constraint)

    def _set_vbr_constraint(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_vbr_constraint, x)

    vbr_constraint = property(_get_vbr_constraint, _set_vbr_constraint)

    def _get_force_channels(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_force_channels)

    def _set_force_channels(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_force_channels, x)

    force_channels = property(_get_force_channels, _set_force_channels)

    def _get_max_bandwidth(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_max_bandwidth)

    def _set_max_bandwidth(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_max_bandwidth, x)

    max_bandwidth = property(_get_max_bandwidth, _set_max_bandwidth)

    def _set_bandwidth(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_bandwidth, x)

    bandwidth = property(None, _set_bandwidth)

    def _get_signal(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_signal)

    def _set_signal(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_signal, x)

    signal = property(_get_signal, _set_signal)

    def _get_application(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_application)

    def _set_application(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_application, x)

    application = property(_get_application, _set_application)

    def _get_sample_rate(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_sample_rate)

    sample_rate = property(_get_sample_rate)

    def _get_lookahead(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_lookahead)

    lookahead = property(_get_lookahead)

    def _get_inband_fec(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_inband_fec)

    def _set_inband_fec(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_inband_fec, x)

    inband_fec = property(_get_inband_fec, _set_inband_fec)

    def _get_packet_loss_perc(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_packet_loss_perc)

    def _set_packet_loss_perc(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_packet_loss_perc, x)

    packet_loss_perc = property(_get_packet_loss_perc, _set_packet_loss_perc)

    def _get_dtx(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_dtx)

    def _set_dtx(self, x): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.set_dtx, x)

    dtx = property(_get_dtx, _set_dtx)

    def _get_demixing_matrix_size(self): return \
        opuslib.api.projection_encoder.encoder_ctl(
        self.projencoder_state, opuslib.api.ctl.get_demixing_matrix_size)

    demixing_matrix_size = property(_get_demixing_matrix_size)

    def get_demixing_matrix(self, matrix_size): return \
        opuslib.api.projection_encoder.get_demixing_matrix(
        self.projencoder_state, matrix_size)


class ProjectionDecoder(object):
    """High-Level ProjectionDecoder Object."""

    def __init__(self, fs: int, channels: int, streams: int,
                 coupled_streams: int, demixing_matrix: list) -> None:
        """
        :param fs: Sample Rate.
        :param channels: Number of channels.
        """
        self._fs = fs
        self._channels = channels
        self._streams = streams
        self._coupled_streams = coupled_streams
        self._demixing_matrix = demixing_matrix
        self.projdecoder_state = opuslib.api.projection_decoder.create_state(
            self._fs, self._channels, self._streams, self._coupled_streams,
            self._demixing_matrix)

    def __del__(self) -> None:
        if hasattr(self, 'projdecoder_state'):
            # Destroying state only if __init__ completed successfully
            opuslib.api.projection_decoder.destroy(self.projdecoder_state)

    def reset_state(self) -> None:
        """
        Resets the codec state to be equivalent to a freshly initialized state
        """
        opuslib.api.projection_decoder.decoder_ctl(
            self.projdecoder_state,
            opuslib.api.ctl.reset_state
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.projection_decoder.decode(
            self.projdecoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

    # FIXME: Remove typing.Any once we have a stub for ctypes
    def decode_float(
        self,
        opus_data: bytes,
        frame_size: int,
        decode_fec: bool = False
    ) -> typing.Union[bytes, typing.Any]:
        """
        Decodes given Opus data to PCM.
        """
        return opuslib.api.projection_decoder.decode_float(
            self.projdecoder_state,
            opus_data,
            len(opus_data),
            frame_size,
            decode_fec,
            channels=self._channels
        )

