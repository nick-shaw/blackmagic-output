#pragma once

#include <memory>
#include <functional>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>

#ifdef _WIN32
    #include "DeckLinkAPI_h.h"
#else
    #include "DeckLinkAPI.h"
#endif

class DeckLinkOutput {
public:
    enum class PixelFormat {
        Format8BitYUV = bmdFormat8BitYUV,
        Format8BitBGRA = bmdFormat8BitBGRA,
        Format10BitYUV = bmdFormat10BitYUV
    };

    enum class DisplayMode {
        HD1080p25 = bmdModeHD1080p25,
        HD1080p30 = bmdModeHD1080p30,
        HD1080p50 = bmdModeHD1080p50,
        HD1080p60 = bmdModeHD1080p6000,
        HD720p50 = bmdModeHD720p50,
        HD720p60 = bmdModeHD720p60
    };

    enum class Gamut {
        Rec709,
        Rec2020
    };

    enum class Eotf {
        SDR = 0,
        PQ = 2,
        HLG = 3
    };

    struct VideoSettings {
        DisplayMode mode;
        PixelFormat format;
        int width;
        int height;
        double framerate;
        Gamut colorimetry = Gamut::Rec709;
        Eotf eotf = Eotf::SDR;
    };

    DeckLinkOutput();
    ~DeckLinkOutput();

    bool initialize(int deviceIndex = 0);
    bool setupOutput(const VideoSettings& settings);
    bool setFrameData(const uint8_t* data, size_t dataSize);
    bool startOutput();
    bool stopOutput(bool sendBlackFrame = false);
    void cleanup();

    struct HdrMetadataCustom {
        double displayPrimariesRedX = 0.64;
        double displayPrimariesRedY = 0.33;
        double displayPrimariesGreenX = 0.30;
        double displayPrimariesGreenY = 0.60;
        double displayPrimariesBlueX = 0.15;
        double displayPrimariesBlueY = 0.06;
        double whitePointX = 0.3127;
        double whitePointY = 0.3290;
        double maxMasteringLuminance = 1000.0;
        double minMasteringLuminance = 0.0001;
        double maxContentLightLevel = 1000.0;
        double maxFrameAverageLightLevel = 50.0;
    };

    struct Timecode {
        uint8_t hours = 0;
        uint8_t minutes = 0;
        uint8_t seconds = 0;
        uint8_t frames = 0;
        bool dropFrame = false;
    };

    std::vector<std::string> getDeviceList();
    VideoSettings getVideoSettings(DisplayMode mode);
    void setHdrMetadata(Gamut colorimetry, Eotf eotf);
    void setHdrMetadataCustom(Gamut colorimetry, Eotf eotf, const HdrMetadataCustom& custom);

    void setTimecode(const Timecode& tc);
    Timecode getTimecode();

private:
    class OutputCallback;

    IDeckLink* m_deckLink;
    IDeckLinkOutput* m_deckLinkOutput;
    IDeckLinkDisplayModeIterator* m_displayModeIterator;
    std::unique_ptr<OutputCallback> m_outputCallback;

    VideoSettings m_currentSettings;
    std::vector<uint8_t> m_frameBuffer;
    std::mutex m_frameBufferMutex;
    std::atomic<bool> m_outputRunning;
    std::atomic<bool> m_outputEnabled;

    BMDTimeValue m_frameDuration;
    BMDTimeScale m_timeScale;
    unsigned long m_totalFramesScheduled;

    bool m_useHdrMetadata;
    Gamut m_hdrColorimetry;
    Eotf m_hdrEotf;
    HdrMetadataCustom m_hdrCustom;

    bool m_useTimecode;
    Timecode m_currentTimecode;
    std::mutex m_timecodeMutex;

    bool createFrame(IDeckLinkMutableVideoFrame** frame);
    IDeckLinkVideoFrame* createHdrFrame(IDeckLinkMutableVideoFrame* frame);
    void incrementTimecode(Timecode& tc, double framerate);
};

class DeckLinkOutput::OutputCallback : public IDeckLinkVideoOutputCallback {
public:
    OutputCallback(DeckLinkOutput* parent);
    virtual ~OutputCallback();

    virtual HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, LPVOID* ppv);
    virtual ULONG STDMETHODCALLTYPE AddRef();
    virtual ULONG STDMETHODCALLTYPE Release();
    
    virtual HRESULT STDMETHODCALLTYPE ScheduledFrameCompleted(
        IDeckLinkVideoFrame* completedFrame,
        BMDOutputFrameCompletionResult result);
    
    virtual HRESULT STDMETHODCALLTYPE ScheduledPlaybackHasStopped();

private:
    std::atomic<ULONG> m_refCount;
    DeckLinkOutput* m_parent;
};