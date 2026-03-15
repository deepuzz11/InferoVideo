def seconds_to_hms(seconds: float) -> str:
    total = int(max(0, seconds))
    h, r = divmod(total, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def seconds_to_vtt(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    total = int(seconds)
    h, r = divmod(total, 3600)
    m, s = divmod(r, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def seconds_to_srt(seconds: float) -> str:
    return seconds_to_vtt(seconds).replace(".", ",")
