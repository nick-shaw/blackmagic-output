#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <stdint.h>

#ifdef __APPLE__
    #include <pthread.h>
    #include <CoreFoundation/CoreFoundation.h>
    #include "DeckLinkAPI.h"
    typedef int32_t INT32;
    typedef uint32_t UINT32;
    typedef uint8_t UINT8;
    typedef uint16_t UINT16;
    typedef int64_t INT64;
    typedef uint64_t UINT64;
    typedef bool BOOL;

    #define Initialize() do {} while(0)
    #define GetDeckLinkIterator(iter) (*iter = CreateDeckLinkIteratorInstance())
    #define STRINGOBJ CFStringRef
    #define STRINGFREE(s) CFRelease(s)

    void StringToStdString(CFStringRef cfString, std::string& stdString) {
        CFIndex length = CFStringGetLength(cfString);
        CFIndex maxSize = CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8) + 1;
        char* buffer = new char[maxSize];
        if (CFStringGetCString(cfString, buffer, maxSize, kCFStringEncodingUTF8)) {
            stdString = buffer;
        }
        delete[] buffer;
    }
#elif defined(__linux__)
    #include "DeckLinkAPI.h"
    #include "LinuxCOM.h"
    typedef int32_t INT32;
    typedef uint32_t UINT32;
    typedef uint8_t UINT8;
    typedef uint16_t UINT16;
    typedef int64_t INT64;
    typedef uint64_t UINT64;
    typedef bool BOOL;

    #define Initialize() do {} while(0)
    #define GetDeckLinkIterator(iter) (*iter = CreateDeckLinkIteratorInstance())
    #define STRINGOBJ const char*
    #define STRINGFREE(s) free((void*)s)

    void StringToStdString(const char* cString, std::string& stdString) {
        if (cString) stdString = cString;
    }
#elif defined(_WIN32)
    #include <windows.h>
    #include <comutil.h>
    #include "DeckLinkAPI.h"
    typedef int32_t INT32;
    typedef uint32_t UINT32;
    typedef uint8_t UINT8;
    typedef uint16_t UINT16;
    typedef int64_t INT64;
    typedef uint64_t UINT64;
    typedef bool BOOL;

    #define Initialize() CoInitialize(NULL)
    #define GetDeckLinkIterator(iter) CoCreateInstance(CLSID_CDeckLinkIterator, NULL, CLSCTX_ALL, IID_IDeckLinkIterator, (void**)iter)
    #define STRINGOBJ BSTR
    #define STRINGFREE(s) SysFreeString(s)

    void StringToStdString(BSTR bstr, std::string& stdString) {
        _bstr_t b(bstr);
        stdString = (const char*)b;
    }
#endif

bool doExit = false;
int counter = 0;
int x = 960;
int y = 540;
bool printHDRMetadata = false;
BMDPixelFormat currentPixelFormat = bmdFormat10BitYUV;

// Helper function to get pixel format name
const char* GetPixelFormatName(BMDPixelFormat pixelFormat) {
    switch (pixelFormat) {
        case bmdFormat8BitYUV:      return "8-bit YUV (2vuy)";
        case bmdFormat10BitYUV:     return "10-bit YUV (v210)";
        case bmdFormat10BitYUVA:    return "10-bit YUVA (Ay10)";
        case bmdFormat8BitARGB:     return "8-bit ARGB";
        case bmdFormat8BitBGRA:     return "8-bit BGRA";
        case bmdFormat10BitRGB:     return "10-bit RGB (r210)";
        case bmdFormat12BitRGB:     return "12-bit RGB (R12B)";
        case bmdFormat12BitRGBLE:   return "12-bit RGB LE (R12L)";
        case bmdFormat10BitRGBXLE:  return "10-bit RGBX LE (R10l)";
        case bmdFormat10BitRGBX:    return "10-bit RGBX (R10b)";
        case bmdFormatH265:         return "H.265 (hev1)";
        case bmdFormatDNxHR:        return "DNxHR (AVdh)";
        default:                    return "Unknown";
    }
}

// Helper function to determine appropriate pixel format from detected flags
BMDPixelFormat GetPixelFormatFromDetectedFlags(BMDDetectedVideoInputFormatFlags flags) {
    bool isYUV = (flags & bmdDetectedVideoInputYCbCr422) != 0;
    bool isRGB = (flags & bmdDetectedVideoInputRGB444) != 0;
    bool is8bit = (flags & bmdDetectedVideoInput8BitDepth) != 0;
    bool is10bit = (flags & bmdDetectedVideoInput10BitDepth) != 0;
    bool is12bit = (flags & bmdDetectedVideoInput12BitDepth) != 0;

    if (isYUV) {
        if (is8bit) return bmdFormat8BitYUV;
        if (is10bit) return bmdFormat10BitYUV;
        return bmdFormat10BitYUV; // Default for YUV
    } else if (isRGB) {
        if (is8bit) return bmdFormat8BitBGRA;
        if (is10bit) return bmdFormat10BitRGBXLE;  // Use little-endian
        if (is12bit) return bmdFormat12BitRGBLE;   // Use little-endian
        return bmdFormat10BitRGBXLE; // Default for RGB (little-endian)
    }

    return bmdFormat10BitYUV; // Fallback default
}

// Structure to hold pixel values
struct PixelValue {
    int comp1, comp2, comp3;
    const char* format;
};

// Extract pixel values based on format
PixelValue ExtractPixelValue(void* frameBytes, int width, int height, int rowBytes, int pixelX, int pixelY, BMDPixelFormat format) {
    PixelValue result = {0, 0, 0, ""};
    UINT8* buffer = (UINT8*)frameBytes;

    if (pixelX < 0) pixelX = 0;
    if (pixelY < 0) pixelY = 0;
    if (pixelX >= width) pixelX = width - 1;
    if (pixelY >= height) pixelY = height - 1;

    switch (format) {
        case bmdFormat10BitYUV: {
            // v210 format: 6 pixels in 16 bytes (4 DWORDs)
            // DWORD 0: U0 Y0 V0 (bits [9:0] U0, [19:10] Y0, [29:20] V0)
            // DWORD 1: Y1 U1 Y2 (bits [9:0] Y1, [19:10] U1, [29:20] Y2)
            // DWORD 2: V1 Y3 U2 (bits [9:0] V1, [19:10] Y3, [29:20] U2)
            // DWORD 3: Y4 V2 Y5 (bits [9:0] Y4, [19:10] V2, [29:20] Y5)
            UINT32* line = (UINT32*)(buffer + pixelY * rowBytes);
            int groupIndex = (pixelX / 6) * 4; // Each group of 4 UINT32s contains 6 pixels
            int pixelInGroup = pixelX % 6;

            UINT32 d0 = line[groupIndex];
            UINT32 d1 = line[groupIndex + 1];
            UINT32 d2 = line[groupIndex + 2];
            UINT32 d3 = line[groupIndex + 3];

            // Extract Y, U, V based on pixel position
            // In 4:2:2, pixels 0-1 share U0/V0, pixels 2-3 share U1/V1, pixels 4-5 share U2/V2
            switch (pixelInGroup) {
                case 0:
                    result.comp1 = (d0 >> 10) & 0x3FF; // Y0
                    result.comp2 = d0 & 0x3FF;         // U0
                    result.comp3 = (d0 >> 20) & 0x3FF; // V0
                    break;
                case 1:
                    result.comp1 = d1 & 0x3FF;         // Y1
                    result.comp2 = d0 & 0x3FF;         // U0 (shared with pixel 0)
                    result.comp3 = (d0 >> 20) & 0x3FF; // V0 (shared with pixel 0)
                    break;
                case 2:
                    result.comp1 = (d1 >> 20) & 0x3FF; // Y2
                    result.comp2 = (d1 >> 10) & 0x3FF; // U1
                    result.comp3 = d2 & 0x3FF;         // V1
                    break;
                case 3:
                    result.comp1 = (d2 >> 10) & 0x3FF; // Y3
                    result.comp2 = (d1 >> 10) & 0x3FF; // U1 (shared with pixel 2)
                    result.comp3 = d2 & 0x3FF;         // V1 (shared with pixel 2)
                    break;
                case 4:
                    result.comp1 = d3 & 0x3FF;         // Y4
                    result.comp2 = (d2 >> 20) & 0x3FF; // U2
                    result.comp3 = (d3 >> 10) & 0x3FF; // V2
                    break;
                case 5:
                    result.comp1 = (d3 >> 20) & 0x3FF; // Y5
                    result.comp2 = (d2 >> 20) & 0x3FF; // U2 (shared with pixel 4)
                    result.comp3 = (d3 >> 10) & 0x3FF; // V2 (shared with pixel 4)
                    break;
            }
            result.format = "Y'CbCr";
            break;
        }

        case bmdFormat8BitYUV: {
            // 2vuy format: UYVY - 2 pixels in 4 bytes
            UINT8* line = buffer + pixelY * rowBytes;
            int byteIndex = (pixelX / 2) * 4;
            result.comp1 = line[byteIndex + 1];     // Y0
            result.comp2 = line[byteIndex];         // U/Cb
            result.comp3 = line[byteIndex + 2];     // V/Cr
            result.format = "Y'CbCr";
            break;
        }

        case bmdFormat10BitRGB: {
            // r210 format: Big-endian RGB 10-bit, packed as 2:10:10:10 (32 bits per pixel)
            UINT32* line = (UINT32*)(buffer + pixelY * rowBytes);
            UINT32 pixel = line[pixelX];
            result.comp1 = (pixel >> 20) & 0x3FF;  // R
            result.comp2 = (pixel >> 10) & 0x3FF;  // G
            result.comp3 = pixel & 0x3FF;          // B
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat10BitRGBXLE: {
            // R10l format: Little-endian 10-bit RGB (32 bits per pixel)
            // 32-bit word: R[9:0] at bits 31:22, G[9:0] at bits 21:12, B[9:0] at bits 11:2, padding at bits 1:0
            UINT32* line = (UINT32*)(buffer + pixelY * rowBytes);
            UINT32 pixel = line[pixelX];
            result.comp1 = (pixel >> 22) & 0x3FF;  // R
            result.comp2 = (pixel >> 12) & 0x3FF;  // G
            result.comp3 = (pixel >> 2) & 0x3FF;   // B
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat10BitRGBX: {
            // R10b format: Big-endian 10-bit RGB (32 bits per pixel)
            UINT32* line = (UINT32*)(buffer + pixelY * rowBytes);
            UINT32 pixel = line[pixelX];
            result.comp1 = (pixel >> 20) & 0x3FF;  // R
            result.comp2 = (pixel >> 10) & 0x3FF;  // G
            result.comp3 = pixel & 0x3FF;          // B
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat12BitRGB: {
            // R12B format: Big-endian RGB 12-bit (36 bits per pixel, 48 bits with padding)
            UINT16* line = (UINT16*)(buffer + pixelY * rowBytes);
            int pixelIndex = pixelX * 3;
            result.comp1 = (line[pixelIndex] >> 4) & 0xFFF;     // R
            result.comp2 = (line[pixelIndex + 1] >> 4) & 0xFFF; // G
            result.comp3 = (line[pixelIndex + 2] >> 4) & 0xFFF; // B
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat12BitRGBLE: {
            // R12L format: 8 pixels packed in 36 bytes (9 DWORDs)
            // Need to unpack based on pixel position within group of 8
            int groupX = (pixelX / 8) * 8;  // Start of 8-pixel group
            int pixelInGroup = pixelX % 8;

            UINT32* groupStart = (UINT32*)(buffer + pixelY * rowBytes + (groupX / 8) * 36);

            uint16_t r[8], g[8], b[8];

            // Unpack the 8 pixels from 9 DWORDs (reverse of packing formula)
            r[0] = groupStart[0] & 0xFFF;
            g[0] = (groupStart[0] >> 12) & 0xFFF;
            b[0] = ((groupStart[0] >> 24) & 0xFF) | ((groupStart[1] & 0xF) << 8);

            r[1] = (groupStart[1] >> 4) & 0xFFF;
            g[1] = (groupStart[1] >> 16) & 0xFFF;
            b[1] = ((groupStart[1] >> 28) & 0xF) | ((groupStart[2] & 0xFF) << 4);

            r[2] = (groupStart[2] >> 8) & 0xFFF;
            g[2] = (groupStart[2] >> 20) & 0xFFF;
            b[2] = groupStart[3] & 0xFFF;

            r[3] = (groupStart[3] >> 12) & 0xFFF;
            g[3] = ((groupStart[3] >> 24) & 0xFF) | ((groupStart[4] & 0xF) << 8);
            b[3] = (groupStart[4] >> 4) & 0xFFF;

            r[4] = (groupStart[4] >> 16) & 0xFFF;
            g[4] = ((groupStart[4] >> 28) & 0xF) | ((groupStart[5] & 0xFF) << 4);
            b[4] = (groupStart[5] >> 8) & 0xFFF;

            r[5] = (groupStart[5] >> 20) & 0xFFF;
            g[5] = groupStart[6] & 0xFFF;
            b[5] = (groupStart[6] >> 12) & 0xFFF;

            r[6] = ((groupStart[6] >> 24) & 0xFF) | ((groupStart[7] & 0xF) << 8);
            g[6] = (groupStart[7] >> 4) & 0xFFF;
            b[6] = (groupStart[7] >> 16) & 0xFFF;

            r[7] = ((groupStart[7] >> 28) & 0xF) | ((groupStart[8] & 0xFF) << 4);
            g[7] = (groupStart[8] >> 8) & 0xFFF;
            b[7] = (groupStart[8] >> 20) & 0xFFF;

            result.comp1 = r[pixelInGroup];
            result.comp2 = g[pixelInGroup];
            result.comp3 = b[pixelInGroup];
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat8BitBGRA: {
            // BGRA format: 8-bit per component (32 bits per pixel)
            UINT8* line = buffer + pixelY * rowBytes;
            int pixelIndex = pixelX * 4;
            result.comp3 = line[pixelIndex];        // B
            result.comp2 = line[pixelIndex + 1];    // G
            result.comp1 = line[pixelIndex + 2];    // R
            result.format = "R'G'B'";
            break;
        }

        case bmdFormat8BitARGB: {
            // ARGB format: 8-bit per component (32 bits per pixel)
            UINT8* line = buffer + pixelY * rowBytes;
            int pixelIndex = pixelX * 4;
            result.comp1 = line[pixelIndex + 1];    // R
            result.comp2 = line[pixelIndex + 2];    // G
            result.comp3 = line[pixelIndex + 3];    // B
            result.format = "R'G'B'";
            break;
        }

        default:
            result.format = "Unsupported";
            break;
    }

    return result;
}

// The input callback class
class NotificationCallback : public IDeckLinkInputCallback
{
public:
    IDeckLinkInput* m_deckLinkInput;

    NotificationCallback(IDeckLinkInput *deckLinkInput)
    {
        m_deckLinkInput = deckLinkInput;
    }

    ~NotificationCallback(void)
    {
    }

    HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, LPVOID *ppv)
    {
        return E_NOINTERFACE;
    }

    ULONG STDMETHODCALLTYPE AddRef()
    {
        return 1;
    }

    ULONG STDMETHODCALLTYPE Release()
    {
        return 1;
    }

    HRESULT STDMETHODCALLTYPE VideoInputFormatChanged(
        /* in */ BMDVideoInputFormatChangedEvents notificationEvents,
        /* in */ IDeckLinkDisplayMode *newDisplayMode,
        /* in */ BMDDetectedVideoInputFormatFlags detectedSignalFlags)
    {
        STRINGOBJ displayModeString = NULL;

        // Check for video field changes
        if (notificationEvents & bmdVideoInputFieldDominanceChanged)
        {
            BMDFieldDominance fieldDominance = newDisplayMode->GetFieldDominance();
            printf("Input field dominance changed to ");
            switch (fieldDominance) {
                case bmdUnknownFieldDominance:
                    printf("unknown\n");
                    break;
                case bmdLowerFieldFirst:
                    printf("lower field first\n");
                    break;
                case bmdUpperFieldFirst:
                    printf("upper field first\n");
                    break;
                case bmdProgressiveFrame:
                    printf("progressive\n");
                    break;
                case bmdProgressiveSegmentedFrame:
                    printf("progressive segmented frame\n");
                    break;
                default:
                    break;
            }
        }

        // Check if the pixel format has changed
        if (notificationEvents & bmdVideoInputColorspaceChanged)
        {
            currentPixelFormat = GetPixelFormatFromDetectedFlags(detectedSignalFlags);
            counter = 0;  // Reset counter so display resets

            printf("Input signal format changed:\x1b[K\n");  // \x1b[K clears to end of line
            printf("  Signal format: ");
            if (detectedSignalFlags & bmdDetectedVideoInputYCbCr422)
                printf("YCbCr422");
            if (detectedSignalFlags & bmdDetectedVideoInputRGB444)
                printf("RGB444");
            printf("\x1b[K\n");  // Clear to end of line

            printf("  Bit depth: ");
            if (detectedSignalFlags & bmdDetectedVideoInput8BitDepth)
                printf("8-bit");
            if (detectedSignalFlags & bmdDetectedVideoInput10BitDepth)
                printf("10-bit");
            if (detectedSignalFlags & bmdDetectedVideoInput12BitDepth)
                printf("12-bit");
            printf("\x1b[K\n\n");  // Clear to end of line
        }

        // Check if the video mode has changed
        if (notificationEvents & bmdVideoInputDisplayModeChanged)
        {
            std::string modeName;
            counter = 0;  // Reset counter so display resets

            // Obtain the name of the video mode
            newDisplayMode->GetName(&displayModeString);
            StringToStdString(displayModeString, modeName);
            printf("\x1b[2A");
            fflush(stdout);
            printf("\nInput display mode: %s\x1b[K\n", modeName.c_str());
            // Release the video mode name string
            STRINGFREE(displayModeString);
        }

        // Pause video capture
        m_deckLinkInput->PauseStreams();

        // Enable video input with the properties of the new video stream
        m_deckLinkInput->EnableVideoInput(newDisplayMode->GetDisplayMode(), currentPixelFormat, bmdVideoInputEnableFormatDetection);

        // Flush any queued video frames
        m_deckLinkInput->FlushStreams();

        // Start video capture
        m_deckLinkInput->StartStreams();
        return S_OK;
    }

    HRESULT STDMETHODCALLTYPE VideoInputFrameArrived(
        /* in */ IDeckLinkVideoInputFrame* videoFrame,
        /* in */ IDeckLinkAudioInputPacket* audioPacket)
    {
        void* frameBytes;

        if (videoFrame)
        {
            videoFrame->GetBytes(&frameBytes);

            int width = videoFrame->GetWidth();
            int height = videoFrame->GetHeight();
            int rowBytes = videoFrame->GetRowBytes();
            BMDPixelFormat frameFormat = videoFrame->GetPixelFormat();

            PixelValue pixel = ExtractPixelValue(frameBytes, width, height, rowBytes, x, y, frameFormat);

            // Try to get metadata extensions
            IDeckLinkVideoFrameMetadataExtensions* metadataExt = NULL;
            HRESULT result = videoFrame->QueryInterface(IID_IDeckLinkVideoFrameMetadataExtensions, (void**)&metadataExt);

            std::string matrixStr = "";
            std::string eotfStr = "";

            double redX = 0.0, redY = 0.0;
            double greenX = 0.0, greenY = 0.0;
            double blueX = 0.0, blueY = 0.0;
            double whiteX = 0.0, whiteY = 0.0;
            double maxMasteringLuminance = 0.0;
            double minMasteringLuminance = 0.0;
            double maxCLL = 0.0;
            double maxFALL = 0.0;

            bool hasDisplayPrimaries = false;
            bool hasWhitePoint = false;
            bool hasMasteringLuminance = false;
            bool hasMaxCLL = false;
            bool hasMaxFALL = false;

            if (result == S_OK && metadataExt != NULL) {
                int64_t colorspace = 0;
                int64_t eotf = 0;

                // Get matrix (colorspace)
                if (metadataExt->GetInt(bmdDeckLinkFrameMetadataColorspace, &colorspace) == S_OK) {
                    switch (colorspace) {
                        case bmdColorspaceRec601:
                            matrixStr = "Rec.601";
                            break;
                        case bmdColorspaceRec709:
                            matrixStr = "Rec.709";
                            break;
                        case bmdColorspaceRec2020:
                            matrixStr = "Rec.2020";
                            break;
                        default:
                            matrixStr = "Unknown";
                            break;
                    }
                }

                // Get EOTF
                if (metadataExt->GetInt(bmdDeckLinkFrameMetadataHDRElectroOpticalTransferFunc, &eotf) == S_OK) {
                    switch (eotf) {
                        case 0:
                            eotfStr = "SDR";
                            break;
                        case 1:
                            eotfStr = "HDR";
                            break;
                        case 2:
                            eotfStr = "PQ";
                            break;
                        case 3:
                            eotfStr = "HLG";
                            break;
                        default:
                            eotfStr = "Unknown";
                            break;
                    }
                }

                if (printHDRMetadata) {
                    // Get display primaries
                    if (metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesRedX, &redX) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesRedY, &redY) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesGreenX, &greenX) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesGreenY, &greenY) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesBlueX, &blueX) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRDisplayPrimariesBlueY, &blueY) == S_OK) {
                        hasDisplayPrimaries = true;
                    }

                    // Get white point
                    if (metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRWhitePointX, &whiteX) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRWhitePointY, &whiteY) == S_OK) {
                        hasWhitePoint = true;
                    }

                    // Get mastering display luminance
                    if (metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRMaxDisplayMasteringLuminance, &maxMasteringLuminance) == S_OK &&
                        metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRMinDisplayMasteringLuminance, &minMasteringLuminance) == S_OK) {
                        hasMasteringLuminance = true;
                    }

                    // Get content light level
                    if (metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRMaximumContentLightLevel, &maxCLL) == S_OK) {
                        hasMaxCLL = true;
                    }
                    if (metadataExt->GetFloat(bmdDeckLinkFrameMetadataHDRMaximumFrameAverageLightLevel, &maxFALL) == S_OK) {
                        hasMaxFALL = true;
                    }
                }

                metadataExt->Release();
            }

            counter += 1;

            // Display initial format on first frame
            if (counter == 1) {
                BMDDetectedVideoInputFormatFlags flags = videoFrame->GetFlags();
                printf("Input signal detected:\x1b[K\n");
                printf("  Signal format: ");
                if (flags & bmdFrameHasNoInputSource) {
                    printf("No signal");
                } else {
                    // Infer from pixel format
                    if (frameFormat == bmdFormat8BitYUV || frameFormat == bmdFormat10BitYUV) {
                        printf("YCbCr422");
                    } else {
                        printf("RGB444");
                    }
                }
                printf("\x1b[K\n");

                printf("  Bit depth: ");
                if (frameFormat == bmdFormat8BitYUV || frameFormat == bmdFormat8BitBGRA || frameFormat == bmdFormat8BitARGB) {
                    printf("8-bit");
                } else if (frameFormat == bmdFormat10BitYUV || frameFormat == bmdFormat10BitRGBXLE || frameFormat == bmdFormat10BitRGBX) {
                    printf("10-bit");
                } else if (frameFormat == bmdFormat12BitRGB || frameFormat == bmdFormat12BitRGBLE) {
                    printf("12-bit");
                }
                printf("\x1b[K\n\n");
            }

            if (counter > 1) {
                int numLines = 2;

                printf("\n%s (%d, %d) = [%d, %d, %d]\x1b[K", pixel.format, x, y, pixel.comp1, pixel.comp2, pixel.comp3);
                if (!matrixStr.empty() || !eotfStr.empty()) {
                    printf("\n");
                    numLines++;
                    if (!matrixStr.empty()) {
                        printf("Matrix: %s\x1b[K", matrixStr.c_str());
                    }
                    if (!eotfStr.empty()) {
                        if (!matrixStr.empty()) printf(" | ");
                        printf("EOTF: %s\x1b[K", eotfStr.c_str());
                    }
                }

                if (printHDRMetadata) {
                    if (hasDisplayPrimaries) {
                        printf("\n");
                        numLines++;
                        printf("Display Primaries: R(%.4f, %.4f) G(%.4f, %.4f) B(%.4f, %.4f)\x1b[K",
                               redX, redY, greenX, greenY, blueX, blueY);
                    }

                    if (hasWhitePoint) {
                        printf("\n");
                        numLines++;
                        printf("White Point: (%.4f, %.4f)\x1b[K", whiteX, whiteY);
                    }

                    if (hasMasteringLuminance) {
                        printf("\n");
                        numLines++;
                        printf("Mastering Display: Max %.1f cd/m², Min %.4f cd/m²\x1b[K",
                               maxMasteringLuminance, minMasteringLuminance);
                    }

                    if (hasMaxCLL || hasMaxFALL) {
                        printf("\n");
                        numLines++;
                        printf("Content Light:");
                        if (hasMaxCLL) {
                            printf(" MaxCLL %.1f cd/m²", maxCLL);
                        }
                        if (hasMaxFALL) {
                            if (hasMaxCLL) printf(",");
                            printf(" MaxFALL %.1f cd/m²", maxFALL);
                        }
                        printf("\x1b[K");
                    }
                }

                printf("\n\x1b[%dA", numLines);
                fflush(stdout);
            }
        }
        return S_OK;
    }
};

void print_usage(const char* programName) {
    printf("Usage: %s [options] [x y]\n", programName);
    printf("Options:\n");
    printf("  -d <index>    Select DeckLink device by index (0-based, default: first with input capability)\n");
    printf("  -i <input>    Select input connection: sdi, hdmi, optical, component, composite, svideo\n");
    printf("                (default: uses currently active input)\n");
    printf("  -m            Print all HDR metadata (primaries, white point, mastering display, content light)\n");
    printf("  -l            List available DeckLink devices and exit\n");
    printf("  -h            Show this help message\n");
    printf("\nArguments:\n");
    printf("  x             X coordinate of pixel to read (default: 960)\n");
    printf("  y             Y coordinate of pixel to read (default: 540)\n");
    printf("\nExamples:\n");
    printf("  %s                      # Use first input device, read pixel at (960, 540)\n", programName);
    printf("  %s 100 200              # Use first input device, read pixel at (100, 200)\n", programName);
    printf("  %s -d 1 100 200         # Use second device, read pixel at (100, 200)\n", programName);
    printf("  %s -i hdmi              # Use HDMI input\n", programName);
    printf("  %s -m                   # Print all HDR metadata\n", programName);
    printf("  %s -d 0 -i sdi 100 200  # Use first device, SDI input, pixel at (100, 200)\n", programName);
    printf("  %s -l                   # List all devices\n", programName);
}

void list_devices() {
    IDeckLinkIterator* deckLinkIterator = NULL;
    IDeckLink* deckLink = NULL;
    STRINGOBJ deviceNameString = NULL;
    int deviceIndex = 0;

    Initialize();

    if (GetDeckLinkIterator(&deckLinkIterator) == NULL) {
        fprintf(stderr, "Could not create DeckLink iterator\n");
        return;
    }

    printf("Available DeckLink devices:\n");
    while (deckLinkIterator->Next(&deckLink) == S_OK) {
        deckLink->GetDisplayName(&deviceNameString);
        std::string deviceName;
        StringToStdString(deviceNameString, deviceName);
        STRINGFREE(deviceNameString);

        // Check if device has input capability
        IDeckLinkInput* deckLinkInput = NULL;
        bool hasInput = (deckLink->QueryInterface(IID_IDeckLinkInput, (void**)&deckLinkInput) == S_OK);
        if (hasInput && deckLinkInput) {
            deckLinkInput->Release();
        }

        printf("  [%d] %s%s\n", deviceIndex, deviceName.c_str(), hasInput ? " (input capable)" : "");

        // List available inputs if device has input capability
        if (hasInput) {
            IDeckLinkProfileAttributes* deckLinkAttributes = NULL;
            if (deckLink->QueryInterface(IID_IDeckLinkProfileAttributes, (void**)&deckLinkAttributes) == S_OK) {
                int64_t availableInputs = 0;
                if (deckLinkAttributes->GetInt(BMDDeckLinkVideoInputConnections, &availableInputs) == S_OK) {
                    printf("      Available inputs:");
                    bool first = true;
                    if (availableInputs & bmdVideoConnectionSDI) {
                        printf("%s sdi", first ? "" : ",");
                        first = false;
                    }
                    if (availableInputs & bmdVideoConnectionHDMI) {
                        printf("%s hdmi", first ? "" : ",");
                        first = false;
                    }
                    if (availableInputs & bmdVideoConnectionOpticalSDI) {
                        printf("%s optical", first ? "" : ",");
                        first = false;
                    }
                    if (availableInputs & bmdVideoConnectionComponent) {
                        printf("%s component", first ? "" : ",");
                        first = false;
                    }
                    if (availableInputs & bmdVideoConnectionComposite) {
                        printf("%s composite", first ? "" : ",");
                        first = false;
                    }
                    if (availableInputs & bmdVideoConnectionSVideo) {
                        printf("%s svideo", first ? "" : ",");
                        first = false;
                    }
                    printf("\n");
                }
                deckLinkAttributes->Release();
            }
        }

        deckLink->Release();
        deviceIndex++;
    }

    if (deviceIndex == 0) {
        printf("  No devices found\n");
    }

    deckLinkIterator->Release();
}

int main(int argc, char** argv)
{
    int deviceIndex = -1;  // -1 means auto-select first input capable device
    bool listDevicesFlag = false;
    BMDVideoConnection inputConnection = 0;  // 0 means use current/default input
    const char* inputConnectionStr = NULL;

    // Parse command line arguments
    int argIndex = 1;
    while (argIndex < argc) {
        if (argv[argIndex][0] == '-') {
            if (strcmp(argv[argIndex], "-d") == 0) {
                if (argIndex + 1 < argc) {
                    deviceIndex = atoi(argv[argIndex + 1]);
                    argIndex += 2;
                } else {
                    fprintf(stderr, "Error: -d requires a device index\n");
                    print_usage(argv[0]);
                    return 1;
                }
            } else if (strcmp(argv[argIndex], "-i") == 0) {
                if (argIndex + 1 < argc) {
                    inputConnectionStr = argv[argIndex + 1];
                    // Parse input connection type
                    if (strcasecmp(inputConnectionStr, "sdi") == 0) {
                        inputConnection = bmdVideoConnectionSDI;
                    } else if (strcasecmp(inputConnectionStr, "hdmi") == 0) {
                        inputConnection = bmdVideoConnectionHDMI;
                    } else if (strcasecmp(inputConnectionStr, "optical") == 0) {
                        inputConnection = bmdVideoConnectionOpticalSDI;
                    } else if (strcasecmp(inputConnectionStr, "component") == 0) {
                        inputConnection = bmdVideoConnectionComponent;
                    } else if (strcasecmp(inputConnectionStr, "composite") == 0) {
                        inputConnection = bmdVideoConnectionComposite;
                    } else if (strcasecmp(inputConnectionStr, "svideo") == 0) {
                        inputConnection = bmdVideoConnectionSVideo;
                    } else {
                        fprintf(stderr, "Error: Unknown input connection '%s'\n", inputConnectionStr);
                        fprintf(stderr, "Valid options: sdi, hdmi, optical, component, composite, svideo\n");
                        return 1;
                    }
                    argIndex += 2;
                } else {
                    fprintf(stderr, "Error: -i requires an input type\n");
                    print_usage(argv[0]);
                    return 1;
                }
            } else if (strcmp(argv[argIndex], "-m") == 0) {
                printHDRMetadata = true;
                argIndex++;
            } else if (strcmp(argv[argIndex], "-l") == 0) {
                listDevicesFlag = true;
                argIndex++;
            } else if (strcmp(argv[argIndex], "-h") == 0 || strcmp(argv[argIndex], "--help") == 0) {
                print_usage(argv[0]);
                return 0;
            } else {
                fprintf(stderr, "Error: Unknown option %s\n", argv[argIndex]);
                print_usage(argv[0]);
                return 1;
            }
        } else {
            // Non-option argument, assume it's x coordinate
            if (argIndex + 1 < argc) {
                x = atoi(argv[argIndex]);
                y = atoi(argv[argIndex + 1]);
                argIndex += 2;
            } else {
                fprintf(stderr, "Error: Both x and y coordinates required\n");
                print_usage(argv[0]);
                return 1;
            }
        }
    }

    if (listDevicesFlag) {
        list_devices();
        return 0;
    }

    IDeckLinkIterator* deckLinkIterator = NULL;
    IDeckLinkProfileAttributes* deckLinkAttributes = NULL;
    IDeckLink* deckLink = NULL;
    IDeckLinkInput* deckLinkInput = NULL;
    IDeckLinkConfiguration* deckLinkConfiguration = NULL;  // Keep this alive for the session
    NotificationCallback* notificationCallback = NULL;

    HRESULT result;
    BOOL supported;
    int returnCode = 1;

    Initialize();

    // Create an IDeckLinkIterator object to enumerate all DeckLink cards in the system
    result = S_OK;

    // Declare variables before any goto statements
    int currentIndex = 0;
    bool foundDevice = false;

    if (GetDeckLinkIterator(&deckLinkIterator) == NULL)
    {
        fprintf(stderr, "A DeckLink iterator could not be created. The DeckLink drivers may not be installed.\n");
        goto bail;
    }

    // Find the requested device

    while (deckLinkIterator->Next(&deckLink) == S_OK) {
        // If device index specified, check if this is the one
        if (deviceIndex >= 0) {
            if (currentIndex == deviceIndex) {
                foundDevice = true;
                break;
            }
            currentIndex++;
            deckLink->Release();
            deckLink = NULL;
        } else {
            // Auto-select: find first device with input capability
            IDeckLinkInput* testInput = NULL;
            if (deckLink->QueryInterface(IID_IDeckLinkInput, (void**)&testInput) == S_OK) {
                testInput->Release();
                foundDevice = true;
                printf("Auto-selected device [%d]\n", currentIndex);
                break;
            }
            currentIndex++;
            deckLink->Release();
            deckLink = NULL;
        }
    }

    if (!foundDevice || deckLink == NULL) {
        if (deviceIndex >= 0) {
            fprintf(stderr, "Could not find DeckLink device at index %d\n", deviceIndex);
        } else {
            fprintf(stderr, "Could not find any DeckLink device with input capability\n");
        }
        goto bail;
    }

    // Obtain the Attributes interface for the DeckLink device
    result = deckLink->QueryInterface(IID_IDeckLinkProfileAttributes, (void**)&deckLinkAttributes);
    if (result != S_OK)
    {
        fprintf(stderr, "Could not obtain the IDeckLinkProfileAttributes interface - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    // Determine whether the DeckLink device supports input format detection
    result = deckLinkAttributes->GetFlag(BMDDeckLinkSupportsInputFormatDetection, &supported);
    if ((result != S_OK) || (supported == false))
    {
        fprintf(stderr, "Device does not support automatic mode detection\n");
        goto bail;
    }

    // Get the configuration interface and keep it alive
    result = deckLink->QueryInterface(IID_IDeckLinkConfiguration, (void**)&deckLinkConfiguration);
    if (result != S_OK) {
        fprintf(stderr, "Could not obtain the IDeckLinkConfiguration interface - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    // Configure input connection BEFORE obtaining the input interface
    if (inputConnection != 0) {
        result = deckLinkConfiguration->SetInt(bmdDeckLinkConfigVideoInputConnection, inputConnection);

        if (result != S_OK) {
            fprintf(stderr, "Could not set input connection to %s - result = %08x\n", inputConnectionStr, (unsigned int)result);
            fprintf(stderr, "The device may not support this input type\n");
            goto bail;
        }
    }

    // Obtain the input interface for the DeckLink device AFTER configuring input connection
    result = deckLink->QueryInterface(IID_IDeckLinkInput, (void**)&deckLinkInput);
    if (result != S_OK)
    {
        fprintf(stderr, "Could not obtain the IDeckLinkInput interface - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    // Create an instance of notification callback
    notificationCallback = new NotificationCallback(deckLinkInput);
    if (notificationCallback == NULL)
    {
        fprintf(stderr, "Could not create notification callback object\n");
        goto bail;
    }

    // Set the callback object to the DeckLink device's input interface
    result = deckLinkInput->SetCallback(notificationCallback);
    if (result != S_OK)
    {
        fprintf(stderr, "Could not set callback - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    // Enable video input with a default video mode and the automatic format detection feature enabled
    result = deckLinkInput->EnableVideoInput(bmdModeNTSC, bmdFormat10BitYUV, bmdVideoInputEnableFormatDetection);
    if (result != S_OK)
    {
        fprintf(stderr, "Could not enable video input - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    printf("Initialising...\n");

    // Start capture
    result = deckLinkInput->StartStreams();
    if (result != S_OK)
    {
        fprintf(stderr, "Could not start capture - result = %08x\n", (unsigned int)result);
        goto bail;
    }

    printf("Reading input signal...\n");
    printf("Coordinates: (%d, %d)\n", x, y);
    printf("Press ENTER to exit\n\n\n");

    getchar();

    printf("\n\n\n\nExiting.\n");

    // Stop capture
    result = deckLinkInput->StopStreams();

    // Disable the video input interface
    result = deckLinkInput->DisableVideoInput();

    // return success
    returnCode = 0;

    // Release resources
bail:

    // Release the attributes interface
    if (deckLinkAttributes != NULL)
        deckLinkAttributes->Release();

    // Release the configuration interface
    if (deckLinkConfiguration != NULL)
        deckLinkConfiguration->Release();

    // Release the video input interface
    if (deckLinkInput != NULL)
        deckLinkInput->Release();

    // Release the Decklink object
    if (deckLink != NULL)
        deckLink->Release();

    // Release the DeckLink iterator
    if (deckLinkIterator != NULL)
        deckLinkIterator->Release();

    // Release the notification callback object
    if (notificationCallback)
        delete notificationCallback;

    return returnCode;
}
