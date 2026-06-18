#!/usr/bin/env python3
"""
Generate a simple app icon for MarkItDown Desktop.
Creates a multi-resolution .ico file in the assets/ directory.

On Windows, this uses tkinter for rendering. Falls back to PIL if available.
"""
import os
import struct
import zlib

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def create_ico_from_bmp_data(sizes, output_path):
    """Create a minimal .ico file from raw pixel data."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    entries = []
    image_data_list = []

    for size in sizes:
        # Create a simple gradient icon with "M" letterform
        pixels = _render_icon(size)
        bmp_data = _create_bmp_data(size, pixels)
        image_data_list.append(bmp_data)
        entries.append({
            'width': size if size < 256 else 0,
            'height': size if size < 256 else 0,
            'bpp': 32,
            'data_size': len(bmp_data),
        })

    # ICO header
    header = struct.pack('<HHH', 0, 1, len(entries))

    # Calculate offsets
    offset = 6 + 16 * len(entries)  # Header + directory entries
    dir_entries = b''
    for i, entry in enumerate(entries):
        dir_entries += struct.pack(
            '<BBBBHHII',
            entry['width'], entry['height'],
            0,  # color palette
            0,  # reserved
            1,  # color planes
            entry['bpp'],
            entry['data_size'],
            offset,
        )
        offset += entry['data_size']

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(dir_entries)
        for data in image_data_list:
            f.write(data)

    print(f"  Icon created: {output_path}")


def _render_icon(size):
    """Render a gradient icon with 'M' letter as RGBA pixel array."""
    pixels = []
    for y in range(size):
        row = []
        for x in range(size):
            # Normalized coordinates
            nx = x / (size - 1)
            ny = y / (size - 1)

            # Background: dark gradient
            r = int(13 + nx * 20)
            g = int(17 + ny * 15)
            b = int(23 + nx * 30 + ny * 20)

            # Round corners
            cx, cy = nx - 0.5, ny - 0.5
            corner_radius = 0.35
            if abs(cx) > corner_radius and abs(cy) > corner_radius:
                dx = abs(cx) - corner_radius
                dy = abs(cy) - corner_radius
                if (dx * dx + dy * dy) > (0.5 - corner_radius) ** 2:
                    row.append((0, 0, 0, 0))
                    continue

            # Border glow
            dist_from_edge = min(nx, 1 - nx, ny, 1 - ny)
            if dist_from_edge < 0.08:
                glow = (0.08 - dist_from_edge) / 0.08
                r = int(r + glow * 40)
                g = int(g + glow * 60)
                b = int(b + glow * 100)

            # Draw "M" letter
            margin = 0.2
            if margin <= nx <= (1 - margin) and margin <= ny <= (1 - margin):
                lnx = (nx - margin) / (1 - 2 * margin)
                lny = (ny - margin) / (1 - 2 * margin)

                is_letter = False

                # Left vertical stroke
                if lnx < 0.2:
                    is_letter = True
                # Right vertical stroke
                elif lnx > 0.8:
                    is_letter = True
                # Left diagonal
                elif lny < (lnx * 1.5) and lny > ((lnx - 0.2) * 1.5) and lnx < 0.55:
                    is_letter = True
                # Right diagonal
                elif lny < ((1 - lnx) * 1.5) and lny > ((0.8 - lnx) * 1.5) and lnx > 0.45:
                    is_letter = True

                if is_letter:
                    # Gradient on the letter: blue to green
                    r = int(35 + lnx * 20)
                    g = int(134 + lnx * 51)
                    b = int(54 + (1 - lnx) * 200)

            row.append((min(255, r), min(255, g), min(255, b), 255))
        pixels.append(row)
    return pixels


def _create_bmp_data(size, pixels):
    """Create BMP info header + pixel data for ICO entry."""
    # BITMAPINFOHEADER
    header = struct.pack(
        '<IiiHHIIiiII',
        40,          # biSize
        size,        # biWidth
        size * 2,    # biHeight (doubled for ICO: includes AND mask)
        1,           # biPlanes
        32,          # biBitCount
        0,           # biCompression (BI_RGB)
        0,           # biSizeImage
        0,           # biXPelsPerMeter
        0,           # biYPelsPerMeter
        0,           # biClrUsed
        0,           # biClrImportant
    )

    # Pixel data (bottom-up, BGRA)
    pixel_data = b''
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = pixels[y][x]
            pixel_data += struct.pack('BBBB', b, g, r, a)

    # AND mask (all zeros = fully opaque, handled by alpha)
    and_mask = b'\x00' * (((size + 31) // 32) * 4 * size)

    return header + pixel_data + and_mask


if __name__ == '__main__':
    output = os.path.join(ASSETS_DIR, 'icon.ico')
    create_ico_from_bmp_data([16, 32, 48, 64, 128, 256], output)
    print("  Done!")
