from pathlib import Path

from PIL import Image, ImageOps, ImageFilter
import numpy as np


def prepare_image(
    input_path: Path,
    m: int,
    red_rgb255 : tuple,  
    green_rgb255: tuple,  
    output_path: Path | None = None,
    ori: int | None = None 
) -> dict:
    """
    Preparing an image to be displayed in a DCM experiment as folows:
    1. Loading image on a transparent or white background.
    2. Making visible pixels grayscale, background white (temporaly colors).
    3. Stretching to fit m×m square.
    4. Applying Gaussian smoothing with a specified radius.
    5. Dithering to black & white
    6. Repainting white to color_background, black to color_object.

    If ori is not None, the relative size of the stimulus on the background would be normalized to allow 
        the full display of the stimulus with all possible degrees of rotation. 
    """

    stim: Image = Image.open(input_path).convert("RGBA")
    _r, _g, _b, alpha = stim.split()

    stim= stim.convert("L")  # to graysclale
    white_bg = Image.new("L", stim.size, 255)
    img = Image.composite(stim, white_bg, alpha)

    if ori is not None:
        m_normalized = int(m/np.sqrt(2))
        img = img.resize((m_normalized, m_normalized), Image.Resampling.LANCZOS)
        offset = ((m - m_normalized)//2, (m-m_normalized)//2)

        canvas = Image.new("L", (m,m), 255)
        canvas.paste(img, offset)
        canvas = canvas.rotate(ori, expand = False, fillcolor = 255)
    elif ori is None:
        img = img.resize((m, m), Image.Resampling.LANCZOS)
        canvas = img

    blur_radius = round(m/20)
    filter_for_blurring = ImageFilter.GaussianBlur(blur_radius)
    canvas = canvas.filter(filter_for_blurring)

    bw = canvas.convert("1")  # dithering
    #print("A", bw.size)

    red_bg_image = ImageOps.colorize(
        bw.convert("L"),
        black=green_rgb255,
        white=red_rgb255,
    )
    green_bg_image = ImageOps.colorize(
        bw.convert("L"),
        black=red_rgb255,
        white=green_rgb255,
    )

    stim_images = {"red" : red_bg_image, "green" : green_bg_image}
    #saving an example of final image 
    if output_path is not None:
        green_bg_image.save(output_path)

    return stim_images


if __name__ == "__main__":
    prepare_image(
        input_path=Path("stimuli") / "gabor.png",
        output_path=Path("output.png"),
        m=175,
        red_rgb255=(150, 110, 0),
        green_rgb255=(110, 150, 0),
        ori = 0
    )