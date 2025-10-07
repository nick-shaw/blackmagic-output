#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "decklink_wrapper.hpp"

namespace py = pybind11;

// Helper function to convert NumPy array to raw data
std::pair<const uint8_t*, size_t> numpy_to_raw(py::array_t<uint8_t> input) {
    py::buffer_info buf_info = input.request();
    return std::make_pair(static_cast<const uint8_t*>(buf_info.ptr), buf_info.size);
}

// Helper function to convert RGB numpy array to BGRA format
py::array_t<uint8_t> rgb_to_bgra(py::array_t<uint8_t> rgb_array, int width, int height) {
    auto buf = rgb_array.request();
    
    if (buf.ndim != 3 || buf.shape[2] != 3) {
        throw std::runtime_error("Input array must be HxWx3 RGB format");
    }
    
    if (buf.shape[0] != height || buf.shape[1] != width) {
        throw std::runtime_error("Array dimensions don't match specified width/height");
    }
    
    auto result = py::array_t<uint8_t>({height, width, 4});
    auto res_buf = result.request();
    
    const uint8_t* src = static_cast<const uint8_t*>(buf.ptr);
    uint8_t* dst = static_cast<uint8_t*>(res_buf.ptr);
    
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            int src_idx = y * width * 3 + x * 3;
            int dst_idx = y * width * 4 + x * 4;
            
            // Convert RGB to BGRA
            dst[dst_idx + 0] = src[src_idx + 2];  // B
            dst[dst_idx + 1] = src[src_idx + 1];  // G
            dst[dst_idx + 2] = src[src_idx + 0];  // R
            dst[dst_idx + 3] = 255;               // A
        }
    }
    
    return result;
}

// Helper function to convert RGB uint16 array to 10-bit YUV v210 format
py::array_t<uint8_t> rgb_uint16_to_yuv10(py::array_t<uint16_t> rgb_array, int width, int height, DeckLinkOutput::Gamut matrix = DeckLinkOutput::Gamut::Rec709) {
    auto buf = rgb_array.request();

    if (buf.ndim != 3 || buf.shape[2] != 3) {
        throw std::runtime_error("Input array must be HxWx3 RGB format");
    }

    if (buf.shape[0] != height || buf.shape[1] != width) {
        throw std::runtime_error("Array dimensions don't match specified width/height");
    }

    // v210 format: 6 pixels packed into 4 32-bit words (16 bytes)
    int row_bytes = ((width + 5) / 6) * 16;
    auto result = py::array_t<uint8_t>(height * row_bytes);
    auto res_buf = result.request();

    const uint8_t* src_base = static_cast<const uint8_t*>(buf.ptr);
    uint32_t* dst = static_cast<uint32_t*>(res_buf.ptr);

    // Get strides in bytes
    ssize_t stride_y = buf.strides[0];
    ssize_t stride_x = buf.strides[1];
    ssize_t stride_c = buf.strides[2];

    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x += 6) {
            uint16_t y_values[6], u_values[3], v_values[3];
            float u_temp[6], v_temp[6];

            // Convert RGB to YUV for up to 6 pixels
            for (int i = 0; i < 6; i++) {
                int pixel_x = x + i;
                if (pixel_x < width) {
                    const uint16_t* pixel = reinterpret_cast<const uint16_t*>(
                        src_base + y * stride_y + pixel_x * stride_x);
                    uint16_t r = pixel[0];
                    uint16_t g = pixel[1];
                    uint16_t b = pixel[2];

                    float rf = r / 65535.0f;
                    float gf = g / 65535.0f;
                    float bf = b / 65535.0f;

                    float yf, uf, vf;
                    if (matrix == DeckLinkOutput::Gamut::Rec2020) {
                        yf = 0.2627f * rf + 0.6780f * gf + 0.0593f * bf;
                        uf = -0.1396f * rf - 0.3604f * gf + 0.5000f * bf;
                        vf = 0.5000f * rf - 0.4598f * gf - 0.0402f * bf;
                    } else {
                        yf = 0.2126f * rf + 0.7152f * gf + 0.0722f * bf;
                        uf = -0.1146f * rf - 0.3854f * gf + 0.5000f * bf;
                        vf = 0.5000f * rf - 0.4542f * gf - 0.0458f * bf;
                    }

                    y_values[i] = (uint16_t)(yf * 876.0f + 64.0f);
                    u_temp[i] = uf;
                    v_temp[i] = vf;
                } else {
                    y_values[i] = 64;
                    u_temp[i] = 0.0f;
                    v_temp[i] = 0.0f;
                }
            }

            // Average pairs of U/V samples for 4:2:2 chroma subsampling
            for (int i = 0; i < 3; i++) {
                float u_avg = (u_temp[i*2] + u_temp[i*2+1]) * 0.5f;
                float v_avg = (v_temp[i*2] + v_temp[i*2+1]) * 0.5f;
                u_values[i] = (uint16_t)((u_avg + 0.5f) * 896.0f + 64.0f);
                v_values[i] = (uint16_t)((v_avg + 0.5f) * 896.0f + 64.0f);
            }

            // Pack into v210 format
            // v210 is little-endian with component order: Cb Y Cr (U Y V)
            // Each DWORD: comp0[9:0] comp1[9:0] comp2[9:0] xx[1:0]
            // Written in little-endian byte order
            int dst_idx = (y * row_bytes / 4) + ((x / 6) * 4);
            dst[dst_idx + 0] = (u_values[0] << 0) | (y_values[0] << 10) | (v_values[0] << 20);
            dst[dst_idx + 1] = (y_values[1] << 0) | (u_values[1] << 10) | (y_values[2] << 20);
            dst[dst_idx + 2] = (v_values[1] << 0) | (y_values[3] << 10) | (u_values[2] << 20);
            dst[dst_idx + 3] = (y_values[4] << 0) | (v_values[2] << 10) | (y_values[5] << 20);
        }
    }

    return result;
}

// Helper function to convert RGB float array to 10-bit YUV v210 format
py::array_t<uint8_t> rgb_float_to_yuv10(py::array_t<float> rgb_array, int width, int height, DeckLinkOutput::Gamut matrix = DeckLinkOutput::Gamut::Rec709) {
    auto buf = rgb_array.request();

    if (buf.ndim != 3 || buf.shape[2] != 3) {
        throw std::runtime_error("Input array must be HxWx3 RGB format");
    }

    if (buf.shape[0] != height || buf.shape[1] != width) {
        throw std::runtime_error("Array dimensions don't match specified width/height");
    }

    // v210 format: 6 pixels packed into 4 32-bit words (16 bytes)
    int row_bytes = ((width + 5) / 6) * 16;
    auto result = py::array_t<uint8_t>(height * row_bytes);
    auto res_buf = result.request();

    const uint8_t* src_base = static_cast<const uint8_t*>(buf.ptr);
    uint32_t* dst = static_cast<uint32_t*>(res_buf.ptr);

    // Get strides in bytes
    ssize_t stride_y = buf.strides[0];
    ssize_t stride_x = buf.strides[1];
    ssize_t stride_c = buf.strides[2];


    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x += 6) {
            uint16_t y_values[6], u_values[3], v_values[3];
            float u_temp[6], v_temp[6];

            // Convert RGB to YUV for up to 6 pixels
            for (int i = 0; i < 6; i++) {
                int pixel_x = x + i;
                if (pixel_x < width) {
                    const float* pixel = reinterpret_cast<const float*>(
                        src_base + y * stride_y + pixel_x * stride_x);
                    float r = pixel[0];
                    float g = pixel[1];
                    float b = pixel[2];

                    float yf, uf, vf;
                    if (matrix == DeckLinkOutput::Gamut::Rec2020) {
                        yf = 0.2627f * r + 0.6780f * g + 0.0593f * b;
                        uf = -0.1396f * r - 0.3604f * g + 0.5000f * b;
                        vf = 0.5000f * r - 0.4598f * g - 0.0402f * b;
                    } else {
                        yf = 0.2126f * r + 0.7152f * g + 0.0722f * b;
                        uf = -0.1146f * r - 0.3854f * g + 0.5000f * b;
                        vf = 0.5000f * r - 0.4542f * g - 0.0458f * b;
                    }

                    int y10 = (int)(yf * 876.0f + 64.0f);
                    y_values[i] = (uint16_t)(y10 < 0 ? 0 : (y10 > 1023 ? 1023 : y10));
                    u_temp[i] = uf;
                    v_temp[i] = vf;
                } else {
                    y_values[i] = 64;
                    u_temp[i] = 0.0f;
                    v_temp[i] = 0.0f;
                }
            }

            // Average pairs of U/V samples for 4:2:2 chroma subsampling
            for (int i = 0; i < 3; i++) {
                float u_avg = (u_temp[i*2] + u_temp[i*2+1]) * 0.5f;
                float v_avg = (v_temp[i*2] + v_temp[i*2+1]) * 0.5f;
                int u10 = (int)((u_avg + 0.5f) * 896.0f + 64.0f);
                int v10 = (int)((v_avg + 0.5f) * 896.0f + 64.0f);
                u_values[i] = (uint16_t)(u10 < 0 ? 0 : (u10 > 1023 ? 1023 : u10));
                v_values[i] = (uint16_t)(v10 < 0 ? 0 : (v10 > 1023 ? 1023 : v10));
            }

            // Pack into v210 format
            // v210 is little-endian with component order: Cb Y Cr (U Y V)
            // Each DWORD: comp0[9:0] comp1[9:0] comp2[9:0] xx[1:0]
            // Written in little-endian byte order
            int dst_idx = (y * row_bytes / 4) + ((x / 6) * 4);
            dst[dst_idx + 0] = (u_values[0] << 0) | (y_values[0] << 10) | (v_values[0] << 20);
            dst[dst_idx + 1] = (y_values[1] << 0) | (u_values[1] << 10) | (y_values[2] << 20);
            dst[dst_idx + 2] = (v_values[1] << 0) | (y_values[3] << 10) | (u_values[2] << 20);
            dst[dst_idx + 3] = (y_values[4] << 0) | (v_values[2] << 10) | (y_values[5] << 20);
        }
    }

    return result;
}

PYBIND11_MODULE(decklink_output, m) {
    m.doc() = "Python bindings for Blackmagic DeckLink video output";

    // Enums
    py::enum_<DeckLinkOutput::PixelFormat>(m, "PixelFormat")
        .value("YUV", DeckLinkOutput::PixelFormat::Format8BitYUV)
        .value("BGRA", DeckLinkOutput::PixelFormat::Format8BitBGRA)
        .value("YUV10", DeckLinkOutput::PixelFormat::Format10BitYUV);

    py::enum_<DeckLinkOutput::DisplayMode>(m, "DisplayMode")
        .value("HD1080p25", DeckLinkOutput::DisplayMode::HD1080p25)
        .value("HD1080p30", DeckLinkOutput::DisplayMode::HD1080p30)
        .value("HD1080p50", DeckLinkOutput::DisplayMode::HD1080p50)
        .value("HD1080p60", DeckLinkOutput::DisplayMode::HD1080p60)
        .value("HD720p50", DeckLinkOutput::DisplayMode::HD720p50)
        .value("HD720p60", DeckLinkOutput::DisplayMode::HD720p60);

    auto gamut_enum = py::enum_<DeckLinkOutput::Gamut>(m, "Gamut")
        .value("Rec709", DeckLinkOutput::Gamut::Rec709)
        .value("Rec2020", DeckLinkOutput::Gamut::Rec2020);

    // Create Matrix as an alias to Gamut for clearer naming in RGB->YCbCr conversion
    m.attr("Matrix") = gamut_enum;

    py::enum_<DeckLinkOutput::Eotf>(m, "Eotf")
        .value("SDR", DeckLinkOutput::Eotf::SDR)
        .value("PQ", DeckLinkOutput::Eotf::PQ)
        .value("HLG", DeckLinkOutput::Eotf::HLG);

    // HdrMetadataCustom struct
    py::class_<DeckLinkOutput::HdrMetadataCustom>(m, "HdrMetadataCustom")
        .def(py::init<>())
        .def_readwrite("display_primaries_red_x", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesRedX)
        .def_readwrite("display_primaries_red_y", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesRedY)
        .def_readwrite("display_primaries_green_x", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesGreenX)
        .def_readwrite("display_primaries_green_y", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesGreenY)
        .def_readwrite("display_primaries_blue_x", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesBlueX)
        .def_readwrite("display_primaries_blue_y", &DeckLinkOutput::HdrMetadataCustom::displayPrimariesBlueY)
        .def_readwrite("white_point_x", &DeckLinkOutput::HdrMetadataCustom::whitePointX)
        .def_readwrite("white_point_y", &DeckLinkOutput::HdrMetadataCustom::whitePointY)
        .def_readwrite("max_mastering_luminance", &DeckLinkOutput::HdrMetadataCustom::maxMasteringLuminance)
        .def_readwrite("min_mastering_luminance", &DeckLinkOutput::HdrMetadataCustom::minMasteringLuminance)
        .def_readwrite("max_content_light_level", &DeckLinkOutput::HdrMetadataCustom::maxContentLightLevel)
        .def_readwrite("max_frame_average_light_level", &DeckLinkOutput::HdrMetadataCustom::maxFrameAverageLightLevel);

    // Timecode struct
    py::class_<DeckLinkOutput::Timecode>(m, "Timecode")
        .def(py::init<>())
        .def_readwrite("hours", &DeckLinkOutput::Timecode::hours)
        .def_readwrite("minutes", &DeckLinkOutput::Timecode::minutes)
        .def_readwrite("seconds", &DeckLinkOutput::Timecode::seconds)
        .def_readwrite("frames", &DeckLinkOutput::Timecode::frames)
        .def_readwrite("drop_frame", &DeckLinkOutput::Timecode::dropFrame)
        .def("__repr__", [](const DeckLinkOutput::Timecode& tc) {
            char buf[32];
            snprintf(buf, sizeof(buf), "%02d:%02d:%02d%c%02d",
                tc.hours, tc.minutes, tc.seconds,
                tc.dropFrame ? ';' : ':', tc.frames);
            return std::string(buf);
        });

    // VideoSettings struct
    py::class_<DeckLinkOutput::VideoSettings>(m, "VideoSettings")
        .def(py::init<>())
        .def_readwrite("mode", &DeckLinkOutput::VideoSettings::mode)
        .def_readwrite("format", &DeckLinkOutput::VideoSettings::format)
        .def_readwrite("width", &DeckLinkOutput::VideoSettings::width)
        .def_readwrite("height", &DeckLinkOutput::VideoSettings::height)
        .def_readwrite("framerate", &DeckLinkOutput::VideoSettings::framerate)
        .def_readwrite("colorimetry", &DeckLinkOutput::VideoSettings::colorimetry)
        .def_readwrite("eotf", &DeckLinkOutput::VideoSettings::eotf);

    // Main DeckLinkOutput class
    py::class_<DeckLinkOutput>(m, "DeckLinkOutput")
        .def(py::init<>())
        .def("initialize", &DeckLinkOutput::initialize,
             "Initialize DeckLink device", py::arg("device_index") = 0)
        .def("setup_output", &DeckLinkOutput::setupOutput,
             "Setup video output with specified settings")
        .def("set_frame_data", [](DeckLinkOutput& self, py::array_t<uint8_t> data) {
            auto [ptr, size] = numpy_to_raw(data);
            return self.setFrameData(ptr, size);
        }, "Set frame data from numpy array")
        .def("start_output", &DeckLinkOutput::startOutput, "Start video output")
        .def("stop_output", &DeckLinkOutput::stopOutput, "Stop video output",
             py::arg("send_black_frame") = false)
        .def("cleanup", &DeckLinkOutput::cleanup, "Cleanup resources")
        .def("get_device_list", &DeckLinkOutput::getDeviceList, "Get list of available devices")
        .def("get_video_settings", &DeckLinkOutput::getVideoSettings, "Get video settings for display mode")
        .def("set_hdr_metadata", &DeckLinkOutput::setHdrMetadata, "Set HDR metadata with default values",
             py::arg("colorimetry"), py::arg("eotf"))
        .def("set_hdr_metadata_custom", &DeckLinkOutput::setHdrMetadataCustom, "Set HDR metadata with custom values",
             py::arg("colorimetry"), py::arg("eotf"), py::arg("custom"))
        .def("set_timecode", &DeckLinkOutput::setTimecode, "Set initial timecode value (auto-increments each frame)",
             py::arg("timecode"))
        .def("get_timecode", &DeckLinkOutput::getTimecode, "Get current timecode value");

    // Utility functions
    m.def("rgb_to_bgra", &rgb_to_bgra,
          "Convert RGB numpy array to BGRA format",
          py::arg("rgb_array"), py::arg("width"), py::arg("height"));

    m.def("rgb_uint16_to_yuv10", &rgb_uint16_to_yuv10,
          "Convert RGB uint16 numpy array to 10-bit YUV v210 format",
          py::arg("rgb_array"), py::arg("width"), py::arg("height"),
          py::arg("matrix") = DeckLinkOutput::Gamut::Rec709);

    m.def("rgb_float_to_yuv10", &rgb_float_to_yuv10,
          "Convert RGB float numpy array to 10-bit YUV v210 format",
          py::arg("rgb_array"), py::arg("width"), py::arg("height"),
          py::arg("matrix") = DeckLinkOutput::Gamut::Rec709);

    // Helper function to create solid color frame
    m.def("create_solid_color_frame", [](int width, int height, py::tuple color) -> py::array_t<uint8_t> {
        if (color.size() != 3) {
            throw std::runtime_error("Color must be RGB tuple (r, g, b)");
        }
        
        auto result = py::array_t<uint8_t>({height, width, 4});
        auto buf = result.request();
        uint8_t* ptr = static_cast<uint8_t*>(buf.ptr);
        
        uint8_t r = color[0].cast<uint8_t>();
        uint8_t g = color[1].cast<uint8_t>();
        uint8_t b = color[2].cast<uint8_t>();
        
        for (int i = 0; i < height * width; i++) {
            ptr[i * 4 + 0] = b;   // B
            ptr[i * 4 + 1] = g;   // G
            ptr[i * 4 + 2] = r;   // R
            ptr[i * 4 + 3] = 255; // A
        }
        
        return result;
    }, "Create solid color frame in BGRA format");

    // Version info
    m.attr("__version__") = "1.0.0";
}