"""
RAG-ALL: Voice Service - Main Application
Piper TTS (offline) + Faster-Whisper STT.

Voice Features:
  - Text-to-Speech: Piper TTS (Vietnamese + English, offline)
  - Speech-to-Text: Faster-Whisper (offline, fast)
  - Voice selection (multiple voices per language)
  - Speed control
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Any
import os
import tempfile

from shared.config.settings import settings
from shared.utils.logger import voice_logger as service_logger


# =============================================================================
# Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    service_logger.info("🚀 Starting Voice Service...")
    service_logger.info(f"   TTS model dir: {settings.piper_model_dir}")
    service_logger.info(f"   STT model: {settings.whisper_model}")
    yield
    service_logger.info("🔄 Shutting down Voice Service...")


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="RAG-ALL Voice Service",
    description="Piper TTS + Faster-Whisper STT",
    version="0.1.0",
    lifespan=lifespan,
)


# =============================================================================
# Request/Response Models
# =============================================================================

class TTSRequest(BaseModel):
    text: str
    language: str = "vi"  # vi, en
    voice: str = "default"
    speed: float = 1.0


class TTSResponse(BaseModel):
    audio_file: str
    duration: float = 0.0
    format: str = "wav"


class STTResponse(BaseModel):
    text: str
    language: str = ""
    confidence: float = 0.0
    duration: float = 0.0


# =============================================================================
# Piper TTS Wrapper
# =============================================================================

class PiperTTS:
    """Piper TTS wrapper for offline text-to-speech."""

    def __init__(self):
        self._voices = {
            "vi": "vi_VN-huymetric-medium",
            "en": "en_US-lessac-medium",
        }

    async def synthesize(
        self,
        text: str,
        language: str = "vi",
        voice: str = "default",
        speed: float = 1.0,
    ) -> str:
        """
        Convert text to speech.

        Args:
            text: Input text
            language: Language code
            voice: Voice name
            speed: Speech speed (0.5-2.0)

        Returns:
            Path to generated audio file
        """
        import subprocess
        import uuid

        # Get voice name
        if voice == "default":
            voice_name = self._voices.get(language, self._voices["en"])
        else:
            voice_name = voice

        # Create temp file
        output_file = os.path.join(
            tempfile.gettempdir(),
            f"tts_{uuid.uuid4().hex}.wav"
        )

        try:
            # Use piper CLI
            cmd = [
                "piper",
                "--model", voice_name,
                "--output_file", output_file,
            ]

            # Pipe text to piper
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            stdout, stderr = process.communicate(input=text.encode("utf-8"))

            if process.returncode != 0:
                service_logger.error(f"Piper error: {stderr.decode()}")
                raise Exception(f"Piper TTS failed: {stderr.decode()}")

            service_logger.info(f"TTS generated: {output_file}")
            return output_file

        except FileNotFoundError:
            # Piper not installed, use edge-tts as fallback
            service_logger.warning("Piper not found, using edge-tts fallback")
            return await self._edge_tts_fallback(text, language, output_file)

    async def _edge_tts_fallback(
        self,
        text: str,
        language: str,
        output_file: str,
    ) -> str:
        """Fallback to edge-tts (requires internet)."""
        import subprocess

        voice_map = {
            "vi": "vi-VN-HoaiMyNeural",
            "en": "en-US-JennyNeural",
        }

        voice = voice_map.get(language, voice_map["en"])

        cmd = [
            "edge-tts",
            "--voice", voice,
            "--text", text,
            "--write-media", output_file,
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        process.communicate()

        if process.returncode != 0:
            raise Exception("edge-tts fallback failed")

        return output_file


# =============================================================================
# Faster-Whisper Wrapper
# =============================================================================

class FasterWhisperSTT:
    """Faster-Whisper wrapper for offline speech-to-text."""

    def __init__(self):
        self._model = None

    def _ensure_model(self):
        if self._model is not None:
            return

        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                settings.whisper_model,
                device="cpu",
                compute_type="int8",
            )
            service_logger.info(f"Whisper model loaded: {settings.whisper_model}")
        except Exception as e:
            service_logger.error(f"Failed to load Whisper model: {e}")
            raise

    async def transcribe(
        self,
        audio_file: str,
        language: str = None,
    ) -> dict:
        """
        Transcribe audio to text.

        Args:
            audio_file: Path to audio file
            language: Optional language hint

        Returns:
            {text, language, confidence, duration}
        """
        self._ensure_model()

        try:
            segments, info = self._model.transcribe(
                audio_file,
                language=language,
                beam_size=5,
            )

            # Combine segments
            text = " ".join([s.text for s in segments])

            return {
                "text": text.strip(),
                "language": info.language,
                "confidence": info.language_probability,
                "duration": info.duration,
            }

        except Exception as e:
            service_logger.error(f"Transcription error: {e}")
            return {
                "text": "",
                "language": "",
                "confidence": 0.0,
                "duration": 0.0,
            }


# =============================================================================
# Initialize & Endpoints
# =============================================================================

tts = PiperTTS()
stt = FasterWhisperSTT()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "voice"}


@app.post("/tts", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest) -> TTSResponse:
    """Convert text to speech."""
    service_logger.info(f"TTS: '{request.text[:30]}...' lang={request.language}")

    try:
        audio_file = await tts.synthesize(
            text=request.text,
            language=request.language,
            voice=request.voice,
            speed=request.speed,
        )

        # Get file size for duration estimate
        file_size = os.path.getsize(audio_file)
        duration = file_size / (16000 * 2)  # Rough estimate for 16kHz 16-bit audio

        return TTSResponse(
            audio_file=audio_file,
            duration=duration,
            format="wav",
        )
    except Exception as e:
        service_logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tts/download/{filename}")
async def download_tts(filename: str):
    """Download generated TTS audio file."""
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type="audio/wav",
        filename=filename,
    )


@app.post("/stt", response_model=STTResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = None,
) -> STTResponse:
    """Convert speech to text."""
    service_logger.info(f"STT: file={file.filename}")

    # Save uploaded file
    temp_file = os.path.join(tempfile.gettempdir(), f"stt_{file.filename}")
    with open(temp_file, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = await stt.transcribe(temp_file, language)
        return STTResponse(**result)
    except Exception as e:
        service_logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)


@app.get("/voices")
async def list_voices():
    """List available voices."""
    return {
        "tts_voices": {
            "vi": ["vi_VN-huymetric-medium"],
            "en": ["en_US-lessac-medium"],
        },
        "stt_models": ["tiny", "base", "small", "medium", "large-v2"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
