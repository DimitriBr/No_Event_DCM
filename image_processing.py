from PIL import Image, ImageOps, ImageFilter


def prepare_image(
    input_path: str,
    output_path: str,
    m: int,
    blur_radius: float,
    new_background_color_rgb255=(255, 255, 255),  # "white" replacement
    new_object_color_rgb255=(0, 0, 0),  # "black" replacement
):
    """
    Preparing an image to be displayed in a DCM experiment as folows:
    1. Loading image on a transparent or white background.
    2. Making visible pixels grayscale, background white (temporaly colors).
    3. Stretching to fit m×m square.
    4. Applying Gaussian smoothing with a specified radius.
    5. Dithering to black & white.
    6. Repainting white to color_background, black to color_object.
    """

    img = Image.open(input_path).convert("RGBA")
    r, g, b, alpha = img.split()

    gray = img.convert("L") # to graysclae
    white_canvas = Image.new("L", img.size, 255) 
    img_composite = Image.composite(gray, white_canvas, alpha)  # alpha as transparency mask

    img_resized = img_composite.resize((m, m), Image.Resampling.LANCZOS)

    filter_for_blurring = ImageFilter.GaussianBlur(blur_radius)
    img_blurred = img_resized.filter(filter_for_blurring)

    bw = img_blurred.convert("1")  # dithering

    final_image = ImageOps.colorize(
        bw.convert("L"), white=new_background_color_rgb255, black=new_object_color_rgb255
    )

    final_image.save(output_path)


if __name__ == "__main__":
    prepare_image(
        input_path="gabor.png",
        output_path="output.png",
        m=175,
        blur_radius=2,
        new_background_color_rgb255=(150, 110, 0),
        new_object_color_rgb255=(110, 150, 0),
    )
