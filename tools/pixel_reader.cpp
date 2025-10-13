#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <string>
#include <stdint.h>

#ifdef __APPLE__
    #include <pthread.h>
    #include <CoreFoundation/CoreFoundation.h>
    #include "decklink_sdk/Mac/include/DeckLinkAPI.h"
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
    #include "decklink_sdk/Linux/include/DeckLinkAPI.h"
    #include "decklink_sdk/Linux/include/LinuxCOM.h"
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
    #include "decklink_sdk/Win/include/DeckLinkAPI.h"
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

    // Clamp coordinates
    if (pixelX < 0) pixelX = 0;
    if (pixelY < 0) pixelY = 0;
    if (pixelX >= width) pixelX = width - 1;
    if (pixelY >= height) pixelY = height - 1;

    switch (format) {
        case bmdFormat10BitYUV: {
            // v210 format: 4 pixels in 16 bytes (128 bits)
            // Each group of 4 pixels is packed as: U0 Y0 V0 Y1 U2 Y2 V2 Y3
            // Each component is 10 bits
            UINT32* line = (UINT32*)(buffer + pixelY * rowBytes);
            int groupIndex = (pixelX / 6) * 4; // Each group of 4 UINT32s contains 6 pixels
            int pixelInGroup = pixelX % 6;

            UINT32 d0 = line[groupIndex];
            UINT32 d1 = line[groupIndex + 1];
            UINT32 d2 = line[groupIndex + 2];

            // Extract based on position in group
            // Format: bits [9:0] Cb0, [19:10] Y0, [29:20] Cr0
            if (pixelInGroup == 0 || pixelInGroup == 1) {
                result.comp1 = (d0 >> 10) & 0x3FF; // Y
                result.comp2 = d0 & 0x3FF;         // Cb
                result.comp3 = (d0 >> 20) & 0x3FF; // Cr
            } else if (pixelInGroup == 2 || pixelInGroup == 3) {
                result.comp1 = (d1 >> 10) & 0x3FF; // Y
                result.comp2 = d1 & 0x3FF;         // Cb
                result.comp3 = (d1 >> 20) & 0x3FF; // Cr
            } else {
                result.comp1 = (d2 >> 10) & 0x3FF; // Y
                result.comp2 = d2 & 0x3FF;         // Cb
                result.comp3 = (d2 >> 20) & 0x3FF; // Cr
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
            // R12L format: Little-endian RGB 12-bit
            UINT16* line = (UINT16*)(buffer + pixelY * rowBytes);
            int pixelIndex = pixelX * 3;
            result.comp1 = line[pixelIndex] & 0xFFF;            // R
            result.comp2 = line[pixelIndex + 1] & 0xFFF;        // G
            result.comp3 = line[pixelIndex + 2] & 0xFFF;        // B
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

    // The callback that is called when a property of the video input stream has changed.
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

            printf("Input color space changed:\x1b[K\n");  // \x1b[K clears to end of line
            printf("  Color space: ");
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
            printf("\x1b[K\n");  // Clear to end of line

            printf("  Pixel format: %s\x1b[K\n\n", GetPixelFormatName(currentPixelFormat));
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

                metadataExt->Release();
            }

            counter += 1;
            if (counter > 1) {
                int numLines = 2;  // Start with 2 lines (blank + pixel values)

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
                printf("\n\x1b[%dA", numLines);  // Move cursor up by numLines
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
    printf("  -l            List available DeckLink devices and exit\n");
    printf("  -h            Show this help message\n");
    printf("\nArguments:\n");
    printf("  x             X coordinate of pixel to read (default: 960)\n");
    printf("  y             Y coordinate of pixel to read (default: 540)\n");
    printf("\nExamples:\n");
    printf("  %s                 # Use first input device, read pixel at (960, 540)\n", programName);
    printf("  %s 100 200         # Use first input device, read pixel at (100, 200)\n", programName);
    printf("  %s -d 1 100 200    # Use second device, read pixel at (100, 200)\n", programName);
    printf("  %s -l              # List all devices\n", programName);
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

    // Obtain the input interface for the DeckLink device
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
