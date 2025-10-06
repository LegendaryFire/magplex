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

    def get_name(self):
        if self.value == EncoderMap.REMUX:
            logging.error("Encoder name does not exist when remuxing.")
        return self.value[0]


    def get_preset(self):
        if self.value == EncoderMap.REMUX:
            logging.error("Encoder preset does not exist when remuxing.")
        return self.value[1]


def get_encoder():
    if Variables.BASE_CODEC:
        if EncoderMap.HEVC_NVIDIA.get_name() == Variables.BASE_CODEC:
            return EncoderMap.HEVC_NVIDIA
        elif EncoderMap.HEVC_INTEL.get_name() == Variables.BASE_CODEC:
            return EncoderMap.HEVC_INTEL
        elif EncoderMap.HEVC_AMD.get_name() == Variables.BASE_CODEC:
            return EncoderMap.HEVC_AMD
        elif EncoderMap.HEVC_SOFTWARE.get_name() == Variables.BASE_CODEC:
            return EncoderMap.HEVC_SOFTWARE
        else:
            logging.warning("Unable to find supported codec. Falling back to remuxing.")
    return EncoderMap.REMUX


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