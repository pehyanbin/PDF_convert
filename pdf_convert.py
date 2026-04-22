import os
import sys
from pathlib import Path
from PIL import Image


def validate_image(image_path: str) -> bool:
    """Validate if the file exists and is a valid image."""
    path = Path(image_path)

    if not path.exists():
        print(f"❌ Error: File '{image_path}' does not exist.")
        return False

    if not path.is_file():
        print(f"❌ Error: '{image_path}' is not a file.")
        return False

    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    if path.suffix.lower() not in valid_extensions:
        print(f"❌ Error: '{image_path}' is not a supported image format.")
        print(f"   Supported formats: {', '.join(valid_extensions)}")
        return False

    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"❌ Error: '{image_path}' is not a valid image file. {e}")
        return False


def prepare_image(image_path: str) -> Image.Image:
    """Open and prepare an image for PDF conversion."""
    img = Image.open(image_path)

    # Convert to RGB if necessary (PDF doesn't support transparency or palette modes)
    if img.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            background.paste(img, mask=img.split()[-1])
        else:
            background.paste(img)
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    return img


def convert_single_image_to_pdf(image_path: str, output_path: str = None) -> bool:
    """
    Convert a single image file to a PDF file.

    Args:
        image_path: Path to the input image file.
        output_path: Path to the output PDF file (optional).

    Returns:
        True if conversion was successful, False otherwise.
    """
    if not validate_image(image_path):
        return False

    # Generate output path if not provided
    if output_path is None:
        output_path = str(Path(image_path).with_suffix(".pdf"))

    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        img = prepare_image(image_path)
        img.save(output_path, "PDF", resolution=100.0)
        print(f"✅ Successfully converted '{image_path}' to '{output_path}'")
        return True
    except Exception as e:
        print(f"❌ Error converting '{image_path}' to PDF: {e}")
        return False


def convert_multiple_images_to_one_pdf(
    image_paths: list, output_path: str
) -> bool:
    """
    Convert multiple image files into a single PDF file.

    Args:
        image_paths: List of paths to the input image files.
        output_path: Path to the output PDF file.

    Returns:
        True if conversion was successful, False otherwise.
    """
    if not image_paths:
        print("❌ Error: No image paths provided.")
        return False

    # Validate all images first
    print("🔍 Validating images...")
    valid_images = []
    for image_path in image_paths:
        if validate_image(image_path):
            valid_images.append(image_path)

    if not valid_images:
        print("❌ Error: No valid images found.")
        return False

    if len(valid_images) < len(image_paths):
        print(
            f"⚠️  Warning: {len(image_paths) - len(valid_images)} invalid image(s) will be skipped."
        )

    # Ensure the output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        print(f"🔄 Converting {len(valid_images)} image(s) to one PDF...")

        images = [prepare_image(img_path) for img_path in valid_images]

        # Save first image and append the rest
        first_image = images[0]
        remaining_images = images[1:]

        if remaining_images:
            first_image.save(
                output_path,
                "PDF",
                resolution=100.0,
                save_all=True,
                append_images=remaining_images,
            )
        else:
            first_image.save(output_path, "PDF", resolution=100.0)

        print(f"✅ Successfully converted {len(valid_images)} image(s) to '{output_path}'")
        print(f"   Images included:")
        for i, img_path in enumerate(valid_images, 1):
            print(f"   {i}. {img_path}")

        return True
    except Exception as e:
        print(f"❌ Error converting images to PDF: {e}")
        return False


def convert_multiple_images_to_multiple_pdfs(
    image_paths: list, output_dir: str = None, prefix: str = ""
) -> dict:
    """
    Convert multiple image files into separate PDF files.

    Args:
        image_paths: List of paths to the input image files.
        output_dir: Directory where the PDF files will be saved (optional).
        prefix: Prefix to add to the output PDF file names (optional).

    Returns:
        Dictionary with image paths as keys and success status as values.
    """
    if not image_paths:
        print("❌ Error: No image paths provided.")
        return {}

    results = {}
    success_count = 0
    fail_count = 0

    print(f"🔄 Converting {len(image_paths)} image(s) to separate PDFs...")

    for image_path in image_paths:
        # Generate output path
        img_path = Path(image_path)

        if output_dir:
            out_dir = Path(output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            pdf_filename = f"{prefix}{img_path.stem}.pdf"
            output_path = str(out_dir / pdf_filename)
        else:
            pdf_filename = f"{prefix}{img_path.stem}.pdf"
            output_path = str(img_path.parent / pdf_filename)

        # Convert the image
        success = convert_single_image_to_pdf(image_path, output_path)
        results[image_path] = success

        if success:
            success_count += 1
        else:
            fail_count += 1

    # Print summary
    print("\n📊 Conversion Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {fail_count}")
    print(f"   📁 Total: {len(image_paths)}")

    return results


def get_images_from_directory(directory: str) -> list:
    """Get all image files from a directory."""
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}
    dir_path = Path(directory)

    if not dir_path.exists() or not dir_path.is_dir():
        print(f"❌ Error: '{directory}' is not a valid directory.")
        return []

    image_files = [
        str(f)
        for f in sorted(dir_path.iterdir())
        if f.is_file() and f.suffix.lower() in valid_extensions
    ]

    return image_files


def print_menu():
    """Print the main menu."""
    print("\n" + "=" * 55)
    print("          🖼️  Image to PDF Converter  📄")
    print("=" * 55)
    print("1. Convert one image to PDF")
    print("2. Convert multiple images into one PDF")
    print("3. Convert multiple images into multiple PDFs")
    print("4. Convert all images in a folder to one PDF")
    print("5. Convert all images in a folder to multiple PDFs")
    print("0. Exit")
    print("=" * 55)


def get_image_paths_from_user() -> list:
    """Get multiple image paths from the user."""
    print("Enter image paths (one per line).")
    print("Press Enter twice when done:\n")
    image_paths = []

    while True:
        path = input("Image path: ").strip()
        if not path:
            if image_paths:
                break
            else:
                print("⚠️  Please enter at least one image path.")
        else:
            image_paths.append(path)

    return image_paths


def handle_single_conversion():
    """Handle single image to PDF conversion."""
    print("\n--- Convert Single Image to PDF ---")
    image_path = input("Enter image path: ").strip()

    use_custom_output = input("Use custom output path? (y/n): ").strip().lower()
    output_path = None

    if use_custom_output == "y":
        output_path = input("Enter output PDF path: ").strip()
        if not output_path.endswith(".pdf"):
            output_path += ".pdf"

    convert_single_image_to_pdf(image_path, output_path)


def handle_multiple_to_one():
    """Handle multiple images to one PDF conversion."""
    print("\n--- Convert Multiple Images to One PDF ---")
    image_paths = get_image_paths_from_user()

    output_path = input("\nEnter output PDF path: ").strip()
    if not output_path.endswith(".pdf"):
        output_path += ".pdf"

    convert_multiple_images_to_one_pdf(image_paths, output_path)


def handle_multiple_to_multiple():
    """Handle multiple images to multiple PDFs conversion."""
    print("\n--- Convert Multiple Images to Multiple PDFs ---")
    image_paths = get_image_paths_from_user()

    use_custom_dir = input("\nSave to a specific directory? (y/n): ").strip().lower()
    output_dir = None
    prefix = ""

    if use_custom_dir == "y":
        output_dir = input("Enter output directory: ").strip()

    use_prefix = input("Add a prefix to PDF names? (y/n): ").strip().lower()
    if use_prefix == "y":
        prefix = input("Enter prefix: ").strip()

    convert_multiple_images_to_multiple_pdfs(image_paths, output_dir, prefix)


def handle_folder_to_one():
    """Handle converting all images in a folder to one PDF."""
    print("\n--- Convert Folder Images to One PDF ---")
    folder_path = input("Enter folder path: ").strip()

    image_paths = get_images_from_directory(folder_path)
    if not image_paths:
        print("❌ No images found in the specified folder.")
        return

    print(f"\n📂 Found {len(image_paths)} image(s):")
    for i, img in enumerate(image_paths, 1):
        print(f"   {i}. {img}")

    output_path = input("\nEnter output PDF path: ").strip()
    if not output_path.endswith(".pdf"):
        output_path += ".pdf"

    convert_multiple_images_to_one_pdf(image_paths, output_path)


def handle_folder_to_multiple():
    """Handle converting all images in a folder to multiple PDFs."""
    print("\n--- Convert Folder Images to Multiple PDFs ---")
    folder_path = input("Enter folder path: ").strip()

    image_paths = get_images_from_directory(folder_path)
    if not image_paths:
        print("❌ No images found in the specified folder.")
        return

    print(f"\n📂 Found {len(image_paths)} image(s):")
    for i, img in enumerate(image_paths, 1):
        print(f"   {i}. {img}")

    use_custom_dir = input("\nSave PDFs to a specific directory? (y/n): ").strip().lower()
    output_dir = None
    prefix = ""

    if use_custom_dir == "y":
        output_dir = input("Enter output directory: ").strip()
    else:
        output_dir = folder_path  # Save in the same folder

    use_prefix = input("Add a prefix to PDF names? (y/n): ").strip().lower()
    if use_prefix == "y":
        prefix = input("Enter prefix: ").strip()

    convert_multiple_images_to_multiple_pdfs(image_paths, output_dir, prefix)


def main():
    """Main function to run the image to PDF converter."""
    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("❌ Error: Pillow library is not installed.")
        print("   Install it using: pip install Pillow")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            handle_single_conversion()
        elif choice == "2":
            handle_multiple_to_one()
        elif choice == "3":
            handle_multiple_to_multiple()
        elif choice == "4":
            handle_folder_to_one()
        elif choice == "5":
            handle_folder_to_multiple()
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n⚠️  Invalid choice. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()