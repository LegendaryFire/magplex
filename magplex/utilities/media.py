import logging
import subprocess
from enum import Enum

import ffmpeg

from magplex.utilities.environment import Variables


class EncoderMap(Enum):
    HEVC_NVIDIA = ('hevc_nvenc', 'llhq')
    HEVC_INTEL = ('hevc_qsv', 'veryfast')
    HEVC_AMD = ('hevc_amf', 'fast')
    HEVC_SOFTWARE = ('libx265', 'ultrafast')
    REMUX = None

    @classmethod
    def find_encoder(cls, encoders):
        if Variables.BASE_ENCODE:
            if EncoderMap.HEVC_NVIDIA.get_name() in encoders:
                return EncoderMap.HEVC_NVIDIA  # NVIDIA NVENC
            elif EncoderMap.HEVC_INTEL.get_name() in encoders:
                return EncoderMap.HEVC_INTEL  # Intel Quick Sync
            elif EncoderMap.HEVC_AMD.get_name() in encoders:
                return EncoderMap.HEVC_AMD  # AMD Advanced Media Framework
            elif EncoderMap.HEVC_SOFTWARE.get_name() in encoders:
                logging.warning("No hardware encoder found, falling back to software encoder.")
                return EncoderMap.HEVC_SOFTWARE  # CPU Software Encoding
            else:
                logging.warning("No available H265 encoders, stream will not be encoded.")
        return EncoderMap.REMUX


    def get_name(self):
        if self.value == EncoderMap.REMUX:
            logging.error("Encoder name does not exist when remuxing.")
        return self.value[0]


    def get_preset(self):
        if self.value == EncoderMap.REMUX:
            logging.error("Encoder preset does not exist when remuxing.")
        return self.value[1]


def get_encoder():
    encoders = subprocess.run([Variables.BASE_FFMPEG, "-encoders"], capture_output=True, text=True).stdout
    return EncoderMap.find_encoder(encoders)


def create_stream_response(url, encoder, headers):
    process = ffmpeg.input(
        url,
        re=None,
        allowed_extensions='ALL',
        http_persistent=1,
        flags='low_delay',
        headers=headers
    )

    if encoder == EncoderMap.REMUX:
        process = process.output(
            'pipe:1',
            format='mpegts',
            codec='copy',
            headers=headers
        )
    else:
        process = process.output(
            'pipe:1',
            format='mpegts',
            vcodec=encoder.get_name(),
            preset=encoder.get_preset(),
            g=50,
            acodec='aac',
            audio_bitrate='128k'
        )
    return process.run_async(cmd=Variables.BASE_FFMPEG, pipe_stdout=True, pipe_stderr=False)