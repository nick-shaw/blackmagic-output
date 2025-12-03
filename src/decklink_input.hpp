#pragma once

#include "decklink_common.hpp"
#include <memory>
#include <vector>
#include <atomic>
#include <mutex>
#include <condition_variable>
#include <string>

class DeckLinkInputCallback;

class DeckLinkInput {
public:
    using PixelFormat = DeckLink::PixelFormat;
    using DisplayMode = DeckLink::DisplayMode;
    using Gamut = DeckLink::Gamut;
    using Eotf = DeckLink::Eotf;
    using VideoSettings = DeckLink::VideoSettings;
    using DisplayModeInfo = DeckLink::DisplayModeInfo;

    struct CapturedFrame {
        std::vector<uint8_t> data;
        int width;
        int height;
        PixelFormat format;
        DisplayMode mode;
        bool valid;
    };

    DeckLinkInput();
    ~DeckLinkInput();

    bool initialize(int deviceIndex = 0);
    bool startCapture();
    bool captureFrame(CapturedFrame& frame, int timeoutMs = 5000);
    bool stopCapture();
    void cleanup();

    VideoSettings getDetectedFormat();
    PixelFormat getDetectedPixelFormat();

    std::vector<std::string> getDeviceList();
    VideoSettings getVideoSettings(DisplayMode mode);
    std::vector<DisplayModeInfo> getSupportedDisplayModes();

private:
    friend class DeckLinkInputCallback;

    IDeckLink* m_deckLink;
    IDeckLinkInput* m_deckLinkInput;
    DeckLinkInputCallback* m_callback;

    VideoSettings m_currentSettings;
    std::atomic<bool> m_inputEnabled;

    std::mutex m_frameMutex;
    std::condition_variable m_frameCondition;
    CapturedFrame m_lastFrame;
    std::atomic<bool> m_frameReceived;

    std::mutex m_formatMutex;
    std::atomic<bool> m_formatDetected;
    VideoSettings m_detectedSettings;

    void onFrameArrived(IDeckLinkVideoInputFrame* videoFrame);
    void onFormatChanged(IDeckLinkDisplayMode* newDisplayMode, BMDDetectedVideoInputFormatFlags detectedSignalFlags);
};
