#include "decklink_wrapper.hpp"
#include "decklink_hdr_frame.hpp"
#include <iostream>
#include <cstring>
#include <CoreFoundation/CoreFoundation.h>

DeckLinkOutput::DeckLinkOutput()
    : m_deckLink(nullptr)
    , m_deckLinkOutput(nullptr)
    , m_displayModeIterator(nullptr)
    , m_outputCallback(nullptr)
    , m_outputRunning(false)
    , m_outputEnabled(false)
    , m_frameDuration(0)
    , m_timeScale(0)
    , m_totalFramesScheduled(0)
    , m_useHdrMetadata(false)
    , m_hdrColorimetry(Gamut::Rec709)
    , m_hdrEotf(Eotf::SDR)
    , m_useTimecode(false)
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

    // Enable video output only if not already enabled
    if (!m_outputEnabled) {
        BMDVideoOutputFlags outputFlags = bmdVideoOutputFlagDefault;
        if (m_useTimecode) {
            outputFlags |= bmdVideoOutputRP188;
        }

        if (m_deckLinkOutput->EnableVideoOutput(static_cast<BMDDisplayMode>(settings.mode),
                                               outputFlags) != S_OK) {
            std::cerr << "Could not enable video output" << std::endl;
            return false;
        }
        m_outputEnabled = true;

        // Set callback
        if (m_deckLinkOutput->SetScheduledFrameCompletionCallback(m_outputCallback.get()) != S_OK) {
            std::cerr << "Could not set frame completion callback" << std::endl;
            return false;
        }
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

bool DeckLinkOutput::startOutput()
{
    if (!m_deckLinkOutput) {
        std::cerr << "DeckLink output not initialized" << std::endl;
        return false;
    }

    // Create initial frames
    for (int i = 0; i < 3; i++) {
        IDeckLinkMutableVideoFrame* mutableFrame = nullptr;
        if (!createFrame(&mutableFrame)) {
            std::cerr << "Could not create frame" << std::endl;
            return false;
        }

        IDeckLinkVideoFrame* frame = mutableFrame;
        if (m_useHdrMetadata) {
            frame = createHdrFrame(mutableFrame);
            mutableFrame->Release();
        }

        BMDTimeValue streamTime = (BMDTimeValue)m_totalFramesScheduled * m_frameDuration;

        if (m_useTimecode) {
            std::lock_guard<std::mutex> lock(m_timecodeMutex);

            mutableFrame->SetTimecode(bmdTimecodeVITC, nullptr);
            mutableFrame->SetTimecode(bmdTimecodeRP188VITC1, nullptr);
            mutableFrame->SetTimecode(bmdTimecodeRP188VITC2, nullptr);
            mutableFrame->SetTimecode(bmdTimecodeRP188LTC, nullptr);

            BMDTimecodeFlags flags = m_currentTimecode.dropFrame ? bmdTimecodeIsDropFrame : bmdTimecodeFlagDefault;

            HRESULT tcResult = mutableFrame->SetTimecodeFromComponents(
                bmdTimecodeRP188VITC1,
                m_currentTimecode.hours,
                m_currentTimecode.minutes,
                m_currentTimecode.seconds,
                m_currentTimecode.frames,
                flags
            );

            if (tcResult != S_OK) {
                std::cerr << "Failed to set RP188 VITC1 timecode: " << std::hex << tcResult << std::dec << std::endl;
            }

            incrementTimecode(m_currentTimecode, m_currentSettings.framerate);
        }

        HRESULT scheduleResult = m_deckLinkOutput->ScheduleVideoFrame(frame, streamTime, m_frameDuration, m_timeScale);

        if (scheduleResult != S_OK) {
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
    
    if (m_outputEnabled && m_deckLinkOutput) {
        m_deckLinkOutput->DisableVideoOutput();
        m_outputEnabled = false;
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

void DeckLinkOutput::setHdrMetadata(Gamut colorimetry, Eotf eotf)
{
    m_useHdrMetadata = true;
    m_hdrColorimetry = colorimetry;
    m_hdrEotf = eotf;

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
        // Rec.709 primaries (default)
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

    // Set luminance values based on transfer function
    if (eotf == Eotf::SDR) {
        m_hdrCustom.maxMasteringLuminance = 100.0;
        m_hdrCustom.minMasteringLuminance = 0.0001;
        m_hdrCustom.maxContentLightLevel = 100.0;
        m_hdrCustom.maxFrameAverageLightLevel = 50.0;
    } else {
        m_hdrCustom.maxMasteringLuminance = 1000.0;
        m_hdrCustom.minMasteringLuminance = 0.0001;
        m_hdrCustom.maxContentLightLevel = 1000.0;
        m_hdrCustom.maxFrameAverageLightLevel = 50.0;
    }
}

void DeckLinkOutput::setHdrMetadataCustom(Gamut colorimetry, Eotf eotf, const HdrMetadataCustom& custom)
{
    m_useHdrMetadata = true;
    m_hdrColorimetry = colorimetry;
    m_hdrEotf = eotf;
    m_hdrCustom = custom;
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
    
    switch (mode) {
        case DisplayMode::HD1080p25:
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 25.0;
            break;
        case DisplayMode::HD1080p30:
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 30.0;
            break;
        case DisplayMode::HD1080p50:
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 50.0;
            break;
        case DisplayMode::HD1080p60:
            settings.width = 1920;
            settings.height = 1080;
            settings.framerate = 60.0;
            break;
        case DisplayMode::HD720p50:
            settings.width = 1280;
            settings.height = 720;
            settings.framerate = 50.0;
            break;
        case DisplayMode::HD720p60:
            settings.width = 1280;
            settings.height = 720;
            settings.framerate = 60.0;
            break;
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

    CFUUIDBytes iunknown = CFUUIDGetUUIDBytes(IUnknownUUID);
    
    if (memcmp(&iid, &iunknown, sizeof(REFIID)) == 0) {
        *ppv = static_cast<IUnknown*>(this);
    } else if (memcmp(&iid, &IID_IDeckLinkVideoOutputCallback, sizeof(REFIID)) == 0) {
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
        IDeckLinkMutableVideoFrame* mutableFrame = nullptr;
        if (m_parent->createFrame(&mutableFrame)) {
            if (m_parent->m_useTimecode) {
                std::lock_guard<std::mutex> lock(m_parent->m_timecodeMutex);

                mutableFrame->SetTimecode(bmdTimecodeVITC, nullptr);
                mutableFrame->SetTimecode(bmdTimecodeRP188VITC1, nullptr);
                mutableFrame->SetTimecode(bmdTimecodeRP188VITC2, nullptr);
                mutableFrame->SetTimecode(bmdTimecodeRP188LTC, nullptr);

                BMDTimecodeFlags flags = m_parent->m_currentTimecode.dropFrame ? bmdTimecodeIsDropFrame : bmdTimecodeFlagDefault;

                HRESULT tcResult = mutableFrame->SetTimecodeFromComponents(
                    bmdTimecodeRP188VITC1,
                    m_parent->m_currentTimecode.hours,
                    m_parent->m_currentTimecode.minutes,
                    m_parent->m_currentTimecode.seconds,
                    m_parent->m_currentTimecode.frames,
                    flags
                );

                if (tcResult != S_OK) {
                    std::cerr << "Failed to set RP188 VITC1 timecode in callback: " << std::hex << tcResult << std::dec << std::endl;
                }

                m_parent->incrementTimecode(m_parent->m_currentTimecode, m_parent->m_currentSettings.framerate);
            }

            IDeckLinkVideoFrame* frame = mutableFrame;
            if (m_parent->m_useHdrMetadata) {
                frame = m_parent->createHdrFrame(mutableFrame);
                mutableFrame->Release();
            }

            BMDTimeValue streamTime = (BMDTimeValue)m_parent->m_totalFramesScheduled * m_parent->m_frameDuration;

            m_parent->m_deckLinkOutput->ScheduleVideoFrame(
                frame,
                streamTime,
                m_parent->m_frameDuration,
                m_parent->m_timeScale
            );

            m_parent->m_totalFramesScheduled++;
            frame->Release();
        }
    }

    return S_OK;
}

HRESULT DeckLinkOutput::OutputCallback::ScheduledPlaybackHasStopped()
{
    m_parent->m_outputRunning = false;
    return S_OK;
}

void DeckLinkOutput::setTimecode(const Timecode& tc)
{
    std::lock_guard<std::mutex> lock(m_timecodeMutex);
    m_currentTimecode = tc;
    m_useTimecode = true;
}

DeckLinkOutput::Timecode DeckLinkOutput::getTimecode()
{
    std::lock_guard<std::mutex> lock(m_timecodeMutex);
    return m_currentTimecode;
}

void DeckLinkOutput::incrementTimecode(Timecode& tc, double framerate)
{
    tc.frames++;

    int framesPerSecond = static_cast<int>(framerate + 0.5);

    if (tc.dropFrame && (framerate > 29.0 && framerate < 31.0)) {
        if (tc.frames >= 30) {
            tc.frames = 0;
            tc.seconds++;

            if (tc.seconds % 60 == 0 && tc.seconds != 0) {
                if (tc.seconds % 600 != 0) {
                    tc.frames = 2;
                }
            }
        }
    } else if (tc.dropFrame && (framerate > 59.0 && framerate < 61.0)) {
        if (tc.frames >= 60) {
            tc.frames = 0;
            tc.seconds++;

            if (tc.seconds % 60 == 0 && tc.seconds != 0) {
                if (tc.seconds % 600 != 0) {
                    tc.frames = 4;
                }
            }
        }
    } else {
        if (tc.frames >= framesPerSecond) {
            tc.frames = 0;
            tc.seconds++;
        }
    }

    if (tc.seconds >= 60) {
        tc.seconds = 0;
        tc.minutes++;
    }

    if (tc.minutes >= 60) {
        tc.minutes = 0;
        tc.hours++;
    }

    if (tc.hours >= 24) {
        tc.hours = 0;
    }
}