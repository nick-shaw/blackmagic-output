"""
Test RGB to YUV conversion with different range parameters.

These tests verify color conversion accuracy for known reference values
and serve as regression tests during refactoring.
"""

import numpy as np
import pytest

try:
    from blackmagic_io import rgb_uint16_to_yuv10, rgb_float_to_yuv10, Gamut
    CONVERSIONS_AVAILABLE = True
except ImportError:
    CONVERSIONS_AVAILABLE = False


def unpack_v210_pixel(v210_buffer, pixel_index, width):
    """
    Unpack a single pixel's Y, Cb, Cr values from v210 format.

    This unpacking logic matches pixel_reader.cpp exactly.

    v210 packs 6 pixels into 4 DWORDs (16 bytes):
    - DWORD 0: U0[9:0] Y0[9:0] V0[9:0] (bits [9:0] U0, [19:10] Y0, [29:20] V0)
    - DWORD 1: Y1[9:0] U1[9:0] Y2[9:0] (bits [9:0] Y1, [19:10] U1, [29:20] Y2)
    - DWORD 2: V1[9:0] Y3[9:0] U2[9:0] (bits [9:0] V1, [19:10] Y3, [29:20] U2)
    - DWORD 3: Y4[9:0] V2[9:0] Y5[9:0] (bits [9:0] Y4, [19:10] V2, [29:20] Y5)

    Returns: (Y, Cb, Cr) as 10-bit values (0-1023)
    """
    dwords = np.frombuffer(v210_buffer, dtype=np.uint32)

    group_index = (pixel_index // 6) * 4
    pixel_in_group = pixel_index % 6

    d0 = dwords[group_index]
    d1 = dwords[group_index + 1]
    d2 = dwords[group_index + 2]
    d3 = dwords[group_index + 3]

    if pixel_in_group == 0:
        y = (d0 >> 10) & 0x3FF
        cb = d0 & 0x3FF
        cr = (d0 >> 20) & 0x3FF
    elif pixel_in_group == 1:
        y = d1 & 0x3FF
        cb = d0 & 0x3FF
        cr = (d0 >> 20) & 0x3FF
    elif pixel_in_group == 2:
        y = (d1 >> 20) & 0x3FF
        cb = (d1 >> 10) & 0x3FF
        cr = d2 & 0x3FF
    elif pixel_in_group == 3:
        y = (d2 >> 10) & 0x3FF
        cb = (d1 >> 10) & 0x3FF
        cr = d2 & 0x3FF
    elif pixel_in_group == 4:
        y = d3 & 0x3FF
        cb = (d2 >> 20) & 0x3FF
        cr = (d3 >> 10) & 0x3FF
    else:  # pixel_in_group == 5
        y = (d3 >> 20) & 0x3FF
        cb = (d2 >> 20) & 0x3FF
        cr = (d3 >> 10) & 0x3FF

    return (y, cb, cr)


@pytest.mark.skipif(not CONVERSIONS_AVAILABLE, reason="Conversion functions not available")
class TestRGBtoYUVConversions:
    """Test RGB to YUV conversions with known reference values."""

    def test_uint16_black_narrow_range_rec709(self):
        """Test black (0,0,0) converts to Y=64, Cb=512, Cr=512 in narrow range."""
        width, height = 12, 2
        rgb = np.zeros((height, width, 3), dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 64, f"Expected Y=64 for black, got {y}"
        assert cb == 512, f"Expected Cb=512 for black, got {cb}"
        assert cr == 512, f"Expected Cr=512 for black, got {cr}"

    def test_uint16_white_narrow_range_rec709(self):
        """Test white (65535,65535,65535) converts to Y=940, Cb=512, Cr=512 in narrow range."""
        width, height = 12, 2
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 940, f"Expected Y=940 for white, got {y}"
        assert cb == 512, f"Expected Cb=512 for white, got {cb}"
        assert cr == 512, f"Expected Cr=512 for white, got {cr}"

    def test_uint16_mid_gray_narrow_range_rec709(self):
        """Test mid-gray (32768,32768,32768) converts to approximately Y=502, Cb=512, Cr=512."""
        width, height = 12, 2
        rgb = np.full((height, width, 3), 32768, dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert 500 <= y <= 504, f"Expected Y≈502 for mid-gray, got {y}"
        assert 510 <= cb <= 514, f"Expected Cb≈512 for mid-gray, got {cb}"
        assert 510 <= cr <= 514, f"Expected Cr≈512 for mid-gray, got {cr}"

    def test_float_black_narrow_range_rec709(self):
        """Test black (0.0,0.0,0.0) converts to Y=64, Cb=512, Cr=512 in narrow range."""
        width, height = 12, 2
        rgb = np.zeros((height, width, 3), dtype=np.float32)

        yuv_buffer = rgb_float_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 64, f"Expected Y=64 for black, got {y}"
        assert cb == 512, f"Expected Cb=512 for black, got {cb}"
        assert cr == 512, f"Expected Cr=512 for black, got {cr}"

    def test_float_white_narrow_range_rec709(self):
        """Test white (1.0,1.0,1.0) converts to Y=940, Cb=512, Cr=512 in narrow range."""
        width, height = 12, 2
        rgb = np.ones((height, width, 3), dtype=np.float32)

        yuv_buffer = rgb_float_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 940, f"Expected Y=940 for white, got {y}"
        assert cb == 512, f"Expected Cb=512 for white, got {cb}"
        assert cr == 512, f"Expected Cr=512 for white, got {cr}"

    def test_float_mid_gray_narrow_range_rec709(self):
        """Test mid-gray (0.5,0.5,0.5) converts to approximately Y=502, Cb=512, Cr=512."""
        width, height = 12, 2
        rgb = np.full((height, width, 3), 0.5, dtype=np.float32)

        yuv_buffer = rgb_float_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert 500 <= y <= 504, f"Expected Y≈502 for mid-gray, got {y}"
        assert 510 <= cb <= 514, f"Expected Cb≈512 for mid-gray, got {cb}"
        assert 510 <= cr <= 514, f"Expected Cr≈512 for mid-gray, got {cr}"

    def test_uint16_red_narrow_range_rec709(self):
        """Test pure red converts correctly with Rec.709 matrix."""
        width, height = 12, 2
        rgb = np.zeros((height, width, 3), dtype=np.uint16)
        rgb[:, :, 0] = 65535

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        # For pure red (R=1, G=0, B=0) with Rec.709:
        # Y = 0.2126, Cb = -0.1146, Cr = 0.5000
        expected_y = int(0.2126 * 876 + 64)
        expected_cb = int((-0.1146 + 0.5) * 896 + 64)
        expected_cr = int((0.5 + 0.5) * 896 + 64)

        assert abs(y - expected_y) <= 2, f"Expected Y≈{expected_y} for red, got {y}"
        assert abs(cb - expected_cb) <= 2, f"Expected Cb≈{expected_cb} for red, got {cb}"
        assert abs(cr - expected_cr) <= 2, f"Expected Cr≈{expected_cr} for red, got {cr}"


    def test_uint16_white_full_range_yuv_rec709(self):
        """Test white converts to Y=1023, Cb=512, Cr=512 in full range YUV."""
        width, height = 12, 2
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709,
                                         input_narrow_range=False, output_narrow_range=False)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 1023, f"Expected Y=1023 for white full range, got {y}"
        assert cb == 512, f"Expected Cb=512 for white, got {cb}"
        assert cr == 512, f"Expected Cr=512 for white, got {cr}"

    def test_uint16_black_full_range_yuv_rec709(self):
        """Test black converts to Y=0, Cb=512, Cr=512 in full range YUV."""
        width, height = 12, 2
        rgb = np.zeros((height, width, 3), dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709,
                                         input_narrow_range=False, output_narrow_range=False)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 0, f"Expected Y=0 for black full range, got {y}"
        assert cb == 512, f"Expected Cb=512 for black, got {cb}"
        assert cr == 512, f"Expected Cr=512 for black, got {cr}"

    def test_uint16_narrow_input_to_narrow_output(self):
        """Test narrow range RGB input (64-940 @10-bit) to narrow range YUV."""
        width, height = 12, 2
        # White in narrow range: 940 @ 10-bit = 60160 @ 16-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709,
                                         input_narrow_range=True, output_narrow_range=True)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 940, f"Expected Y=940 for narrow white, got {y}"
        assert cb == 512, f"Expected Cb=512 for narrow white, got {cb}"
        assert cr == 512, f"Expected Cr=512 for narrow white, got {cr}"

    def test_uint16_narrow_input_to_full_output(self):
        """Test narrow range RGB input to full range YUV output."""
        width, height = 12, 2
        # White in narrow range: 940 @ 10-bit = 60160 @ 16-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        yuv_buffer = rgb_uint16_to_yuv10(rgb, width, height, Gamut.Rec709,
                                         input_narrow_range=True, output_narrow_range=False)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 1023, f"Expected Y=1023 for narrow input to full output, got {y}"
        assert cb == 512, f"Expected Cb=512, got {cb}"
        assert cr == 512, f"Expected Cr=512, got {cr}"

    def test_float_white_full_range_yuv_rec709(self):
        """Test float white converts to full range YUV (Y=1023, Cb=512, Cr=512)."""
        width, height = 12, 2
        rgb = np.ones((height, width, 3), dtype=np.float32)

        yuv_buffer = rgb_float_to_yuv10(rgb, width, height, Gamut.Rec709, output_narrow_range=False)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 1023, f"Expected Y=1023 for white full range, got {y}"
        assert cb == 512, f"Expected Cb=512 for white, got {cb}"
        assert cr == 512, f"Expected Cr=512 for white, got {cr}"

    def test_float_black_full_range_yuv_rec709(self):
        """Test float black converts to full range YUV (Y=0, Cb=512, Cr=512)."""
        width, height = 12, 2
        rgb = np.zeros((height, width, 3), dtype=np.float32)

        yuv_buffer = rgb_float_to_yuv10(rgb, width, height, Gamut.Rec709, output_narrow_range=False)

        y, cb, cr = unpack_v210_pixel(yuv_buffer, 0, width)

        assert y == 0, f"Expected Y=0 for black full range, got {y}"
        assert cb == 512, f"Expected Cb=512 for black, got {cb}"
        assert cr == 512, f"Expected Cr=512 for black, got {cr}"


@pytest.mark.skipif(not CONVERSIONS_AVAILABLE, reason="Conversion functions not available")
class TestRGBtoRGB10Conversions:
    """Test RGB to RGB10 conversions with different range parameters."""

    def test_uint16_to_rgb10_narrow_to_narrow(self):
        """Test narrow range uint16 to narrow range RGB10 (default behavior - bit shift)."""
        width, height = 12, 2
        # Narrow range white: 940 @ 10-bit = 60160 @ 16-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb10

        rgb10_buffer = rgb_uint16_to_rgb10(rgb, width, height)

        # Unpack first pixel from r210 format (little-endian RGBX 10-bit)
        dwords = np.frombuffer(rgb10_buffer, dtype=np.uint32)
        r = (dwords[0] >> 22) & 0x3FF
        g = (dwords[0] >> 12) & 0x3FF
        b = (dwords[0] >> 2) & 0x3FF

        assert r == 940, f"Expected R=940 for narrow white, got {r}"
        assert g == 940, f"Expected G=940 for narrow white, got {g}"
        assert b == 940, f"Expected B=940 for narrow white, got {b}"

    def test_uint16_to_rgb10_full_to_full(self):
        """Test full range uint16 to full range RGB10."""
        width, height = 12, 2
        # Full range white: 65535 @ 16-bit
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb10

        rgb10_buffer = rgb_uint16_to_rgb10(rgb, width, height,
                                          input_narrow_range=False, output_narrow_range=False)

        dwords = np.frombuffer(rgb10_buffer, dtype=np.uint32)
        r = (dwords[0] >> 22) & 0x3FF
        g = (dwords[0] >> 12) & 0x3FF
        b = (dwords[0] >> 2) & 0x3FF

        assert r == 1023, f"Expected R=1023 for full white, got {r}"
        assert g == 1023, f"Expected G=1023 for full white, got {g}"
        assert b == 1023, f"Expected B=1023 for full white, got {b}"

    def test_uint16_to_rgb10_full_to_narrow(self):
        """Test full range uint16 to narrow range RGB10."""
        width, height = 12, 2
        # Full range white: 65535 @ 16-bit
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb10

        rgb10_buffer = rgb_uint16_to_rgb10(rgb, width, height,
                                          input_narrow_range=False, output_narrow_range=True)

        dwords = np.frombuffer(rgb10_buffer, dtype=np.uint32)
        r = (dwords[0] >> 22) & 0x3FF
        g = (dwords[0] >> 12) & 0x3FF
        b = (dwords[0] >> 2) & 0x3FF

        assert r == 940, f"Expected R=940 for full→narrow white, got {r}"
        assert g == 940, f"Expected G=940 for full→narrow white, got {g}"
        assert b == 940, f"Expected B=940 for full→narrow white, got {b}"

    def test_uint16_to_rgb10_narrow_to_full(self):
        """Test narrow range uint16 to full range RGB10."""
        width, height = 12, 2
        # Narrow range white: 940 @ 10-bit = 60160 @ 16-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb10

        rgb10_buffer = rgb_uint16_to_rgb10(rgb, width, height,
                                          input_narrow_range=True, output_narrow_range=False)

        dwords = np.frombuffer(rgb10_buffer, dtype=np.uint32)
        r = (dwords[0] >> 22) & 0x3FF
        g = (dwords[0] >> 12) & 0x3FF
        b = (dwords[0] >> 2) & 0x3FF

        assert r == 1023, f"Expected R=1023 for narrow→full white, got {r}"
        assert g == 1023, f"Expected G=1023 for narrow→full white, got {g}"
        assert b == 1023, f"Expected B=1023 for narrow→full white, got {b}"


class TestRGBtoRGB12Conversions:
    """Test RGB to 12-bit RGB conversions with range parameters."""

    @staticmethod
    def unpack_r12l_pixel(buffer, pixel_index):
        """Unpack a single pixel from R12L (12-bit RGB LE) format.

        R12L format: 8 pixels in 36 bytes (9 DWORDs).
        This matches the unpacking code in pixel_reader.cpp.
        """
        # Each group of 8 pixels is packed in 9 DWORDs (36 bytes)
        group = pixel_index // 8
        pixel_in_group = pixel_index % 8

        # Start of this group's data
        dwords = np.frombuffer(buffer[group * 36:(group + 1) * 36], dtype=np.uint32)

        # Unpack based on position in group (matching pixel_reader.cpp)
        if pixel_in_group == 0:
            r = dwords[0] & 0xFFF
            g = (dwords[0] >> 12) & 0xFFF
            b = ((dwords[0] >> 24) & 0xFF) | ((dwords[1] & 0xF) << 8)
        elif pixel_in_group == 1:
            r = (dwords[1] >> 4) & 0xFFF
            g = (dwords[1] >> 16) & 0xFFF
            b = ((dwords[1] >> 28) & 0xF) | ((dwords[2] & 0xFF) << 4)
        elif pixel_in_group == 2:
            r = (dwords[2] >> 8) & 0xFFF
            g = (dwords[2] >> 20) & 0xFFF
            b = dwords[3] & 0xFFF
        elif pixel_in_group == 3:
            r = (dwords[3] >> 12) & 0xFFF
            g = ((dwords[3] >> 24) & 0xFF) | ((dwords[4] & 0xF) << 8)
            b = (dwords[4] >> 4) & 0xFFF
        elif pixel_in_group == 4:
            r = (dwords[4] >> 16) & 0xFFF
            g = ((dwords[4] >> 28) & 0xF) | ((dwords[5] & 0xFF) << 4)
            b = (dwords[5] >> 8) & 0xFFF
        elif pixel_in_group == 5:
            r = (dwords[5] >> 20) & 0xFFF
            g = dwords[6] & 0xFFF
            b = (dwords[6] >> 12) & 0xFFF
        elif pixel_in_group == 6:
            r = ((dwords[6] >> 24) & 0xFF) | ((dwords[7] & 0xF) << 8)
            g = (dwords[7] >> 4) & 0xFFF
            b = (dwords[7] >> 16) & 0xFFF
        else:  # pixel_in_group == 7
            r = ((dwords[7] >> 28) & 0xF) | ((dwords[8] & 0xFF) << 4)
            g = (dwords[8] >> 8) & 0xFFF
            b = (dwords[8] >> 20) & 0xFFF

        return r, g, b

    def test_uint16_to_rgb12_default(self):
        """Test default behavior: full to full."""
        width, height = 16, 2
        # Full range white: 65535 @ 16-bit
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb12

        rgb12_buffer = rgb_uint16_to_rgb12(rgb, width, height)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 4095, f"Expected R=4095 for full white, got {r}"
        assert g == 4095, f"Expected G=4095 for full white, got {g}"
        assert b == 4095, f"Expected B=4095 for full white, got {b}"

    def test_uint16_to_rgb12_full_to_full(self):
        """Test full range uint16 to full range RGB12."""
        width, height = 16, 2
        # Full range white: 65535 @ 16-bit
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb12

        rgb12_buffer = rgb_uint16_to_rgb12(rgb, width, height,
                                          input_narrow_range=False, output_narrow_range=False)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 4095, f"Expected R=4095 for full white, got {r}"
        assert g == 4095, f"Expected G=4095 for full white, got {g}"
        assert b == 4095, f"Expected B=4095 for full white, got {b}"

    def test_uint16_to_rgb12_full_to_narrow(self):
        """Test full range uint16 to narrow range RGB12."""
        width, height = 16, 2
        # Full range white: 65535 @ 16-bit
        rgb = np.full((height, width, 3), 65535, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb12

        rgb12_buffer = rgb_uint16_to_rgb12(rgb, width, height,
                                          input_narrow_range=False, output_narrow_range=True)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 3760, f"Expected R=3760 for full→narrow white, got {r}"
        assert g == 3760, f"Expected G=3760 for full→narrow white, got {g}"
        assert b == 3760, f"Expected B=3760 for full→narrow white, got {b}"

    def test_uint16_to_rgb12_narrow_to_full(self):
        """Test narrow range uint16 to full range RGB12."""
        width, height = 16, 2
        # Narrow range white: 940 @ 10-bit = 60160 @ 16-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb12

        rgb12_buffer = rgb_uint16_to_rgb12(rgb, width, height,
                                          input_narrow_range=True, output_narrow_range=False)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 4095, f"Expected R=4095 for narrow→full white, got {r}"
        assert g == 4095, f"Expected G=4095 for narrow→full white, got {g}"
        assert b == 4095, f"Expected B=4095 for narrow→full white, got {b}"

    def test_uint16_to_rgb12_narrow_to_narrow(self):
        """Test narrow range uint16 to narrow range RGB12 (bitshift path)."""
        width, height = 16, 2
        # Narrow range white: 940 @ 10-bit = 60160 @ 16-bit = 3760 @ 12-bit
        rgb = np.full((height, width, 3), 60160, dtype=np.uint16)

        from blackmagic_io import rgb_uint16_to_rgb12

        rgb12_buffer = rgb_uint16_to_rgb12(rgb, width, height,
                                          input_narrow_range=True, output_narrow_range=True)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 3760, f"Expected R=3760 for narrow white, got {r}"
        assert g == 3760, f"Expected G=3760 for narrow white, got {g}"
        assert b == 3760, f"Expected B=3760 for narrow white, got {b}"

    def test_float_to_rgb12_default(self):
        """Test float to RGB12 default (full range output)."""
        width, height = 16, 2
        rgb = np.full((height, width, 3), 1.0, dtype=np.float32)

        from blackmagic_io import rgb_float_to_rgb12

        rgb12_buffer = rgb_float_to_rgb12(rgb, width, height)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 4095, f"Expected R=4095 for float full white, got {r}"
        assert g == 4095, f"Expected G=4095 for float full white, got {g}"
        assert b == 4095, f"Expected B=4095 for float full white, got {b}"

    def test_float_to_rgb12_narrow(self):
        """Test float to RGB12 narrow range output."""
        width, height = 16, 2
        rgb = np.full((height, width, 3), 1.0, dtype=np.float32)

        from blackmagic_io import rgb_float_to_rgb12

        rgb12_buffer = rgb_float_to_rgb12(rgb, width, height, output_narrow_range=True)

        r, g, b = self.unpack_r12l_pixel(rgb12_buffer, 0)

        assert r == 3760, f"Expected R=3760 for float narrow white, got {r}"
        assert g == 3760, f"Expected G=3760 for float narrow white, got {g}"
        assert b == 3760, f"Expected B=3760 for float narrow white, got {b}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
