import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import exifread
import hachoir.metadata
import hachoir.parser
from PIL import Image

# Application Metadata
APP_NAME = "Image Metadata Extractor"
VERSION = "1.0.0"
PUBLISHER = "SrJ Solutions"

def extract_image_metadata(image_path):
    """Extracts detailed metadata from an image (JPEG, PNG, etc.)"""
    metadata = {
        "File Name": os.path.basename(image_path),
        "File Size (bytes)": os.path.getsize(image_path),
        "Creation Time": time.ctime(os.path.getctime(image_path)),
        "Modification Time": time.ctime(os.path.getmtime(image_path)),
    }

    try:
        with Image.open(image_path) as img:
            metadata["Format"] = img.format
            metadata["Mode"] = img.mode
            metadata["Size (pixels)"] = f"{img.width}x{img.height}"
            metadata["Bit Depth"] = img.bits if hasattr(img, "bits") else "Unknown"
            metadata["Compression"] = img.info.get("compression", "None")
            metadata["ICC Profile"] = "Present" if img.info.get("icc_profile") else "None"
    except Exception as e:
        metadata["PIL Error"] = str(e)

    if not image_path.lower().endswith('.heic'):
        metadata.update(extract_exif_metadata(image_path))

    metadata.update(extract_hidden_metadata(image_path))
    return metadata

def extract_exif_metadata(image_path):
    """Extracts EXIF metadata including GPS, Camera Model, etc."""
    metadata = {}

    with open(image_path, "rb") as img_file:
        tags = exifread.process_file(img_file, details=True)

        for tag, value in tags.items():
            metadata[tag] = str(value)

        gps_lat = tags.get("GPS GPSLatitude")
        gps_lon = tags.get("GPS GPSLongitude")
        lat_ref = tags.get("GPS GPSLatitudeRef")
        lon_ref = tags.get("GPS GPSLongitudeRef")

        if gps_lat and gps_lon and lat_ref and lon_ref:
            latitude = convert_gps(gps_lat, str(lat_ref))
            longitude = convert_gps(gps_lon, str(lon_ref))
            metadata["GPS Coordinates"] = f"{latitude}, {longitude}"

        metadata["Camera Model"] = tags.get("Image Model", "Unknown")
        metadata["Software"] = tags.get("Image Software", "Unknown")

    return metadata

def convert_gps(value, ref):
    """Convert GPS coordinates to decimal degrees"""
    def convert_to_degrees(values):
        if not isinstance(values, list):
            values = list(values.values)
        d, m, s = [float(v.num) / float(v.den) for v in values]
        return d + (m / 60.0) + (s / 3600.0)

    degrees = convert_to_degrees(value)
    if ref in ["S", "W"]:
        degrees = -degrees
    return degrees

def extract_hidden_metadata(file_path):
    """Extracts deep hidden metadata using hachoir"""
    metadata = {}

    try:
        parser = hachoir.parser.createParser(file_path)
        if not parser:
            return {"Hidden Metadata": "Unable to parse"}

        metadata_extractor = hachoir.metadata.extractMetadata(parser)
        if metadata_extractor:
            for item in metadata_extractor.exportPlaintext():
                key, value = item.split(": ", 1) if ": " in item else (item, "Unknown")
                metadata[key] = value

    except Exception as e:
        metadata["Hidden Metadata Error"] = str(e)

    return metadata

def save_metadata_to_file(metadata, output_file="metadata.txt"):
    """Saves metadata to a Notepad file"""
    with open(output_file, "w", encoding="utf-8") as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")
    
    os.startfile(output_file)

def browse_file():
    """Opens file dialog to select an image"""
    file_path = filedialog.askopenfilename(
        title="Select an Image",
        filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.tiff;*.bmp;*.gif;*.webp;*.heic")]
    )

    if file_path:
        metadata = extract_image_metadata(file_path)
        save_metadata_to_file(metadata)

def about_app():
    """Displays about information"""
    messagebox.showinfo(APP_NAME, f"{APP_NAME}\nVersion: {VERSION}\nPublisher: {PUBLISHER}")

def create_gui():
    """Creates the main GUI"""
    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("400x200")
    root.resizable(False, False)

    label = tk.Label(root, text=f"{APP_NAME}", font=("Arial", 14, "bold"))
    label.pack(pady=10)

    browse_button = tk.Button(root, text="Select Image", command=browse_file, font=("Arial", 12))
    browse_button.pack(pady=10)

    about_button = tk.Button(root, text="About", command=about_app, font=("Arial", 10))
    about_button.pack(pady=5)

    exit_button = tk.Button(root, text="Exit", command=root.quit, font=("Arial", 10))
    exit_button.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
