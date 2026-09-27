import os
from app.image_generator import generate_image, sanitize_filename


def test_sanitize_filename():
    raw_prompt = "A Brave Fox, in an ENCHANTED Forest! @#$%"
    filename = sanitize_filename(raw_prompt, panel_num=2)
    assert filename.startswith("panel_2_")
    assert filename.endswith(".png")
    assert "@" not in filename
    assert "#" not in filename


def test_generate_image_creates_file():
    prompt = "Rusty leaping over glowing crystal stream, comic style"
    image_url = generate_image(prompt=prompt, art_style="comic book", panel_num=1)

    assert image_url.startswith("/static/panels/")
    assert image_url.endswith(".png")

    local_path = image_url.lstrip("/")
    assert os.path.exists(local_path)
    assert os.path.getsize(local_path) > 1000  # valid image file generated
