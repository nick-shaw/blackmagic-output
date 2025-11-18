#include "decklink_wrapper.hpp"
#include "decklink_hdr_frame.hpp"
#include <iostream>
#include <cstring>

#ifdef __APPLE__
    #include <CoreFoundation/CoreFoundation.h>
#endif

#ifdef _WIN32
    #include <comutil.h>
    // Windows needs CoCreateInstance to create the DeckLink iterator
    IDeckLinkIterator* CreateDeckLinkIteratorInstance() {
        IDeckLinkIterator* iterator = nullptr;
        HRESULT result = CoCreateInstance(CLSID_CDeckLinkIterator, nullptr, CLSCTX_ALL,
                                         IID_IDeckLinkIterator, (void**)&iterator);
        if (FAILED(result)) {
            return nullptr;
        }
        return iterator;
    }
#endif

DeckLinkOutput::DeckLinkOutput()
    : m_deckLink(nullptr)
    , m_deckLinkOutput(nullptr)
    , m_deckLinkConfiguration(nullptr)
    , m_outputEnabled(false)
    , m_frameDuration(0)
    , m_timeScale(0)
    , m_useHdrMetadata(false)
    , m_hdrColorimetry(Gamut::Rec709)
    , m_hdrEotf(Eotf::SDR)
{
}

DeckLinkOutput::~DeckLinkOutput()
{
    cleanup();
}

bool DeckLinkOutput::initialize(int deviceIndex)
{
    IDeckLinkIterator* deckLinkIterator = CreateDeckLinkIteratorInstance();
    if (!deckLinkIterator) {
        std::cerr << "Could not create DeckLink iterator" << std::endl;
        return false;
    }

    // Get the specified device
    IDeckLink* deckLink = nullptr;
    for (int i = 0; i <= deviceIndex; i++) {
        if (deckLink) {
            deckLink->Release();
        }
        if (deckLinkIterator->Next(&deckLink) != S_OK) {
            std::cerr << "Could not find DeckLink device at index " << deviceIndex << std::endl;
            deckLinkIterator->Release();
            return false;
        }
    }

    deckLinkIterator->Release();
    
    m_deckLink = deckLink;

    // Get output interface
    if (m_deckLink->QueryInterface(IID_IDeckLinkOutput, (void**)&m_deckLinkOutput) != S_OK) {
        std::cerr << "Could not get IDeckLinkOutput interface" << std::endl;
        return false;
    }

    // Get configuration interface
    if (m_deckLink->QueryInterface(IID_IDeckLinkConfiguration, (void**)&m_deckLinkConfiguration) != S_OK) {
        std::cerr << "Could not get IDeckLinkConfiguration interface" << std::endl;
        return false;
    }

    return true;
}

bool DeckLinkOutput::setupOutput(const VideoSettings& settings)
{
    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return false;
    }

    m_currentSettings = settings;

    // Get display mode iterator and find the mode
    IDeckLinkDisplayModeIterator* displayModeIterator = nullptr;
    if (m_deckLinkOutput->GetDisplayModeIterator(&displayModeIterator) != S_OK) {
        std::cerr << "Could not get display mode iterator" << std::endl;
        return false;
    }

    IDeckLinkDisplayMode* displayMode = nullptr;
    bool modeFound = false;
    
    while (displayModeIterator->Next(&displayMode) == S_OK) {
        BMDDisplayMode mode = displayMode->GetDisplayMode();
        if (mode == static_cast<BMDDisplayMode>(settings.mode)) {
            displayMode->GetFrameRate(&m_frameDuration, &m_timeScale);
            modeFound = true;
            displayMode->Release();
            break;
        }
        displayMode->Release();
    }
    
    displayModeIterator->Release();

    if (!modeFound) {
        std::cerr << "Could not find display mode" << std::endl;
        return false;
    }

    // Configure RGB 4:4:4 mode if using RGB formats (Linux/Windows may not support this)
    if (m_deckLinkConfiguration) {
        if (settings.format == PixelFormat::Format10BitRGB || settings.format == PixelFormat::Format12BitRGB) {
            m_deckLinkConfiguration->SetFlag(bmdDeckLinkConfig444SDIVideoOutput, true);
        } else {
            m_deckLinkConfiguration->SetFlag(bmdDeckLinkConfig444SDIVideoOutput, false);
        }
    }

    // If already enabled with a different mode, disable first
    if (m_outputEnabled && m_currentSettings.mode != settings.mode) {
        m_deckLinkOutput->DisableVideoOutput();
        m_outputEnabled = false;
    }

    // Enable video output only if not already enabled
    if (!m_outputEnabled) {
        if (m_deckLinkOutput->EnableVideoOutput(static_cast<BMDDisplayMode>(settings.mode),
                                               bmdVideoOutputFlagDefault) != S_OK) {
            std::cerr << "Could not enable video output" << std::endl;
            return false;
        }
        m_outputEnabled = true;
    }

    // Calculate frame buffer size
    size_t frameSize;
    switch (settings.format) {
        case PixelFormat::Format8BitBGRA:
            frameSize = settings.width * settings.height * 4;
            break;
        case PixelFormat::Format10BitYUV:
            // v210 format: 6 pixels in 4 32-bit words (16 bytes)
            frameSize = ((settings.width + 5) / 6) * 16 * settings.height;
            break;
        case PixelFormat::Format10BitRGB:
            // bmdFormat10BitRGBXLE: 4 bytes per pixel
            frameSize = settings.width * settings.height * 4;
            break;
        case PixelFormat::Format12BitRGB:
            // bmdFormat12BitRGBLE: 36 bits per pixel, 8 pixels in 36 bytes
            frameSize = ((settings.width + 7) / 8) * 36 * settings.height;
            break;
        case PixelFormat::Format8BitYUV:
        default:
            frameSize = settings.width * settings.height * 2;
            break;
    }

    m_frameBuffer.resize(frameSize);
    
    return true;
}

bool DeckLinkOutput::setFrameData(const uint8_t* data, size_t dataSize)
{
    std::lock_guard<std::mutex> lock(m_frameBufferMutex);
    
    if (dataSize > m_frameBuffer.size()) {
        std::cerr << "Frame data too large" << std::endl;
        return false;
    }
    
    std::memcpy(m_frameBuffer.data(), data, dataSize);
    return true;
}

bool DeckLinkOutput::createFrame(IDeckLinkMutableVideoFrame** frame)
{
    std::lock_guard<std::mutex> lock(m_frameBufferMutex);

    int32_t rowBytes;
    switch (m_currentSettings.format) {
        case PixelFormat::Format8BitBGRA:
            rowBytes = m_currentSettings.width * 4;
            break;
        case PixelFormat::Format10BitYUV:
            // v210 format: 6 pixels in 4 32-bit words (16 bytes)
            rowBytes = ((m_currentSettings.width + 5) / 6) * 16;
            break;
        case PixelFormat::Format10BitRGB:
            // bmdFormat10BitRGBXLE: 4 bytes per pixel
            rowBytes = m_currentSettings.width * 4;
            break;
        case PixelFormat::Format12BitRGB:
            // bmdFormat12BitRGBLE: 36 bits per pixel, 8 pixels in 36 bytes
            rowBytes = ((m_currentSettings.width + 7) / 8) * 36;
            break;
        case PixelFormat::Format8BitYUV:
        default:
            rowBytes = m_currentSettings.width * 2;
            break;
    }

    if (m_deckLinkOutput->CreateVideoFrame(
            m_currentSettings.width,
            m_currentSettings.height,
            rowBytes,
            static_cast<BMDPixelFormat>(m_currentSettings.format),
            bmdFrameFlagDefault,
            frame) != S_OK) {
        return false;
    }

    void* frameBuffer;
    if ((*frame)->GetBytes(&frameBuffer) == S_OK) {
        std::memcpy(frameBuffer, m_frameBuffer.data(), m_frameBuffer.size());
    }

    return true;
}

bool DeckLinkOutput::displayFrame()
{
    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return false;
    }

    // Create frame with current buffer data
    IDeckLinkMutableVideoFrame* mutableFrame = nullptr;
    if (!createFrame(&mutableFrame)) {
        std::cerr << "Could not create frame" << std::endl;
        return false;
    }

    IDeckLinkVideoFrame* frame = mutableFrame;

    // Wrap with HDR metadata if needed
    if (m_useHdrMetadata) {
        frame = createHdrFrame(mutableFrame);
        mutableFrame->Release();
    }

    // Display frame synchronously
    HRESULT result = m_deckLinkOutput->DisplayVideoFrameSync(frame);
    frame->Release();

    if (result != S_OK) {
        std::cerr << "Could not display video frame" << std::endl;
        return false;
    }

    return true;
}

bool DeckLinkOutput::stopOutput()
{
    if (m_outputEnabled && m_deckLinkOutput) {
        m_deckLinkOutput->DisableVideoOutput();
        m_outputEnabled = false;
    }
    return true;
}

void DeckLinkOutput::cleanup()
{
    stopOutput();

    if (m_deckLinkConfiguration) {
        m_deckLinkConfiguration->Release();
        m_deckLinkConfiguration = nullptr;
    }

    if (m_deckLinkOutput) {
        m_deckLinkOutput->Release();
        m_deckLinkOutput = nullptr;
    }

    if (m_deckLink) {
        m_deckLink->Release();
        m_deckLink = nullptr;
    }
}

void DeckLinkOutput::setHdrMetadata(Gamut colorimetry, Eotf eotf)
{
    m_useHdrMetadata = true;
    m_hdrColorimetry = colorimetry;
    m_hdrEotf = eotf;

    // PQ requires primaries and luminance metadata
    // HLG only needs colorimetry and EOTF
    if (eotf == Eotf::PQ) {
        // Set display primaries based on the matrix/colorimetry
        if (colorimetry == Gamut::Rec2020) {
            // Rec.2020 primaries
            m_hdrCustom.displayPrimariesRedX = 0.708;
            m_hdrCustom.displayPrimariesRedY = 0.292;
            m_hdrCustom.displayPrimariesGreenX = 0.170;
            m_hdrCustom.displayPrimariesGreenY = 0.797;
            m_hdrCustom.displayPrimariesBlueX = 0.131;
            m_hdrCustom.displayPrimariesBlueY = 0.046;
        } else {
            // Rec.709 primaries
            m_hdrCustom.displayPrimariesRedX = 0.64;
            m_hdrCustom.displayPrimariesRedY = 0.33;
            m_hdrCustom.displayPrimariesGreenX = 0.30;
            m_hdrCustom.displayPrimariesGreenY = 0.60;
            m_hdrCustom.displayPrimariesBlueX = 0.15;
            m_hdrCustom.displayPrimariesBlueY = 0.06;
        }

        // D65 white point (same for both Rec.709 and Rec.2020)
        m_hdrCustom.whitePointX = 0.3127;
        m_hdrCustom.whitePointY = 0.3290;

        // Set luminance values for PQ
        m_hdrCustom.maxMasteringLuminance = 1000.0;
        m_hdrCustom.minMasteringLuminance = 0.0001;
        m_hdrCustom.maxContentLightLevel = 1000.0;
        m_hdrCustom.maxFrameAverageLightLevel = 50.0;
    } else {
        // For HLG and SDR, set neutral/zero values for primaries and luminance
        m_hdrCustom.displayPrimariesRedX = 0.0;
        m_hdrCustom.displayPrimariesRedY = 0.0;
        m_hdrCustom.displayPrimariesGreenX = 0.0;
        m_hdrCustom.displayPrimariesGreenY = 0.0;
        m_hdrCustom.displayPrimariesBlueX = 0.0;
        m_hdrCustom.displayPrimariesBlueY = 0.0;
        m_hdrCustom.whitePointX = 0.0;
        m_hdrCustom.whitePointY = 0.0;
        m_hdrCustom.maxMasteringLuminance = 0.0;
        m_hdrCustom.minMasteringLuminance = 0.0;
        m_hdrCustom.maxContentLightLevel = 0.0;
        m_hdrCustom.maxFrameAverageLightLevel = 0.0;
    }
}

void DeckLinkOutput::setHdrMetadataCustom(Gamut colorimetry, Eotf eotf, const HdrMetadataCustom& custom)
{
    m_useHdrMetadata = true;
    m_hdrColorimetry = colorimetry;
    m_hdrEotf = eotf;
    m_hdrCustom = custom;
}

void DeckLinkOutput::clearHdrMetadata()
{
    m_useHdrMetadata = false;
    m_hdrColorimetry = Gamut::Rec709;
    m_hdrEotf = Eotf::SDR;
    // Zero out custom metadata
    m_hdrCustom.displayPrimariesRedX = 0.0;
    m_hdrCustom.displayPrimariesRedY = 0.0;
    m_hdrCustom.displayPrimariesGreenX = 0.0;
    m_hdrCustom.displayPrimariesGreenY = 0.0;
    m_hdrCustom.displayPrimariesBlueX = 0.0;
    m_hdrCustom.displayPrimariesBlueY = 0.0;
    m_hdrCustom.whitePointX = 0.0;
    m_hdrCustom.whitePointY = 0.0;
    m_hdrCustom.maxMasteringLuminance = 0.0;
    m_hdrCustom.minMasteringLuminance = 0.0;
    m_hdrCustom.maxContentLightLevel = 0.0;
    m_hdrCustom.maxFrameAverageLightLevel = 0.0;
}

IDeckLinkVideoFrame* DeckLinkOutput::createHdrFrame(IDeckLinkMutableVideoFrame* frame)
{
    HdrMetadata::ChromaticityCoordinates primaries = {
        m_hdrCustom.displayPrimariesRedX,
        m_hdrCustom.displayPrimariesRedY,
        m_hdrCustom.displayPrimariesGreenX,
        m_hdrCustom.displayPrimariesGreenY,
        m_hdrCustom.displayPrimariesBlueX,
        m_hdrCustom.displayPrimariesBlueY,
        m_hdrCustom.whitePointX,
        m_hdrCustom.whitePointY
    };

    HdrMetadata metadata = HdrMetadata::custom(
        m_hdrColorimetry,
        m_hdrEotf,
        primaries,
        m_hdrCustom.maxMasteringLuminance,
        m_hdrCustom.minMasteringLuminance,
        m_hdrCustom.maxContentLightLevel,
        m_hdrCustom.maxFrameAverageLightLevel
    );

    return new DeckLinkHdrVideoFrame(frame, metadata);
}

std::vector<std::string> DeckLinkOutput::getDeviceList()
{
    std::vector<std::string> devices;

    IDeckLinkIterator* deckLinkIterator = CreateDeckLinkIteratorInstance();
    if (!deckLinkIterator) {
        return devices;
    }

    IDeckLink* deckLink = nullptr;
    while (deckLinkIterator->Next(&deckLink) == S_OK) {
#ifdef __APPLE__
        CFStringRef deviceNameRef = nullptr;
        if (deckLink->GetDisplayName(&deviceNameRef) == S_OK) {
            // Convert CFString to std::string
            CFIndex length = CFStringGetLength(deviceNameRef);
            CFIndex maxSize = CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8) + 1;
            char* buffer = new char[maxSize];

            if (CFStringGetCString(deviceNameRef, buffer, maxSize, kCFStringEncodingUTF8)) {
                devices.push_back(std::string(buffer));
            }

            delete[] buffer;
            CFRelease(deviceNameRef);
        }
#elif defined(_WIN32)
        BSTR deviceNameBSTR = nullptr;
        if (deckLink->GetDisplayName(&deviceNameBSTR) == S_OK) {
            // Convert BSTR to std::string
            _bstr_t bstr(deviceNameBSTR, false); // false = don't copy, we'll free it
            devices.push_back(std::string((const char*)bstr));
            SysFreeString(deviceNameBSTR);
        }
#else
        const char* deviceName = nullptr;
        if (deckLink->GetDisplayName(&deviceName) == S_OK) {
            devices.push_back(std::string(deviceName));
            free((void*)deviceName);
        }
#endif
        deckLink->Release();
    }

    deckLinkIterator->Release();
    return devices;
}

DeckLinkOutput::VideoSettings DeckLinkOutput::getVideoSettings(DisplayMode mode)
{
    VideoSettings settings;
    settings.mode = mode;
    settings.format = PixelFormat::Format8BitBGRA;

    // Query the hardware for display mode information dynamically
    if (m_deckLinkOutput) {
        IDeckLinkDisplayMode* displayMode = nullptr;
        if (m_deckLinkOutput->GetDisplayMode(static_cast<BMDDisplayMode>(mode), &displayMode) == S_OK) {
            settings.width = displayMode->GetWidth();
            settings.height = displayMode->GetHeight();

            BMDTimeValue frameDuration;
            BMDTimeScale timeScale;
            displayMode->GetFrameRate(&frameDuration, &timeScale);
            settings.framerate = (double)timeScale / (double)frameDuration;

            displayMode->Release();
        } else {
            std::cerr << "Warning: Could not get display mode information for mode "
                      << static_cast<int>(mode) << ", using defaults" << std::endl;
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 25.0;
        }
    } else {
        std::cerr << "Warning: DeckLink output not initialized, using default settings" << std::endl;
        settings.width = 1920;
        settings.height = 1080;
        settings.framerate = 25.0;
    }

    return settings;
}

bool DeckLinkOutput::isPixelFormatSupported(DisplayMode mode, PixelFormat format)
{
    if (!m_deckLinkOutput) {
        return false;
    }

    // Check if the mode/format combination is supported
#ifdef _WIN32
    BOOL supported = FALSE;
#else
    bool supported = false;
#endif
    BMDDisplayMode actualMode;

    HRESULT result = m_deckLinkOutput->DoesSupportVideoMode(
        bmdVideoConnectionUnspecified,
        static_cast<BMDDisplayMode>(mode),
        static_cast<BMDPixelFormat>(format),
        bmdNoVideoOutputConversion,
        bmdSupportedVideoModeDefault,
        &actualMode,
        &supported
    );

#ifdef _WIN32
    return (result == S_OK && supported != FALSE);
#else
    return (result == S_OK && supported);
#endif
}

DeckLinkOutput::OutputInfo DeckLinkOutput::getCurrentOutputInfo()
{
    OutputInfo info;

    info.displayMode = m_currentSettings.mode;
    info.pixelFormat = m_currentSettings.format;
    info.width = m_currentSettings.width;
    info.height = m_currentSettings.height;
    info.framerate = m_currentSettings.framerate;
    info.rgb444ModeEnabled = false;

    // Query RGB 4:4:4 mode status
    if (m_deckLinkConfiguration) {
#ifdef _WIN32
        BOOL flagValue = FALSE;
        if (m_deckLinkConfiguration->GetFlag(bmdDeckLinkConfig444SDIVideoOutput, &flagValue) == S_OK) {
            info.rgb444ModeEnabled = (flagValue != FALSE);
        }
#else
        bool flagValue = false;
        if (m_deckLinkConfiguration->GetFlag(bmdDeckLinkConfig444SDIVideoOutput, &flagValue) == S_OK) {
            info.rgb444ModeEnabled = flagValue;
        }
#endif
    }

    // Get display mode name
    BMDDisplayMode bmdMode = static_cast<BMDDisplayMode>(m_currentSettings.mode);
    IDeckLinkDisplayModeIterator* displayModeIterator = nullptr;
    if (m_deckLinkOutput && m_deckLinkOutput->GetDisplayModeIterator(&displayModeIterator) == S_OK) {
        IDeckLinkDisplayMode* displayMode = nullptr;
        while (displayModeIterator->Next(&displayMode) == S_OK) {
            if (displayMode->GetDisplayMode() == bmdMode) {
#ifdef __APPLE__
                CFStringRef modeName;
                if (displayMode->GetName(&modeName) == S_OK) {
                    char buffer[256];
                    CFStringGetCString(modeName, buffer, sizeof(buffer), kCFStringEncodingUTF8);
                    info.displayModeName = buffer;
                    CFRelease(modeName);
                }
#elif defined(_WIN32)
                BSTR modeName = nullptr;
                if (displayMode->GetName(&modeName) == S_OK) {
                    _bstr_t bstr(modeName, false);
                    info.displayModeName = std::string((const char*)bstr);
                    SysFreeString(modeName);
                }
#else
                const char* modeName = nullptr;
                if (displayMode->GetName(&modeName) == S_OK) {
                    info.displayModeName = modeName;
                    free((void*)modeName);
                }
#endif
                displayMode->Release();
                break;
            }
            displayMode->Release();
        }
        displayModeIterator->Release();
    }

    if (info.displayModeName.empty()) {
        info.displayModeName = "Unknown mode";
    }

    // Get pixel format name
    BMDPixelFormat bmdFormat = static_cast<BMDPixelFormat>(m_currentSettings.format);
    switch (bmdFormat) {
        case bmdFormat8BitYUV:
            info.pixelFormatName = "8-bit YUV (2vuy)";
            break;
        case bmdFormat8BitBGRA:
            info.pixelFormatName = "8-bit BGRA";
            break;
        case bmdFormat10BitYUV:
            info.pixelFormatName = "10-bit YUV (v210)";
            break;
        case bmdFormat10BitRGBXLE:
            info.pixelFormatName = "10-bit RGB LE (R10l)";
            break;
        case bmdFormat12BitRGBLE:
            info.pixelFormatName = "12-bit RGB LE (R12L)";
            break;
        default:
            info.pixelFormatName = "Unknown format";
            break;
    }

    return info;
}

std::vector<DeckLinkOutput::DisplayModeInfo> DeckLinkOutput::getSupportedDisplayModes()
{
    std::vector<DisplayModeInfo> modes;

    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return modes;
    }

    IDeckLinkDisplayModeIterator* displayModeIterator = nullptr;
    if (m_deckLinkOutput->GetDisplayModeIterator(&displayModeIterator) != S_OK) {
        std::cerr << "Could not get display mode iterator" << std::endl;
        return modes;
    }

    IDeckLinkDisplayMode* displayMode = nullptr;
    while (displayModeIterator->Next(&displayMode) == S_OK) {
        DisplayModeInfo modeInfo;

        modeInfo.displayMode = static_cast<DisplayMode>(displayMode->GetDisplayMode());
        modeInfo.width = displayMode->GetWidth();
        modeInfo.height = displayMode->GetHeight();

        BMDTimeValue frameDuration;
        BMDTimeScale timeScale;
        displayMode->GetFrameRate(&frameDuration, &timeScale);
        modeInfo.framerate = (double)timeScale / (double)frameDuration;

#ifdef _WIN32
        BSTR nameString;
        if (displayMode->GetName(&nameString) == S_OK) {
            int nameLen = WideCharToMultiByte(CP_UTF8, 0, nameString, -1, nullptr, 0, nullptr, nullptr);
            if (nameLen > 0) {
                std::vector<char> nameBuffer(nameLen);
                WideCharToMultiByte(CP_UTF8, 0, nameString, -1, nameBuffer.data(), nameLen, nullptr, nullptr);
                modeInfo.name = std::string(nameBuffer.data());
            }
            SysFreeString(nameString);
        }
#else
        const char* nameString;
        if (displayMode->GetName(&nameString) == S_OK) {
            modeInfo.name = std::string(nameString);
        }
#endif

        modes.push_back(modeInfo);
        displayMode->Release();
    }

    displayModeIterator->Release();
    return modes;
}