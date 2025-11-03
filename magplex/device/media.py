import io
import logging
import threading
from enum import Enum

import ffmpeg

from magplex.utilities.variables import Environment


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
    if Environment.BASE_CODEC:
        if EncoderMap.HEVC_NVIDIA.get_name() == Environment.BASE_CODEC:
            return EncoderMap.HEVC_NVIDIA
        elif EncoderMap.HEVC_INTEL.get_name() == Environment.BASE_CODEC:
            return EncoderMap.HEVC_INTEL
        elif EncoderMap.HEVC_AMD.get_name() == Environment.BASE_CODEC:
            return EncoderMap.HEVC_AMD
        elif EncoderMap.HEVC_SOFTWARE.get_name() == Environment.BASE_CODEC:
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
        rw_timeout=60 * 10**6,  # 60 seconds, in microseconds.
        reconnect_streamed=1,
        reconnect_on_network_error=1,
        headers = headers
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

    proc = process.run_async(
        cmd=Environment.BASE_FFMPEG,
        pipe_stdout=True,
        pipe_stderr=True
    )

    # Monitor FFMPEG logs if debugging is enabled.
    logger = logging.getLogger()
    def log_output(pipe):
        for line in iter(pipe.readline, b''):
            text = line.decode(errors="ignore").rstrip()  # Must consume error to drain piped output.
            if Environment.DEBUG:
                if "error" in text.lower():
                    logger.error(text)
                elif "warning" in text.lower():
                    logger.warning(text)
                else:
                    logger.debug(text)

        threading.Thread(target=log_output, args=(proc.stderr,), daemon=True).start()

    return proc