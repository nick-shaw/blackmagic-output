#include "decklink_wrapper.hpp"
#include <iostream>
#include <cstring>

#ifdef _WIN32
    #include <comutil.h>
#endif

DeckLinkOutput::DeckLinkOutput()
    : m_deckLink(nullptr)
    , m_deckLinkOutput(nullptr)
    , m_displayModeIterator(nullptr)
    , m_outputCallback(nullptr)
    , m_outputRunning(false)
    , m_frameDuration(0)
    , m_timeScale(0)
    , m_totalFramesScheduled(0)
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

    m_outputCallback = std::make_unique<OutputCallback>(this);
    
    return true;
}

bool DeckLinkOutput::setupOutput(const VideoSettings& settings)
{
    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return false;
    }

    m_currentSettings = settings;

    // Get display mode
    IDeckLinkDisplayMode* displayMode = nullptr;
    if (m_deckLinkOutput->GetDisplayMode(static_cast<BMDDisplayMode>(settings.mode), &displayMode) != S_OK) {
        std::cerr << "Could not get display mode" << std::endl;
        return false;
    }

    m_frameDuration = displayMode->GetFrameRate(&m_timeScale);
    displayMode->Release();

    // Set video output format
    if (m_deckLinkOutput->SetVideoOutputFormat(
            static_cast<BMDDisplayMode>(settings.mode),
            static_cast<BMDPixelFormat>(settings.format),
            bmdVideoOutputFlagDefault) != S_OK) {
        std::cerr << "Could not set video output format" << std::endl;
        return false;
    }

    // Set callback
    if (m_deckLinkOutput->SetScheduledFrameCompletionCallback(m_outputCallback.get()) != S_OK) {
        std::cerr << "Could not set frame completion callback" << std::endl;
        return false;
    }

    // Calculate frame buffer size
    size_t frameSize;
    switch (settings.format) {
        case PixelFormat::Format8BitBGRA:
            frameSize = settings.width * settings.height * 4;
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
    
    if (m_deckLinkOutput->CreateVideoFrame(
            m_currentSettings.width,
            m_currentSettings.height,
            m_currentSettings.width * (m_currentSettings.format == PixelFormat::Format8BitBGRA ? 4 : 2),
            static_cast<BMDPixelFormat>(m_currentSettings.format),
            bmdFrameFlagDefault,
            frame) != S_OK) {
        return false;
    }

    void* frameBuffer;
    IDeckLinkVideoBuffer* videoBuffer = nullptr;
    if ((*frame)->QueryInterface(IID_IDeckLinkVideoBuffer, (void**)&videoBuffer) == S_OK) {
        if (videoBuffer->GetBytes(&frameBuffer) == S_OK) {
            std::memcpy(frameBuffer, m_frameBuffer.data(), m_frameBuffer.size());
        }
        videoBuffer->Release();
    }
    
    return true;
}

bool DeckLinkOutput::startOutput()
{
    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return false;
    }

    // Create initial frames
    for (int i = 0; i < 3; i++) {
        IDeckLinkMutableVideoFrame* frame = nullptr;
        if (!createFrame(&frame)) {
            std::cerr << "Could not create frame" << std::endl;
            return false;
        }

        BMDTimeValue streamTime = (BMDTimeValue)m_totalFramesScheduled * m_frameDuration;
        
        if (m_deckLinkOutput->ScheduleVideoFrame(frame, streamTime, m_frameDuration, m_timeScale) != S_OK) {
            std::cerr << "Could not schedule video frame" << std::endl;
            frame->Release();
            return false;
        }

        m_totalFramesScheduled++;
        frame->Release();
    }

    if (m_deckLinkOutput->StartScheduledPlayback(0, m_timeScale, 1.0) != S_OK) {
        std::cerr << "Could not start scheduled playback" << std::endl;
        return false;
    }

    m_outputRunning = true;
    return true;
}

bool DeckLinkOutput::stopOutput()
{
    if (m_outputRunning && m_deckLinkOutput) {
        m_deckLinkOutput->StopScheduledPlayback(0, nullptr, m_timeScale);
        m_outputRunning = false;
    }
    return true;
}

void DeckLinkOutput::cleanup()
{
    stopOutput();
    
    if (m_deckLinkOutput) {
        m_deckLinkOutput->Release();
        m_deckLinkOutput = nullptr;
    }
    
    if (m_deckLink) {
        m_deckLink->Release();
        m_deckLink = nullptr;
    }
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
        const char* deviceName = nullptr;
        if (deckLink->GetDisplayName(&deviceName) == S_OK) {
            devices.push_back(std::string(deviceName));
#ifdef _WIN32
            SysFreeString((BSTR)deviceName);
#else
            free((void*)deviceName);
#endif
        }
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

// OutputCallback implementation
DeckLinkOutput::OutputCallback::OutputCallback(DeckLinkOutput* parent)
    : m_refCount(1)
    , m_parent(parent)
{
}

DeckLinkOutput::OutputCallback::~OutputCallback()
{
}

HRESULT DeckLinkOutput::OutputCallback::QueryInterface(REFIID iid, LPVOID* ppv)
{
    if (ppv == nullptr)
        return E_INVALIDARG;

    *ppv = nullptr;

    if (iid == IID_IUnknown) {
        *ppv = static_cast<IUnknown*>(this);
    } else if (iid == IID_IDeckLinkVideoOutputCallback) {
        *ppv = static_cast<IDeckLinkVideoOutputCallback*>(this);
    } else {
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}

ULONG DeckLinkOutput::OutputCallback::AddRef()
{
    return ++m_refCount;
}

ULONG DeckLinkOutput::OutputCallback::Release()
{
    ULONG refCount = --m_refCount;
    if (refCount == 0) {
        delete this;
    }
    return refCount;
}

HRESULT DeckLinkOutput::OutputCallback::ScheduledFrameCompleted(
    IDeckLinkVideoFrame* completedFrame,
    BMDOutputFrameCompletionResult result)
{
    if (m_parent->m_outputRunning) {
        // Schedule next frame
        IDeckLinkMutableVideoFrame* nextFrame = nullptr;
        if (m_parent->createFrame(&nextFrame)) {
            BMDTimeValue streamTime = (BMDTimeValue)m_parent->m_totalFramesScheduled * m_parent->m_frameDuration;
            
            m_parent->m_deckLinkOutput->ScheduleVideoFrame(
                nextFrame, 
                streamTime, 
                m_parent->m_frameDuration, 
                m_parent->m_timeScale
            );
            
            m_parent->m_totalFramesScheduled++;
            nextFrame->Release();
        }
    }
    
    return S_OK;
}

HRESULT DeckLinkOutput::OutputCallback::ScheduledPlaybackHasStopped()
{
    m_parent->m_outputRunning = false;
    return S_OK;
}