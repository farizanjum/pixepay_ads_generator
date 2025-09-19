import json
import re
import time
import base64
import os
from typing import List, Tuple, Dict, Any, Optional
from io import BytesIO

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Optional: Google Gemini SDK
try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    genai = None  # will error at call-time if not installed

# Load credentials and IDs from environment variables
API_KEY = os.getenv("OPENAI_API_KEY")
ANALYSIS_ASSISTANT_ID = os.getenv("ANALYSIS_ASSISTANT_ID")

# Google Gemini API key from environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def _extract_json_blocks(text: str) -> List[dict]:
    blocks: List[str] = []
    cur: List[str] = []
    in_json = False
    for line in text.splitlines():
        if line.strip().startswith("```") and "json" in line.lower():
            in_json = True
            cur = []
            continue
        if line.strip().startswith("```") and in_json:
            in_json = False
            if cur:
                blocks.append("\n".join(cur))
            cur = []
            continue
        if in_json:
            cur.append(line)

    if not blocks and text.strip().startswith("{"):
        try:
            json.loads(text)
            blocks.append(text)
        except Exception:
            pass

    parsed: List[dict] = []
    for b in blocks:
        try:
            parsed.append(json.loads(b))
        except Exception:
            pass
    return parsed


def _extract_prompts(text: str, desired_count: int = 5) -> List[str]:
    """Extract VU Engine prompts in the direct format, without modification.

    Expectations (enforced by validation but not mutated):
    - Lines start with "Create a" or "Create an"
    - Include full text in quotes and specify font, composition, and color scheme
    - Raw, casual, unpolished style
    - Exactly desired_count prompts are required (we will trim/duplicate to match desired_count)
    """
    lines = [l.strip() for l in text.splitlines()]
    prompts: List[str] = []
    current_prompt: List[str] = []
    in_prompt = False
    def save_current_prompt():
        nonlocal current_prompt, in_prompt
        if current_prompt:
            prompt_text = " ".join(current_prompt).strip()
            # Relaxed validation: accept any prompt starting with Create a/An
            if prompt_text.lower().startswith(("create a ", "create an ")):
                prompts.append(prompt_text)
        current_prompt = []
        in_prompt = False

    for line in lines:
        if not line:
            if in_prompt:
                save_current_prompt()
            continue

        # Check if this line starts a new VU Engine prompt
        line_lower = line.lower()

        # Handle various prompt start patterns:
        # - Direct: "Create a..."
        # - Numbered: "1. Create a..."
        # - Bulleted: "- Create a..." or "* Create a..."
        is_prompt_start = False
        clean_line = line

        if line_lower.startswith(("create a ", "create an ")):
            # Direct prompt start
            is_prompt_start = True
            clean_line = line
        elif line_lower.startswith(("image ", "image:")):
            # Handle "Image X:" prefix format
            # Extract the actual prompt after "Image X:"
            colon_pos = line.find(":")
            if colon_pos != -1:
                prompt_part = line[colon_pos + 1:].strip()
                if prompt_part.lower().startswith(("create a ", "create an ")):
                    is_prompt_start = True
                    clean_line = prompt_part
        elif (line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")) or
              line.strip().startswith(("-", "*"))):
            # Check if numbered or bulleted line contains "Create a/an"
            if ("create a " in line_lower or "create an " in line_lower):
                is_prompt_start = True
                # Remove the numbering/bullet from the start
                clean_line = line.lstrip("0123456789.-* ")

        if is_prompt_start and ("text \"" in clean_line.lower() or "with the text" in clean_line.lower()):
            # Save previous prompt if exists
            if in_prompt:
                save_current_prompt()

            current_prompt = [clean_line]
            in_prompt = True

        elif in_prompt:
            # Continuation of current prompt
            current_prompt.append(line)

    # Save final prompt if exists
    if in_prompt:
        save_current_prompt()

    # VU Engine: Ensure exactly desired_count variations
    if prompts:
        print(f"VU Engine: Extracted {len(prompts)} prompts from assistant response")

        # If we have more than desired_count, take first desired_count
        if len(prompts) > desired_count:
            prompts = prompts[:desired_count]
            print(f"VU Engine: Limited to first {desired_count} prompts")
        # If we have fewer than desired_count, duplicate the last one to reach desired_count
        elif len(prompts) < desired_count:
            original_count = len(prompts)
            while len(prompts) < desired_count:
                prompts.append(prompts[-1])
            print(f"VU Engine: Duplicated last prompt to reach {desired_count} variations (was {original_count})")

        print(f"VU Engine: Final prompt count: {len(prompts)}")

    return prompts


def analyze_images(api_key: Optional[str], assistant_id: Optional[str], images: List[Tuple[str, bytes]], *, desired_count: int = 5) -> Tuple[dict, dict]:
    """
    VU Engine Ad Creative Generator - Stage A & B Implementation

    Stage A (Internal): Analyze images with OpenAI Assistant for detailed extraction. The Assistant MUST:
    - Parse ALL visible text exactly as shown (multi-line, ordering, casing)
    - Identify each text block's position (top/middle/bottom; left/center/right) and relationships
    - Identify main visual(s); if no visual, explicitly state "no main visual"
    - Describe visual subject(s) concretely (people/objects/scene), materials, style, lighting
    - Summarize composition and layout (where text and visuals sit relative to each other)
    - Classify font family/style if possible; otherwise describe typographic traits (e.g., bold condensed sans, rounded display), or omit
    - Describe background type and texture
    - Extract and analyze color palette, considering contrast, relationships, and color psychology
    - Assess readability/contrast issues
    - Flag risky elements and compliance concerns

    Stage B (Output): Produce exactly desired_count direct prompts (no JSON wrapper) that:
    - Start with "Create a" or "Create an"
    - Explicitly include all extracted text in quotes, preserving lines and order
    - Specify font family/style if clearly identifiable; otherwise describe typographic traits briefly, or omit
    - Specify composition and positions for every text block and visual(s)
    - Describe visuals in detail; if no visuals, state that explicitly
    - Include background description and a dynamic color scheme based on analyzed colors (not just muted/dull)
    - Emphasize raw, casual, unpolished aesthetic (no glossy/premium)
    - Distribute prompts across uploaded images fairly: keep counts as even as possible (difference between any two images' counts ≤ 1). Example for 3 images and 5 prompts: 2/2/1

    IMPORTANT: Sends ONLY images to assistant (no extra text input besides images).
    Returns base prompt JSON and a dict {"prompts": [..desired_count strings..]}.

    Required prompt qualities:
    - Must start with "Create a" or "Create an".
    - Must include all text in quotes (can include multiple lines in separate quotes).
    - Must include font family/style.
    - Must describe composition placements explicitly.
    - Must include background/style and dynamic color scheme based on analyzed colors.
    """
    api_key = api_key or API_KEY
    assistant_id = assistant_id or ANALYSIS_ASSISTANT_ID
    client = OpenAI(api_key=api_key)

    file_ids: List[str] = []
    for name, data in images:
        file = BytesIO(data)
        file.name = f"{name}.png" if not hasattr(file, "name") else file.name
        fr = client.files.create(file=file, purpose="vision")
        file_ids.append(fr.id)

    thread = client.beta.threads.create()
    # Provide explicit instruction text to solve context and fidelity issues
    instruction_text = (
        f"You are an Ad Creative analyst. Analyze each uploaded image individually and create prompts that perfectly match each image's characteristics.\n"
        f"Generate exactly {desired_count} prompts total, distributed randomly but fairly across all uploaded images.\n"
        "CRITICAL DISTRIBUTION RULE:\n"
        "- If you have multiple images, randomly assign prompts to different images.\n"
        "- Example: For 2 images and 5 prompts, you might assign 3 prompts to image 1 and 2 prompts to image 2, OR 2 prompts to image 1 and 3 prompts to image 2, etc.\n"
        "- Make the distribution as even as possible but feel free to vary it randomly.\n"
        "- Each prompt should clearly reference which image it corresponds to.\n"
        "Rules you MUST follow strictly:\n"
        "1) Analyze EACH image separately and create prompts that replicate its exact style, colors, and composition.\n"
        "2) If an image is text-only (no visuals), generate text-only prompts with no graphics, photos, or illustrations.\n"
        "3) If an image has visuals, include the same type of visual elements (photos, illustrations, graphics) in the prompts.\n"
        "4) Copy ALL visible text exactly as shown, preserving order and formatting.\n"
        "5) Match the exact color scheme and style of each image - if it's vibrant, use vibrant colors; if it's muted, use muted colors.\n"
        "6) Maintain the same composition, layout, and visual hierarchy as each original image.\n"
        "7) Each prompt must start with 'Create a' or 'Create an'.\n"
        "8) Output ONLY the prompts, no commentary.\n"
        "IMAGE-SPECIFIC REQUIREMENTS:\n"
        "- For each image, analyze: color palette, visual style, composition, text placement, background type.\n"
        "- Generate prompts that would recreate nearly identical versions of each uploaded image.\n"
        "- Match the mood, style, and aesthetic exactly - no generic or default styles.\n"
        "- If an image has a specific visual theme (e.g., nature, technology, people), incorporate that theme.\n"
        "- Preserve the exact font style and text positioning from each image.\n"
        "VARIATION RULES:\n"
        "- Create subtle variations within the same style (slight color adjustments, minor layout tweaks).\n"
        "- Stay true to each image's original characteristics - don't mix styles between images.\n"
        "- Each set of prompts for an image should maintain visual consistency.\n"
        "OUTPUT FORMAT:\n"
        "- List all prompts clearly, indicating which image each prompt corresponds to.\n"
        "- Example: 'Image 1: Create a...' then 'Image 2: Create a...' etc.\n"
    )

    # Build a single message with instruction text followed by image parts
    content: List[Dict[str, Any]] = [
        {"type": "text", "text": instruction_text}
    ]
    for fid in file_ids:
        content.append({"type": "image_file", "image_file": {"file_id": fid, "detail": "high"}})

    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=content)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)

    while run.status in ("queued", "in_progress", "cancelling"):
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    if run.status != "completed":
        raise RuntimeError(f"Assistant run failed: {run.status}")

    msgs = client.beta.threads.messages.list(thread_id=thread.id)
    raw: Optional[str] = None
    for m in msgs.data:
        if m.role == "assistant":
            # take first text item
            for part in m.content:
                if part.type == "text":
                    raw = part.text.value
                    break
        if raw:
            break
    if not raw:
        raise RuntimeError("No assistant response found")

    # VU Engine: Parse prompt-only output in the new format
    prompts = _extract_prompts(raw, desired_count)
    if not prompts:
        raise RuntimeError("Assistant returned no prompts starting with 'Create a/An'. Please check the assistant's output or adjust instructions.")

    # Return prompts directly in the new format structure
    base = {
        "type": "vu_engine_direct_prompts",
        "engine": "VU Engine v2.0",
        "format": "direct_prompts",
        "variations_count": len(prompts),
        "note": "Direct VU Engine prompts - no JSON wrapper"
    }

    variants = {
        "prompts": prompts,
        "metadata": {
            "variation_count": len(prompts),
            "format_version": "2.0",
            "creativity_limit": "±5%",
            "similarity_lock": "enabled",
            "structure_lock": "enabled"
        }
    }

    return base, variants


def _gemini_generate_image(api_key: Optional[str], prompt_text: str, *, size: str = "1024x1024", reference_images: Optional[List[bytes]] = None) -> bytes:
    """VU Engine Image Generation using Gemini 2.5 Flash Image Preview with Reference Images.

    This function takes VU Engine creative prompts and generates raw, unpolished images
    that break the polished feed pattern while maintaining high similarity to reference images.

    VU Engine Features:
    - Raw, casual, unpolished aesthetic with imperfections
    - Uses reference images for maximum similarity (±2% creativity only)
    - Preserves exact text structure and positioning
    - Breaks glossy, luxury, premium patterns
    - Includes reference images in Gemini API calls for better fidelity

    Uses Gemini 2.5 Flash Image Preview model for optimal VU Engine results.
    """
    key = (api_key or GOOGLE_API_KEY or "").strip()
    if not genai:
        raise RuntimeError("google-generativeai is not installed. Add it to requirements and install.")
    if not key:
        raise RuntimeError("Missing Google API key. Set GOOGLE_API_KEY environment variable.")

    # Configure SDK
    genai.configure(api_key=key)

    # Use the correct Gemini 2.5 Flash Image Preview model
    model_name = "models/gemini-2.5-flash-image-preview"
    model = genai.GenerativeModel(model_name)

    # Pass prompt verbatim as requested (no automatic additions)
    enhanced_prompt = str(prompt_text).strip()

    # Helpers: retry with the exact same prompt only
    def _try_generate_with_retries(model_obj: Any, content: List[Any], *, retries: int = 3, base_delay: float = 0.8):
        last_err: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                return model_obj.generate_content(content)
            except Exception as e:  # noqa: BLE001
                last_err = e
                # Backoff
                try:
                    import time as _time
                    _time.sleep(base_delay * attempt)
                except Exception:
                    pass
        if last_err:
            raise last_err
        raise RuntimeError("Unknown error during Gemini generation retries")

    # Try different approaches for Gemini image generation
    response = None

    # First try: With reference images (disabled by default)
    if reference_images and len(reference_images) > 0 and False:  # Disabled per request (prompt-only for now)
        try:
            print(f"VU Engine: Attempting generation with {len(reference_images)} reference images")

            content_parts = []
            valid_images = []

            # Process reference images
            try:
                from PIL import Image
                import io
                pil_available = True
            except ImportError:
                pil_available = False
                print("VU Engine: PIL not available, skipping reference image processing")

            if pil_available:
                for i, img_bytes in enumerate(reference_images[:3]):  # Limit to 3 images max
                    try:
                        # Convert bytes to PIL Image for Gemini
                        img = Image.open(io.BytesIO(img_bytes))
                        # Ensure image is in RGB mode
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        valid_images.append(img)
                        print(f"VU Engine: Processed reference image {i+1}")
                    except Exception as e:
                        print(f"VU Engine: Could not process reference image {i+1}: {e}")
            else:
                print("VU Engine: PIL not available, using prompt-only generation")

            if valid_images:
                # Try with images + text (some Gemini models support this)
                content_parts = valid_images + [enhanced_prompt]
                try:
                    response = _try_generate_with_retries(model, content_parts)
                    print("VU Engine: Successfully generated with reference images + prompt")
                except Exception as img_error:
                    print(f"VU Engine: Failed with images + prompt: {img_error}")

                    # Fallback: Try with just the prompt (no images)
                    try:
                        response = _try_generate_with_retries(model, [enhanced_prompt])
                        print("VU Engine: Fallback successful - generated with prompt only")
                    except Exception as prompt_error:
                        print(f"VU Engine: Fallback also failed: {prompt_error}")
                        # Final fallback: simplified prompt-only
                        try:
                            simplified = _simplify_prompt(enhanced_prompt)
                            response = _try_generate_with_retries(model, [simplified])
                            print("VU Engine: Final fallback successful - simplified prompt only")
                        except Exception as final_prompt_error:
                            raise RuntimeError(
                                f"Gemini image generation failed with images, prompt, and simplified prompt. "
                                f"Image error: {img_error}; Prompt error: {prompt_error}; Final: {final_prompt_error}"
                            )
            else:
                # No valid images, use prompt only
                try:
                    response = _try_generate_with_retries(model, [enhanced_prompt])
                except Exception as prompt_only_error:
                    # Final fallback: simplified prompt-only
                    simplified = _simplify_prompt(enhanced_prompt)
                    response = _try_generate_with_retries(model, [simplified])
                print("VU Engine: No valid reference images, generated with prompt only")

        except Exception as e:
            print(f"VU Engine: Reference image approach failed: {e}")
            # Final fallback: prompt only
            try:
                response = _try_generate_with_retries(model, [enhanced_prompt])
                print("VU Engine: Final fallback successful - generated with prompt only")
            except Exception as final_error:
                # Final fallback: simplified prompt-only
                simplified = _simplify_prompt(enhanced_prompt)
                try:
                    response = _try_generate_with_retries(model, [simplified])
                    print("VU Engine: Final fallback successful - simplified prompt only")
                except Exception as very_final_error:
                    raise RuntimeError(
                        f"All Gemini image generation attempts failed. Final error: {very_final_error}"
                    )
    else:
        # No reference images provided, use prompt only
        print("VU Engine: No reference images provided, generating with prompt only (verbatim)")
        response = _try_generate_with_retries(model, [enhanced_prompt])

    # Handle VU Engine Gemini 2.5 Flash Image Preview response
    try:
        # Debug: Print response structure to understand what we're getting
        print(f"Gemini Response Type: {type(response)}")
        print(f"Gemini Response Attributes: {dir(response)}")

        # Check if response has direct binary data
        if hasattr(response, 'binary') and response.binary:
            print("✅ Found binary data in response")
            return response.binary

        # Check for image data in response parts
        if hasattr(response, 'parts') and response.parts:
            print(f"✅ Found {len(response.parts)} parts in response")
            for i, part in enumerate(response.parts):
                print(f"Part {i}: {type(part)}, attributes: {dir(part)}")
                if hasattr(part, 'inline_data') and part.inline_data:
                    data = part.inline_data.data
                    if data:
                        print(f"✅ Found inline data in part {i}")
                        # Data might be base64 encoded
                        if isinstance(data, str):
                            return base64.b64decode(data)
                        elif isinstance(data, (bytes, bytearray)):
                            return bytes(data)

        # Check candidates for image data
        if hasattr(response, 'candidates') and response.candidates:
            print(f"✅ Found {len(response.candidates)} candidates")
            for i, candidate in enumerate(response.candidates):
                print(f"Candidate {i}: {type(candidate)}")
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    print(f"Candidate {i} has content with {len(candidate.content.parts)} parts")
                    for j, part in enumerate(candidate.content.parts):
                        if hasattr(part, 'inline_data') and part.inline_data:
                            data = part.inline_data.data
                            if data:
                                print(f"✅ Found inline data in candidate {i}, part {j}")
                                # Data might be base64 encoded
                                if isinstance(data, str):
                                    return base64.b64decode(data)
                                elif isinstance(data, (bytes, bytearray)):
                                    return bytes(data)

        # Check if response is text-based (model returned text instead of image)
        if hasattr(response, 'text') and response.text:
            print(f"⚠️ Response contains text instead of image: {response.text[:100]}...")
            raise RuntimeError(f"Gemini returned text instead of image. Response: {response.text[:200]}")

        # Try accessing raw response data
        if hasattr(response, '_result') and hasattr(response._result, 'data'):
            print("✅ Found data in _result")
            return response._result.data

        # Print full response structure for debugging
        print("Full response structure:")
        print(str(response)[:500])

    except Exception as e:
        raise RuntimeError(f"Failed to extract image data from Gemini response: {e}")

    raise RuntimeError("VU Engine Error: Gemini 2.5 Flash Image Preview did not return image bytes. The VU Engine may have issues with the prompt format or API configuration. Check that your Gemini API key has access to image generation and that the VU Engine prompt follows the required format.")


def generate_single_variant_image(api_key: Optional[str], base_prompt_json: dict, variant_json: dict, *, size: str = "1024x1024", reference_images: Optional[List[bytes]] = None) -> bytes:
    """VU Engine Single Variant Image Generation with Reference Images.

    Generates one VU Engine variation from the new direct prompt format.
    Uses reference images to ensure high similarity to originals.
    Applies raw, casual, unpolished styling with imperfections within ±2% margin.
    Preserves exact text structure and positioning while breaking polished patterns.

    Now handles direct VU Engine prompt format with reference image support.
    """
    # Handle new direct prompt format
    prompt_text = None

    # Check if variant_json is a direct prompt string
    if isinstance(variant_json, str) and variant_json.strip():
        prompt_text = variant_json.strip()

    # Check if variant_json contains a "prompt" field (legacy support)
    elif isinstance(variant_json, dict) and "prompt" in variant_json and isinstance(variant_json["prompt"], str):
        prompt_text = variant_json["prompt"].strip()

    # Check if it's the new format with "prompts" array
    elif isinstance(variant_json, dict) and "prompts" in variant_json and isinstance(variant_json["prompts"], list):
        # Use the first prompt from the array
        if variant_json["prompts"]:
            prompt_text = str(variant_json["prompts"][0]).strip()

    if not prompt_text:
        # Final fallback
        prompt_text = "Create a simple ad with raw, unpolished styling and imperfections."

    # Pass the Assistant's prompt verbatim to Gemini
    print(f"VU Engine: Generating image for prompt (verbatim): {prompt_text[:140]}...")
    return _gemini_generate_image(api_key, prompt_text, size=size, reference_images=None)


def build_prompt_text(base_prompt_json: dict, variant_json: dict) -> str:
    """Return the exact creative prompt text for a given variant.

    If variant_json contains a 'prompt' field, return it directly; otherwise, build a JSON-style prompt string for debugging/compat.
    """
    if isinstance(variant_json, dict) and isinstance(variant_json.get("prompt"), str):
        return variant_json["prompt"].strip()

    prompt_copy = json.loads(json.dumps(base_prompt_json))
    if isinstance(prompt_copy, dict):
        if "instructions" in prompt_copy and isinstance(prompt_copy.get("instructions"), dict):
            prompt_copy["instructions"]["variants"] = [variant_json]
        else:
            prompt_copy["variants"] = [variant_json]
    return json.dumps(prompt_copy, ensure_ascii=False, indent=2)


