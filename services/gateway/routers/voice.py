"""
RAG-ALL: Gateway Router - Voice
Text-to-Speech (TTS) and Speech-to-Text (STT) endpoints.
Routes to Voice Service for processing.
"""

import uuid
import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from httpx import AsyncClient

from shared.config.settings import settings
from shared.utils.logger import gateway_logger as logger

router = APIRouter()


@router.post("/stt")
async def speech_to_text(
    file: UploadFile = File(...),
    language: str = "vi",
):
    """
    Speech-to-Text: Chuyển audio thành text.
    Sử dụng Whisper model (local) để transcribe.
    """
    audio_id = str(uuid.uuid4())
    audio_path = f"data/cache/stt_{audio_id}_{file.filename}"

    logger.info(f"STT request: file={file.filename}, lang={language}")

    # Save uploaded audio
    try:
        content = await file.read()
        with open(audio_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save audio: {e}")

    # Route to Voice Service
    try:
        async with AsyncClient(timeout=60.0) as client:
            # Upload audio to voice service
            with open(audio_path, "rb") as f:
                files = {"file": (file.filename, f, file.content_type)}
                response = await client.post(
                    f"{settings.voice_service_url}/stt?language={language}",
                    files=files,
                )

            if response.status_code == 200:
                result = response.json()
                # Cleanup temp file
                os.remove(audio_path)
                return result
            else:
                raise HTTPException(status_code=500, detail="STT failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"STT error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tts")
async def text_to_speech(
    text: str,
    voice: str = "vi-VN-hoaimy-medium",
    speed: float = 1.0,
):
    """
    Text-to-Speech: Chuyển text thành audio.
    Sử dụng Piper TTS (local) hoặc Edge TTS (cloud fallback).
    """
    tts_id = str(uuid.uuid4())
    logger.info(f"TTS request: text={text[:50]}..., voice={voice}")

    try:
        async with AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.voice_service_url}/tts",
                json={
                    "text": text,
                    "voice": voice,
                    "speed": speed,
                    "output_path": f"data/cache/tts_{tts_id}.wav",
                },
            )

            if response.status_code == 200:
                result = response.json()
                audio_path = result.get("audio_path", "")

                if audio_path and os.path.exists(audio_path):
                    return FileResponse(
                        path=audio_path,
                        media_type="audio/wav",
                        filename=f"tts_{tts_id}.wav",
                    )
                else:
                    raise HTTPException(status_code=500, detail="TTS audio not generated")
            else:
                raise HTTPException(status_code=500, detail="TTS failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def list_voices(language: str = "vi"):
    """Liệt kê các giọng TTS có sẵn."""
    try:
        async with AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.voice_service_url}/voices?language={language}"
            )
            if response.status_code == 200:
                return response.json()
            return {"voices": []}
    except Exception:
        return {"voices": []}
