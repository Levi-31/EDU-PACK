import io
import os
import httpx
from PIL import Image
from app.modules.research.interfaces import ImageGeneratorService


def standardize_image_bytes(img_bytes: bytes, target_width: int = 1600, target_height: int = 900, inner_margin: float = 0.90) -> bytes:
    """
    Standardizes any generated image to an exact 16:9 widescreen canvas (1600x900)
    with safe centered margins so no text labels, boxes, or arrows are ever cut off.
    """
    try:
        with Image.open(io.BytesIO(img_bytes)) as img:
            img = img.convert("RGB")
            max_w = int(target_width * inner_margin)
            max_h = int(target_height * inner_margin)
            scale = min(max_w / img.width, max_h / img.height)
            new_w = max(1, int(img.width * scale))
            new_h = max(1, int(img.height * scale))
            resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Sample background color from image corners (default white)
            corners = [
                img.getpixel((0, 0)),
                img.getpixel((img.width - 1, 0)),
                img.getpixel((0, img.height - 1)),
                img.getpixel((img.width - 1, img.height - 1))
            ]
            bg_color = (255, 255, 255)
            for c in corners:
                if isinstance(c, tuple) and len(c) >= 3 and c[0] > 230 and c[1] > 230 and c[2] > 230:
                    bg_color = (c[0], c[1], c[2])
                    break
            
            canvas = Image.new("RGB", (target_width, target_height), bg_color)
            offset_x = (target_width - new_w) // 2
            offset_y = (target_height - new_h) // 2
            canvas.paste(resized, (offset_x, offset_y))
            
            buf = io.BytesIO()
            canvas.save(buf, format="PNG", optimize=True)
            return buf.getvalue()
    except Exception:
        return img_bytes


class GeminiImageGeneratorService(ImageGeneratorService):
    """
    Gemini-based image generator service using async client.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")

    async def generate_image_bytes(self, prompt: str) -> bytes:
        from google import genai
        from google.genai import types

        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set.")

        guarded_prompt = (
            f"{prompt.strip()} "
            "Clean technical diagram centered on a solid white background. "
            "Widescreen landscape 16:9 composition with generous margins on all sides. "
            "All text labels, diagram nodes, and connectors must be completely contained in frame."
        )

        client = genai.Client(api_key=self.api_key)

        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=guarded_prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_ONLY_HIGH",
                    )
                ],
            ),
        )

        parts = getattr(resp, "parts", None)
        if not parts and getattr(resp, "candidates", None):
            try:
                parts = resp.candidates[0].content.parts
            except Exception:
                parts = None

        if not parts:
            raise RuntimeError("No image content returned (safety/quota/SDK change).")

        for part in parts:
            inline = getattr(part, "inline_data", None)
            if inline and getattr(inline, "data", None):
                return standardize_image_bytes(inline.data)

        raise RuntimeError("No inline image bytes found in response.")


class OpenAIImageGeneratorService(ImageGeneratorService):
    """
    OpenAI DALL-E / GPT-Image based image generator service using AsyncOpenAI.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    async def generate_image_bytes(self, prompt: str) -> bytes:
        from openai import AsyncOpenAI
        from app.modules.research.config import OPENAI_IMAGE_MODEL

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")

        client = AsyncOpenAI(api_key=self.api_key)

        # Select appropriate widescreen dimensions for the model
        model_lower = OPENAI_IMAGE_MODEL.lower()
        if "gpt-image" in model_lower:
            size = "1536x1024"  # Landscape standard for gpt-image models
        elif "dall-e-3" in model_lower:
            size = "1792x1024"  # 16:9 widescreen standard for DALL-E 3
        else:
            size = "1024x1024"

        # Explicit safe margin instruction to prevent edge clipping
        guarded_prompt = (
            f"{prompt.strip()} "
            "Clean, high-contrast technical diagram centered on a solid white background. "
            "Widescreen landscape composition. The entire diagram must be fully contained within "
            "the center with generous 15% white margin around all outer edges. "
            "All text labels, boxes, and arrows must fit completely inside with zero edge clipping."
        )

        params = {
            "model": OPENAI_IMAGE_MODEL,
            "prompt": guarded_prompt,
            "size": size,
            "n": 1
        }
        
        # dall-e-2 does not support quality parameter, others do
        if OPENAI_IMAGE_MODEL != "dall-e-2":
            params["quality"] = "auto"

        response = await client.images.generate(**params)

        # Handle URL output (standard for DALL-E)
        image_url = getattr(response.data[0], "url", None)
        if image_url:
            async with httpx.AsyncClient() as http_client:
                image_response = await http_client.get(image_url)
                image_response.raise_for_status()
                return standardize_image_bytes(image_response.content)

        # Handle base64 output (standard for gpt-image models)
        b64_json = getattr(response.data[0], "b64_json", None)
        if b64_json:
            import base64
            raw_bytes = base64.b64decode(b64_json)
            return standardize_image_bytes(raw_bytes)

        raise RuntimeError("No image URL or base64 data returned from OpenAI.")
