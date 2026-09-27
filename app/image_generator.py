import hashlib
import io
import logging
import math
import os
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import requests

load_dotenv()
logger = logging.getLogger(__name__)

STATIC_PANELS_DIR = os.path.join("static", "panels")
HORDE_API_URL = "https://aihorde.net/api/v2/generate"
HORDE_HEADERS = {
    "apikey": "0000000000",
    "Client-Agent": "ComicCraft:2.0:production",
    "Content-Type": "application/json"
}


def ensure_panels_directory():
    """Ensures the static/panels directory exists."""
    os.makedirs(STATIC_PANELS_DIR, exist_ok=True)


def sanitize_filename(prompt: str, panel_num: int = 1) -> str:
    """Generates a clean, filesystem-safe filename with timestamp and hash."""
    clean_text = re.sub(r"[^\w\s-]", "", prompt.lower()).strip()
    slug = re.sub(r"[-\s]+", "_", clean_text)[:28]
    prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:6]
    timestamp = int(time.time())
    return f"panel_{panel_num}_{timestamp}_{slug}_{prompt_hash}.png"


def _build_enhanced_prompt(prompt: str, art_style: str) -> str:
    """
    Constructs high-clarity Stable Diffusion prompt with comic styling,
    sharp lineart, cel shading, and an explicit negative prompt to eliminate blur.
    """
    clean_prompt = prompt.replace("masterpiece comic panel, ", "").replace("masterpiece action comic panel, ", "").strip()
    clean_prompt = clean_prompt[:220]
    
    pos = (
        f"masterpiece comic book panel, {art_style} style, {clean_prompt}, "
        f"sharp clean ink outlines, vivid dynamic anime cel shading, cinematic comic lighting, "
        f"high contrast, clean details, 8k resolution, graphic novel illustration"
    )
    neg = (
        "blurry, photographic, stock photo, watermark, bad anatomy, deformed, distorted, "
        "low quality, duplicate, text glitch, out of focus, realistic photo, amateur"
    )
    return f"{pos} ### {neg}"


def _submit_horde_task(full_prompt: str, session: requests.Session) -> Optional[str]:
    """Submits a single generation task to AI Horde with retry logic for 429 rate limits."""
    payload = {
        "prompt": full_prompt,
        "params": {
            "width": 512,
            "height": 512,
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler_name": "k_euler"
        }
    }
    for attempt in range(4):
        try:
            res = session.post(f"{HORDE_API_URL}/async", json=payload, headers=HORDE_HEADERS, timeout=12)
            if res.status_code == 202:
                task_id = res.json().get("id")
                return task_id
            elif res.status_code == 429:
                logger.info("AI Horde rate-limited (429) on submit attempt %s. Pausing 3s...", attempt + 1)
                time.sleep(3.0)
            else:
                logger.warning("AI Horde submit returned HTTP %s: %s", res.status_code, res.text[:120])
                time.sleep(2.0)
        except Exception as e:
            logger.debug("AI Horde submit exception: %s", e)
            time.sleep(1.5)
    return None


def _fetch_horde_image(task_id: str, session: requests.Session) -> Optional[Image.Image]:
    """Fetches the generated image from AI Horde status endpoint."""
    try:
        status_res = session.get(f"{HORDE_API_URL}/status/{task_id}", headers=HORDE_HEADERS, timeout=10)
        if status_res.status_code == 200:
            gens = status_res.json().get("generations", [])
            if gens and gens[0].get("img"):
                img_url = gens[0].get("img")
                r = session.get(img_url, timeout=14)
                if r.status_code == 200 and len(r.content) > 3000:
                    img = Image.open(io.BytesIO(r.content)).convert("RGB")
                    # Upscale or standardize to 768x512
                    return img.resize((768, 512), Image.Resampling.LANCZOS)
    except Exception as e:
        logger.warning("Failed to fetch image for Horde task %s: %s", task_id, e)
    return None


def _generate_via_pollinations(prompt: str, art_style: str, panel_num: int) -> Optional[Image.Image]:
    """
    Fallback cloud image generator via Pollinations with fast timeout.
    """
    clean_prompt = prompt.replace("masterpiece comic panel, ", "").replace("masterpiece action comic panel, ", "")[:140].strip()
    full_prompt = f"{clean_prompt}, {art_style} comic book illustration, sharp ink linework, vivid cel shading"
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = abs(hash(prompt + str(panel_num))) % 100000

    try:
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&nologo=true&seed={seed}&model=flux"
        logger.info("Attempting Pollinations generation for Panel %s...", panel_num)
        response = requests.get(url, timeout=8)
        if response.status_code == 200 and len(response.content) > 5000:
            img = Image.open(io.BytesIO(response.content)).convert("RGB")
            logger.info("Panel %s Pollinations generation succeeded (%sx%s)", panel_num, img.width, img.height)
            return img
    except Exception as e:
        logger.debug("Pollinations fallback failed for panel %s: %s", panel_num, e)

    return None


def _render_stylized_comic_art(prompt: str, art_style: str = "comic book", panel_num: int = 1) -> Image.Image:
    """
    High-quality graphic novel canvas fallback when offline or all cloud endpoints fail.
    Renders dynamic action rays, comic border, and styled typography.
    Guarantees NO stock photography (zero picsum bulldog photos).
    """
    width, height = 768, 512
    img = Image.new("RGB", (width, height), color=(20, 24, 28))
    draw = ImageDraw.Draw(img)

    center_x, center_y = width // 2, height // 2
    num_rays = 20
    for i in range(num_rays):
        if i % 2 == 0:
            angle1 = (i / num_rays) * 2 * math.pi
            angle2 = ((i + 1) / num_rays) * 2 * math.pi
            r = max(width, height)
            p1 = (center_x, center_y)
            p2 = (int(center_x + r * math.cos(angle1)), int(center_y + r * math.sin(angle1)))
            p3 = (int(center_x + r * math.cos(angle2)), int(center_y + r * math.sin(angle2)))
            draw.polygon([p1, p2, p3], fill=(32, 40, 48))

    # Bold comic border
    border_inset = 12
    draw.rectangle(
        [(border_inset, border_inset), (width - border_inset, height - border_inset)],
        outline=(245, 245, 240),
        width=5
    )
    draw.rectangle(
        [(border_inset + 6, border_inset + 6), (width - border_inset - 6, height - border_inset - 6)],
        outline=(234, 88, 12),
        width=2
    )

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    draw.text((border_inset + 20, border_inset + 18), f"ACT // PANEL {panel_num} [{art_style.upper()[:16]}]", fill=(255, 255, 255), font=font)
    prompt_short = prompt[:76] + ("..." if len(prompt) > 76 else "")
    draw.text((border_inset + 18, height - border_inset - 26), f">> SCENE: {prompt_short}", fill=(203, 213, 225), font=font)

    return img


def generate_comic_panels(panels_data: List[Dict[str, Any]], art_style: str = "Comic Book Classic") -> List[str]:
    """
    Master Batch Comic Panel Generator:
    Generates real, distinct AI comic illustrations for ALL panels in parallel.
    Uses AI Horde distributed Stable Diffusion with staggered queueing and async polling,
    falling back to Pollinations or graphic novel canvas per panel.
    """
    ensure_panels_directory()
    session = requests.Session()
    image_paths: List[str] = ["" for _ in range(len(panels_data))]
    task_queue: List[Tuple[int, str, str, str]] = []  # (index, panel_num, task_id, filename)

    logger.info("Starting batch AI image generation for %s comic panels...", len(panels_data))

    # Step 1: Queue panels in AI Horde with gentle 2.0s stagger to prevent anonymous 429
    for i, panel in enumerate(panels_data):
        p_num = panel.get("panel", i + 1)
        p_prompt = panel.get("prompt", f"Heroic comic scene, panel {p_num}")
        filename = sanitize_filename(p_prompt, panel_num=p_num)
        enhanced_prompt = _build_enhanced_prompt(p_prompt, art_style)

        task_id = _submit_horde_task(enhanced_prompt, session)
        if task_id:
            logger.info("Panel %s queued on AI Horde (task: %s)", p_num, task_id)
            task_queue.append((i, p_num, task_id, filename))
            time.sleep(2.0)
        else:
            logger.warning("Could not queue Panel %s on AI Horde; will use fast fallback.", p_num)

    # Step 2: Poll queued tasks concurrently
    completed_indices = set()
    poll_start = time.time()
    max_poll_seconds = 65

    while len(completed_indices) < len(task_queue) and (time.time() - poll_start) < max_poll_seconds:
        time.sleep(2.5)
        for i, p_num, t_id, filename in task_queue:
            if i in completed_indices:
                continue
            try:
                check_res = session.get(f"{HORDE_API_URL}/check/{t_id}", headers=HORDE_HEADERS, timeout=8)
                if check_res.status_code == 200 and check_res.json().get("done"):
                    img = _fetch_horde_image(t_id, session)
                    if img:
                        out_path = os.path.join(STATIC_PANELS_DIR, filename)
                        img.save(out_path, format="PNG")
                        image_paths[i] = f"/static/panels/{filename}"
                        completed_indices.add(i)
                        logger.info("Panel %s generated and saved successfully (%sx%s)", p_num, img.width, img.height)
            except Exception as e:
                logger.debug("Error checking Horde task %s: %s", t_id, e)

    # Step 3: Handle any panels that timed out or failed Horde queueing
    for i, panel in enumerate(panels_data):
        if image_paths[i]:
            continue

        p_num = panel.get("panel", i + 1)
        p_prompt = panel.get("prompt", f"Heroic comic scene, panel {p_num}")
        filename = sanitize_filename(p_prompt, panel_num=p_num)
        out_path = os.path.join(STATIC_PANELS_DIR, filename)

        logger.info("Resolving Panel %s with secondary tier generator...", p_num)
        img = _generate_via_pollinations(p_prompt, art_style, p_num)
        if img is None:
            logger.info("Using graphic novel canvas renderer for Panel %s...", p_num)
            img = _render_stylized_comic_art(p_prompt, art_style, p_num)

        img.save(out_path, format="PNG")
        image_paths[i] = f"/static/panels/{filename}"
        logger.info("Saved Panel %s to %s", p_num, out_path)

    return image_paths


def generate_image(prompt: str, art_style: str = "comic book", panel_num: int = 1) -> str:
    """
    Generates a single comic illustration based on the provided prompt and art style.
    Used for single-panel tests and standalone queries.
    """
    ensure_panels_directory()
    filename = sanitize_filename(prompt, panel_num=panel_num)
    file_path = os.path.join(STATIC_PANELS_DIR, filename)
    session = requests.Session()

    # 1. Primary: AI Horde
    enhanced_prompt = _build_enhanced_prompt(prompt, art_style)
    task_id = _submit_horde_task(enhanced_prompt, session)
    if task_id:
        poll_start = time.time()
        while (time.time() - poll_start) < 30:
            time.sleep(2.5)
            try:
                check_res = session.get(f"{HORDE_API_URL}/check/{task_id}", headers=HORDE_HEADERS, timeout=8)
                if check_res.status_code == 200 and check_res.json().get("done"):
                    img = _fetch_horde_image(task_id, session)
                    if img:
                        img.save(file_path, format="PNG")
                        logger.info("Single Panel %s generated via AI Horde and saved.", panel_num)
                        return f"/static/panels/{filename}"
            except Exception as e:
                logger.debug("Horde check error: %s", e)

    # 2. Secondary: Pollinations
    img = _generate_via_pollinations(prompt=prompt, art_style=art_style, panel_num=panel_num)

    # 3. Tertiary: Stylized graphic renderer
    if img is None:
        img = _render_stylized_comic_art(prompt=prompt, art_style=art_style, panel_num=panel_num)

    img.save(file_path, format="PNG")
    logger.info("Saved single comic panel %s to %s", panel_num, file_path)
    return f"/static/panels/{filename}"
