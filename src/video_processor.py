"""
Processeur video pour l'extraction audio et de frames depuis des fichiers video.

Utilise PyAV (bindings FFmpeg) pour demuxer les flux audio et video.
Le pipeline de transcription existant fonctionne sans modification :
on extrait l'audio en WAV, Whisper le traite normalement, et les
timecodes obtenus servent a extraire les frames correspondantes.
"""

import io
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import av

logger = logging.getLogger("amours.video")


@dataclass
class VideoInfo:
    """Metadata d'un fichier video."""

    path: str
    duration: float
    has_audio: bool
    has_video: bool
    # Audio
    audio_codec: Optional[str] = None
    audio_sample_rate: Optional[int] = None
    audio_channels: Optional[int] = None
    # Video
    video_codec: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None


@dataclass
class FrameExtraction:
    """Resultat d'extraction d'une frame a un timecode donne."""

    timestamp: float
    frame_index: int
    image_path: str
    width: int
    height: int
    segment_id: Optional[int] = None
    segment_text: Optional[str] = None


class VideoProcessor:
    """
    Extrait l'audio et les frames de fichiers video.

    L'audio extrait est compatible avec le pipeline Whisper existant.
    Les frames sont extraites aux timecodes des segments de transcription.
    """

    def __init__(self, thumbnail_width: int = 320):
        """
        Initialise le processeur video.

        Args:
            thumbnail_width: Largeur des thumbnails en pixels (hauteur auto).
        """
        self.thumbnail_width = thumbnail_width

    @staticmethod
    def is_video(file_path: str) -> bool:
        """
        Determine si un fichier est une video (contient un flux video).

        Args:
            file_path: Chemin ou URL du fichier media.

        Returns:
            True si le fichier contient au moins un flux video.
        """
        try:
            container = av.open(file_path)
            has_video = len(container.streams.video) > 0
            container.close()
            return has_video
        except Exception:
            return False

    def get_video_info(self, video_path: str) -> VideoInfo:
        """
        Recupere les metadonnees d'un fichier video.

        Args:
            video_path: Chemin ou URL du fichier video.

        Returns:
            VideoInfo avec toutes les metadonnees disponibles.
        """
        container = av.open(video_path)

        info = VideoInfo(
            path=video_path,
            duration=float(container.duration / av.time_base) if container.duration else 0,
            has_audio=len(container.streams.audio) > 0,
            has_video=len(container.streams.video) > 0,
        )

        if container.streams.audio:
            astream = container.streams.audio[0]
            info.audio_codec = astream.codec_context.name if astream.codec_context else None
            info.audio_sample_rate = astream.rate
            info.audio_channels = astream.channels if hasattr(astream, "channels") else None

        if container.streams.video:
            vstream = container.streams.video[0]
            info.video_codec = vstream.codec_context.name if vstream.codec_context else None
            info.width = vstream.codec_context.width
            info.height = vstream.codec_context.height
            if vstream.average_rate:
                info.fps = float(vstream.average_rate)
            info.frame_count = vstream.frames if vstream.frames > 0 else None

        container.close()
        return info

    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> str:
        """
        Extrait la piste audio d'une video en WAV mono 16kHz.

        Le fichier WAV produit est directement compatible avec Whisper.

        Args:
            video_path: Chemin ou URL du fichier video.
            output_path: Chemin de sortie WAV. Si None, genere un fichier temp.
            sample_rate: Frequence d'echantillonnage cible (16000 pour Whisper).

        Returns:
            Chemin du fichier WAV extrait.

        Raises:
            ValueError: Si le fichier ne contient pas de piste audio.
        """
        input_container = av.open(video_path)

        if not input_container.streams.audio:
            input_container.close()
            raise ValueError(f"Pas de piste audio dans: {video_path}")

        if output_path is None:
            stem = Path(video_path).stem if not video_path.startswith(("http", "srt")) else "video"
            tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".wav", prefix=f"{stem}_audio_"
            )
            output_path = tmp.name
            tmp.close()

        # Ouvrir le conteneur de sortie WAV
        output_container = av.open(output_path, mode="w")
        output_stream = output_container.add_stream("pcm_s16le", rate=sample_rate)
        output_stream.layout = "mono"

        # Creer un resampler pour convertir en mono 16kHz
        resampler = av.AudioResampler(
            format="s16",
            layout="mono",
            rate=sample_rate,
        )

        audio_stream = input_container.streams.audio[0]

        for frame in input_container.decode(audio_stream):
            # Resampler la frame
            resampled_frames = resampler.resample(frame)
            for resampled in resampled_frames:
                for packet in output_stream.encode(resampled):
                    output_container.mux(packet)

        # Flush encoder
        for packet in output_stream.encode():
            output_container.mux(packet)

        output_container.close()
        input_container.close()

        logger.info("Audio extrait: %s", output_path)
        return output_path

    def extract_frame_at(
        self,
        video_path: str,
        timestamp: float,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
    ) -> FrameExtraction:
        """
        Extrait une frame a un timecode precis en utilisant les PTS.

        Args:
            video_path: Chemin ou URL du fichier video.
            timestamp: Temps en secondes.
            output_path: Chemin de sortie JPEG. Si None, genere un nom.
            width: Largeur du thumbnail (None = taille originale).

        Returns:
            FrameExtraction avec le chemin de l'image et ses metadonnees.
        """
        container = av.open(video_path)
        vstream = container.streams.video[0]

        # Seek au timecode demande
        seek_ts = int(timestamp / vstream.time_base)
        container.seek(seek_ts, stream=vstream)

        target_width = width or self.thumbnail_width
        frame_data = None

        for frame in container.decode(vstream):
            actual_time = float(frame.pts * vstream.time_base) if frame.pts else 0

            # Redimensionner si necessaire
            if target_width and frame.width > target_width:
                scale = target_width / frame.width
                new_h = int(frame.height * scale)
                frame = frame.reformat(width=target_width, height=new_h)

            # Convertir en image
            img = frame.to_image()

            if output_path is None:
                ts_str = f"{timestamp:.3f}".replace(".", "_")
                stem = Path(video_path).stem if not video_path.startswith(("http", "srt")) else "video"
                output_path = str(
                    Path(tempfile.gettempdir()) / f"{stem}_frame_{ts_str}.jpg"
                )

            img.save(output_path, quality=85)

            frame_data = FrameExtraction(
                timestamp=actual_time,
                frame_index=frame.index if hasattr(frame, "index") else 0,
                image_path=output_path,
                width=frame.width,
                height=frame.height,
            )
            break  # On ne veut que la premiere frame apres le seek

        container.close()

        if frame_data is None:
            raise ValueError(f"Aucune frame trouvee a t={timestamp}s dans {video_path}")

        return frame_data

    def extract_frames_for_segments(
        self,
        video_path: str,
        segments: List[Dict],
        output_dir: str,
        strategy: str = "midpoint",
    ) -> List[FrameExtraction]:
        """
        Extrait une frame par segment de transcription.

        C'est la methode principale pour aligner video et transcription.
        Chaque segment Whisper produit une vignette representative.

        Args:
            video_path: Chemin ou URL du fichier video.
            segments: Liste de segments Whisper (dicts avec 'start', 'end', 'text').
            output_dir: Repertoire de sortie pour les images.
            strategy: 'midpoint' (milieu du segment) ou 'start' (debut).

        Returns:
            Liste de FrameExtraction, une par segment.
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        stem = Path(video_path).stem if not video_path.startswith(("http", "srt")) else "video"
        extractions = []

        container = av.open(video_path)
        vstream = container.streams.video[0]

        for seg in segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_id = seg.get("id", len(extractions))
            seg_text = seg.get("text", "")

            if strategy == "midpoint":
                ts = (seg_start + seg_end) / 2
            else:
                ts = seg_start

            # Seek et decode
            seek_ts = int(ts / vstream.time_base)
            try:
                container.seek(seek_ts, stream=vstream)
            except av.error.InvalidDataError:
                logger.warning("Seek impossible a t=%.3f pour segment %d", ts, seg_id)
                continue

            for frame in container.decode(vstream):
                actual_time = float(frame.pts * vstream.time_base) if frame.pts else ts

                # Redimensionner
                if frame.width > self.thumbnail_width:
                    scale = self.thumbnail_width / frame.width
                    new_h = int(frame.height * scale)
                    frame = frame.reformat(width=self.thumbnail_width, height=new_h)

                img = frame.to_image()
                img_filename = f"{stem}_seg{seg_id:04d}.jpg"
                img_path = output_path / img_filename
                img.save(str(img_path), quality=85)

                extractions.append(
                    FrameExtraction(
                        timestamp=actual_time,
                        frame_index=frame.index if hasattr(frame, "index") else 0,
                        image_path=str(img_path),
                        width=frame.width,
                        height=frame.height,
                        segment_id=seg_id,
                        segment_text=seg_text,
                    )
                )
                break  # Une seule frame par segment

        container.close()
        logger.info(
            "%d frames extraites pour %d segments depuis %s",
            len(extractions),
            len(segments),
            video_path,
        )
        return extractions

    def extract_audio_and_frames(
        self,
        video_path: str,
        audio_output: Optional[str] = None,
        frames_dir: Optional[str] = None,
        segments: Optional[List[Dict]] = None,
    ) -> Tuple[str, List[FrameExtraction]]:
        """
        Point d'entree principal : extrait audio ET frames en une passe.

        Si `segments` n'est pas fourni, extrait des frames a intervalle
        regulier (1 frame toutes les 5 secondes). Si `segments` est fourni
        (apres transcription Whisper), extrait une frame par segment.

        Args:
            video_path: Chemin ou URL du fichier video.
            audio_output: Chemin WAV de sortie. None = auto.
            frames_dir: Repertoire pour les frames. None = auto.
            segments: Segments Whisper pour extraction alignee.

        Returns:
            Tuple (chemin_audio_wav, liste_frame_extractions).
        """
        # Extraire l'audio
        audio_path = self.extract_audio(video_path, output_path=audio_output)

        frames = []

        # Verifier qu'il y a bien une piste video
        info = self.get_video_info(video_path)
        if not info.has_video:
            logger.info("Pas de piste video, extraction audio seule")
            return audio_path, frames

        if frames_dir is None:
            frames_dir = str(
                Path(tempfile.gettempdir()) / f"amours_frames_{Path(video_path).stem}"
            )

        if segments:
            # Extraction alignee sur les segments de transcription
            frames = self.extract_frames_for_segments(
                video_path, segments, frames_dir, strategy="midpoint"
            )
        else:
            # Extraction a intervalle regulier (avant transcription)
            interval = 5.0  # 1 frame toutes les 5 secondes
            duration = info.duration
            timestamps = []
            t = 0.0
            while t < duration:
                timestamps.append(t)
                t += interval

            Path(frames_dir).mkdir(parents=True, exist_ok=True)
            stem = Path(video_path).stem if not video_path.startswith(("http", "srt")) else "video"

            container = av.open(video_path)
            vstream = container.streams.video[0]

            for i, ts in enumerate(timestamps):
                seek_ts = int(ts / vstream.time_base)
                try:
                    container.seek(seek_ts, stream=vstream)
                except av.error.InvalidDataError:
                    continue

                for frame in container.decode(vstream):
                    actual_time = float(frame.pts * vstream.time_base) if frame.pts else ts

                    if frame.width > self.thumbnail_width:
                        scale = self.thumbnail_width / frame.width
                        new_h = int(frame.height * scale)
                        frame = frame.reformat(width=self.thumbnail_width, height=new_h)

                    img = frame.to_image()
                    img_path = Path(frames_dir) / f"{stem}_t{i:04d}.jpg"
                    img.save(str(img_path), quality=85)

                    frames.append(
                        FrameExtraction(
                            timestamp=actual_time,
                            frame_index=i,
                            image_path=str(img_path),
                            width=frame.width,
                            height=frame.height,
                        )
                    )
                    break

            container.close()
            logger.info(
                "%d frames extraites a intervalle %.1fs depuis %s",
                len(frames),
                interval,
                video_path,
            )

        return audio_path, frames
