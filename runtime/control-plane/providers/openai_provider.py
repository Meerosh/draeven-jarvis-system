"""OpenAI Images API provider - dumb API client, no JARVIS logic."""

import base64
import ctypes
import os
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_OPENAI_CREDENTIAL_TARGET = "Draeven/OpenAI/API-Key"


class _WindowsCredential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD), ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR), ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME), ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p), ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _load_protected_openai_key() -> Optional[str]:
    """Read Draeven's key from Windows Credential Manager without logging it."""
    if os.name != "nt":
        return None
    credential_pointer = ctypes.POINTER(_WindowsCredential)()
    api = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    read = api.CredReadW
    read.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p)
    read.restype = wintypes.BOOL
    free = api.CredFree
    free.argtypes = (ctypes.c_void_p,)
    if not read(_OPENAI_CREDENTIAL_TARGET, 1, 0, ctypes.byref(credential_pointer)):
        return None
    try:
        item = credential_pointer.contents
        raw = ctypes.string_at(item.CredentialBlob, item.CredentialBlobSize)
        return raw.decode("utf-16-le")
    finally:
        free(credential_pointer)


@dataclass
class ImageGenerationRequest:
    """Structured request for image generation."""
    model: str
    prompt: str
    size: str
    quality: str
    n: int = 1
    reference_image_path: Optional[Path] = None


@dataclass
class ImageGenerationResult:
    """Result from image generation."""
    image_bytes: bytes
    model: str
    prompt: str
    size: str
    quality: str
    reference_image_used: bool


class OpenAIImageProvider:
    """
    Clean OpenAI Images API client.

    Responsibility: structured generation request -> OpenAI API -> return image bytes + sanitized metadata.

    Does NOT own JARVIS job mutation, asset registry, audit logging, or state transitions.
    """

    def __init__(self):
        """Initialize with an environment key or Draeven's protected credential."""
        self.api_key = os.environ.get("OPENAI_API_KEY") or _load_protected_openai_key()
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured")

    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        """
        Generate an image using OpenAI API.

        Args:
            request: ImageGenerationRequest with model, prompt, size, quality, and optional reference image.

        Returns:
            ImageGenerationResult with image bytes and sanitized metadata.

        Raises:
            RuntimeError: On API failure or missing reference image.
        """
        try:
            import openai
        except ImportError:
            raise RuntimeError("openai package not installed. Install with: pip install openai")

        client = openai.OpenAI(api_key=self.api_key)

        # Verify reference image exists if specified
        if request.reference_image_path:
            if not Path(request.reference_image_path).is_file():
                raise RuntimeError(f"Reference image not found: {request.reference_image_path}")

        # Add reference image if present - using edit endpoint for reference-guided generation
        if request.reference_image_path:
            # Keep the file handle scoped to the request so Windows can release it immediately.
            with open(request.reference_image_path, "rb") as image_file:
                response = client.images.edit(
                    model=request.model,
                    image=image_file,
                    prompt=request.prompt,
                    size=request.size,
                    quality=request.quality,
                    n=request.n,
                    response_format="b64_json",
                )
        else:
            # Text-only generation
            response = client.images.generate(
                model=request.model,
                prompt=request.prompt,
                size=request.size,
                quality=request.quality,
                n=request.n,
                response_format="b64_json",
            )

        # Extract first image (n=1 in Phase 1)
        if not response.data or not response.data[0].b64_json:
            raise RuntimeError("OpenAI API returned empty or invalid response")

        image_bytes = base64.b64decode(response.data[0].b64_json)

        return ImageGenerationResult(
            image_bytes=image_bytes,
            model=request.model,
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
            reference_image_used=bool(request.reference_image_path),
        )
