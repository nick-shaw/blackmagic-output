#include "decklink_input.hpp"
#include <iostream>
#include <cstring>
#include <chrono>

#ifdef __APPLE__
    #include <CoreFoundation/CoreFoundation.h>
#endif

class DeckLinkInputCallback : public IDeckLinkInputCallback {
public:
    DeckLinkInputCallback(DeckLinkInput* parent) : m_parent(parent), m_refCount(1) {}

    virtual HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, LPVOID* ppv) override {
#ifdef __APPLE__
        CFUUIDBytes iunknown = CFUUIDGetUUIDBytes(IUnknownUUID);
        if (memcmp(&iid, &iunknown, sizeof(REFIID)) == 0) {
            *ppv = static_cast<IDeckLinkInputCallback*>(this);
        } else if (memcmp(&iid, &IID_IDeckLinkInputCallback, sizeof(REFIID)) == 0) {
            *ppv = static_cast<IDeckLinkInputCallback*>(this);
        } else {
            *ppv = nullptr;
            return E_NOINTERFACE;
        }
#else
        REFIID iunknown = IID_IUnknown;
        REFIID inputCallback = IID_IDeckLinkInputCallback;
        if (memcmp(&iid, &iunknown, sizeof(REFIID)) == 0) {
            *ppv = static_cast<IDeckLinkInputCallback*>(this);
        } else if (memcmp(&iid, &inputCallback, sizeof(REFIID)) == 0) {
            *ppv = static_cast<IDeckLinkInputCallback*>(this);
        } else {
            *ppv = nullptr;
            return E_NOINTERFACE;
        }
#endif
        AddRef();
        return S_OK;
    }

    virtual ULONG STDMETHODCALLTYPE AddRef() override {
        return ++m_refCount;
    }

    virtual ULONG STDMETHODCALLTYPE Release() override {
        ULONG newRefValue = --m_refCount;
        if (newRefValue == 0) {
            delete this;
        }
        return newRefValue;
    }

    virtual HRESULT STDMETHODCALLTYPE VideoInputFormatChanged(
        BMDVideoInputFormatChangedEvents notificationEvents,
        IDeckLinkDisplayMode* newDisplayMode,
        BMDDetectedVideoInputFormatFlags detectedSignalFlags) override {
        if (m_parent && newDisplayMode) {
            m_parent->onFormatChanged(newDisplayMode, detectedSignalFlags);
        }
        return S_OK;
    }

    virtual HRESULT STDMETHODCALLTYPE VideoInputFrameArrived(
        IDeckLinkVideoInputFrame* videoFrame,
        IDeckLinkAudioInputPacket* audioPacket) override {
        if (videoFrame && m_parent) {
            m_parent->onFrameArrived(videoFrame);
        }
        return S_OK;
    }

private:
    DeckLinkInput* m_parent;
    std::atomic<ULONG> m_refCount;
};

DeckLinkInput::DeckLinkInput()
    : m_deckLink(nullptr)
    , m_deckLinkInput(nullptr)
    , m_callback(nullptr)
    , m_inputEnabled(false)
    , m_frameReceived(false)
    , m_formatDetected(false)
{
    m_lastFrame.valid = false;
}

DeckLinkInput::~DeckLinkInput()
{
    cleanup();
}

bool DeckLinkInput::initialize(int deviceIndex)
{
    IDeckLinkIterator* deckLinkIterator = DeckLink::CreateDeckLinkIteratorInstance();
    if (!deckLinkIterator) {
        std::cerr << "Could not create DeckLink iterator" << std::endl;
        return false;
    }

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

    if (m_deckLink->QueryInterface(IID_IDeckLinkInput, (void**)&m_deckLinkInput) != S_OK) {
        std::cerr << "Could not get IDeckLinkInput interface" << std::endl;
        return false;
    }

    m_callback = new DeckLinkInputCallback(this);
    if (m_deckLinkInput->SetCallback(m_callback) != S_OK) {
        std::cerr << "Could not set input callback" << std::endl;
        return false;
    }

    return true;
}

bool DeckLinkInput::startCapture()
{
    if (!m_deckLinkInput) {
        std::cerr << "DeckLink input not initialized" << std::endl;
        return false;
    }

    if (m_inputEnabled) {
        m_deckLinkInput->DisableVideoInput();
        m_inputEnabled = false;
    }

    m_currentSettings.format = PixelFormat::Format10BitYUV;
    m_formatDetected = false;

    if (m_deckLinkInput->EnableVideoInput(
            bmdModeHD1080p2997,
            bmdFormat10BitYUV,
            bmdVideoInputEnableFormatDetection) != S_OK) {
        std::cerr << "Could not enable video input with format detection" << std::endl;
        return false;
    }
    m_inputEnabled = true;

    if (m_deckLinkInput->StartStreams() != S_OK) {
        std::cerr << "Could not start input streams" << std::endl;
        return false;
    }

    return true;
}

bool DeckLinkInput::captureFrame(CapturedFrame& frame, int timeoutMs)
{
    if (!m_inputEnabled) {
        std::cerr << "Input not enabled" << std::endl;
        return false;
    }

    m_frameReceived = false;

    std::unique_lock<std::mutex> lock(m_frameMutex);
    if (!m_frameCondition.wait_for(lock, std::chrono::milliseconds(timeoutMs),
                                   [this] { return m_frameReceived.load(); })) {
        std::cerr << "Timeout waiting for frame" << std::endl;
        return false;
    }

    if (!m_lastFrame.valid) {
        std::cerr << "Invalid frame received" << std::endl;
        return false;
    }

    frame = m_lastFrame;
    return true;
}

void DeckLinkInput::onFrameArrived(IDeckLinkVideoInputFrame* videoFrame)
{
    std::lock_guard<std::mutex> lock(m_frameMutex);

    m_lastFrame.width = videoFrame->GetWidth();
    m_lastFrame.height = videoFrame->GetHeight();
    m_lastFrame.format = m_currentSettings.format;
    m_lastFrame.mode = m_currentSettings.mode;

    void* frameBytes;
    if (videoFrame->GetBytes(&frameBytes) == S_OK) {
        long frameSize = videoFrame->GetRowBytes() * videoFrame->GetHeight();
        m_lastFrame.data.resize(frameSize);
        std::memcpy(m_lastFrame.data.data(), frameBytes, frameSize);
        m_lastFrame.valid = true;
    } else {
        m_lastFrame.valid = false;
    }

    m_frameReceived = true;
    m_frameCondition.notify_one();
}

void DeckLinkInput::onFormatChanged(IDeckLinkDisplayMode* newDisplayMode, BMDDetectedVideoInputFormatFlags detectedSignalFlags)
{
    BMDPixelFormat pixelFormat;

    if (detectedSignalFlags & bmdDetectedVideoInputRGB444) {
        if (detectedSignalFlags & bmdDetectedVideoInput12BitDepth) {
            pixelFormat = bmdFormat12BitRGBLE;
            m_detectedSettings.format = PixelFormat::Format12BitRGB;
        } else {
            pixelFormat = bmdFormat10BitRGBXLE;
            m_detectedSettings.format = PixelFormat::Format10BitRGB;
        }
    } else {
        if (detectedSignalFlags & bmdDetectedVideoInput8BitDepth) {
            pixelFormat = bmdFormat8BitYUV;
            m_detectedSettings.format = PixelFormat::Format8BitYUV;
        } else {
            pixelFormat = bmdFormat10BitYUV;
            m_detectedSettings.format = PixelFormat::Format10BitYUV;
        }
    }

    {
        std::lock_guard<std::mutex> lock(m_formatMutex);

        m_detectedSettings.mode = static_cast<DisplayMode>(newDisplayMode->GetDisplayMode());
        m_detectedSettings.width = newDisplayMode->GetWidth();
        m_detectedSettings.height = newDisplayMode->GetHeight();

        BMDTimeValue frameDuration;
        BMDTimeScale timeScale;
        newDisplayMode->GetFrameRate(&frameDuration, &timeScale);
        m_detectedSettings.framerate = (double)timeScale / (double)frameDuration;

        m_formatDetected = true;

        std::cout << "Detected format: " << m_detectedSettings.width << "x" << m_detectedSettings.height
                  << " @ " << m_detectedSettings.framerate << " fps";

        if (detectedSignalFlags & bmdDetectedVideoInputRGB444) {
            std::cout << " (RGB 4:4:4";
        } else {
            std::cout << " (YCbCr 4:2:2";
        }

        if (detectedSignalFlags & bmdDetectedVideoInput12BitDepth) {
            std::cout << " 12-bit)" << std::endl;
        } else if (detectedSignalFlags & bmdDetectedVideoInput10BitDepth) {
            std::cout << " 10-bit)" << std::endl;
        } else {
            std::cout << " 8-bit)" << std::endl;
        }
    }

    m_currentSettings.format = m_detectedSettings.format;

    if (m_deckLinkInput) {
        m_deckLinkInput->PauseStreams();
        m_deckLinkInput->EnableVideoInput(
            newDisplayMode->GetDisplayMode(),
            pixelFormat,
            bmdVideoInputEnableFormatDetection);
        m_deckLinkInput->FlushStreams();
        m_deckLinkInput->StartStreams();
    }
}

DeckLinkInput::VideoSettings DeckLinkInput::getDetectedFormat()
{
    std::lock_guard<std::mutex> lock(m_formatMutex);
    return m_detectedSettings;
}

DeckLinkInput::PixelFormat DeckLinkInput::getDetectedPixelFormat()
{
    std::lock_guard<std::mutex> lock(m_formatMutex);
    return m_detectedSettings.format;
}

bool DeckLinkInput::stopCapture()
{
    if (m_inputEnabled && m_deckLinkInput) {
        m_deckLinkInput->StopStreams();
        m_deckLinkInput->DisableVideoInput();
        m_inputEnabled = false;
    }
    return true;
}

void DeckLinkInput::cleanup()
{
    stopCapture();

    if (m_callback) {
        m_callback->Release();
        m_callback = nullptr;
    }

    if (m_deckLinkInput) {
        m_deckLinkInput->Release();
        m_deckLinkInput = nullptr;
    }

    if (m_deckLink) {
        m_deckLink->Release();
        m_deckLink = nullptr;
    }
}

std::vector<std::string> DeckLinkInput::getDeviceList()
{
    return DeckLink::getDeviceList();
}

DeckLinkInput::VideoSettings DeckLinkInput::getVideoSettings(DisplayMode mode)
{
    VideoSettings settings;
    settings.mode = mode;
    settings.format = PixelFormat::Format8BitBGRA;

    if (m_deckLinkInput) {
        IDeckLinkDisplayMode* displayMode = nullptr;
        if (m_deckLinkInput->GetDisplayMode(static_cast<BMDDisplayMode>(mode), &displayMode) == S_OK) {
            settings.width = displayMode->GetWidth();
            settings.height = displayMode->GetHeight();

            BMDTimeValue frameDuration;
            BMDTimeScale timeScale;
            displayMode->GetFrameRate(&frameDuration, &timeScale);
            settings.framerate = (double)timeScale / (double)frameDuration;

            displayMode->Release();
        } else {
            std::cerr << "Warning: Could not get display mode information, using defaults" << std::endl;
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 25.0;
        }
    } else {
        std::cerr << "Warning: DeckLink input not initialized, using defaults" << std::endl;
        settings.width = 1920;
        settings.height = 1080;
        settings.framerate = 25.0;
    }

    return settings;
}

std::vector<DeckLinkInput::DisplayModeInfo> DeckLinkInput::getSupportedDisplayModes()
{
    std::vector<DisplayModeInfo> modes;

    if (!m_deckLinkInput) {
        std::cerr << "DeckLink input not initialized" << std::endl;
        return modes;
    }

    IDeckLinkDisplayModeIterator* displayModeIterator = nullptr;
    if (m_deckLinkInput->GetDisplayModeIterator(&displayModeIterator) != S_OK) {
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

#ifdef __APPLE__
        CFStringRef nameString;
        if (displayMode->GetName(&nameString) == S_OK) {
            CFIndex nameLen = CFStringGetLength(nameString);
            CFIndex maxSize = CFStringGetMaximumSizeForEncoding(nameLen, kCFStringEncodingUTF8) + 1;
            std::vector<char> nameBuffer(maxSize);
            if (CFStringGetCString(nameString, nameBuffer.data(), maxSize, kCFStringEncodingUTF8)) {
                modeInfo.name = std::string(nameBuffer.data());
            }
            CFRelease(nameString);
        }
#elif defined(_WIN32)
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
