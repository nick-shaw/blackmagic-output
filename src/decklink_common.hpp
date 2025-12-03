#pragma once

#include <memory>
#include <vector>
#include <string>

#ifdef _WIN32
    #include <windows.h>
    #include <combaseapi.h>
    #include "DeckLinkAPI_h.h"
#else
    #include "DeckLinkAPI.h"
#endif

namespace DeckLink {

enum class PixelFormat {
    Format8BitYUV = bmdFormat8BitYUV,
    Format8BitBGRA = bmdFormat8BitBGRA,
    Format10BitYUV = bmdFormat10BitYUV,
    Format10BitRGB = bmdFormat10BitRGBXLE,
    Format12BitRGB = bmdFormat12BitRGBLE
};

enum class DisplayMode {
    NTSC = bmdModeNTSC,
    NTSC2398 = bmdModeNTSC2398,
    PAL = bmdModePAL,
    NTSCp = bmdModeNTSCp,
    PALp = bmdModePALp,

    HD1080p2398 = bmdModeHD1080p2398,
    HD1080p24 = bmdModeHD1080p24,
    HD1080p25 = bmdModeHD1080p25,
    HD1080p2997 = bmdModeHD1080p2997,
    HD1080p30 = bmdModeHD1080p30,
    HD1080p4795 = bmdModeHD1080p4795,
    HD1080p48 = bmdModeHD1080p48,
    HD1080p50 = bmdModeHD1080p50,
    HD1080p5994 = bmdModeHD1080p5994,
    HD1080p60 = bmdModeHD1080p6000,
    HD1080p9590 = bmdModeHD1080p9590,
    HD1080p96 = bmdModeHD1080p96,
    HD1080p100 = bmdModeHD1080p100,
    HD1080p11988 = bmdModeHD1080p11988,
    HD1080p120 = bmdModeHD1080p120,

    HD1080i50 = bmdModeHD1080i50,
    HD1080i5994 = bmdModeHD1080i5994,
    HD1080i60 = bmdModeHD1080i6000,

    HD720p50 = bmdModeHD720p50,
    HD720p5994 = bmdModeHD720p5994,
    HD720p60 = bmdModeHD720p60,

    Mode2k2398 = bmdMode2k2398,
    Mode2k24 = bmdMode2k24,
    Mode2k25 = bmdMode2k25,

    Mode2kDCI2398 = bmdMode2kDCI2398,
    Mode2kDCI24 = bmdMode2kDCI24,
    Mode2kDCI25 = bmdMode2kDCI25,
    Mode2kDCI2997 = bmdMode2kDCI2997,
    Mode2kDCI30 = bmdMode2kDCI30,
    Mode2kDCI4795 = bmdMode2kDCI4795,
    Mode2kDCI48 = bmdMode2kDCI48,
    Mode2kDCI50 = bmdMode2kDCI50,
    Mode2kDCI5994 = bmdMode2kDCI5994,
    Mode2kDCI60 = bmdMode2kDCI60,
    Mode2kDCI9590 = bmdMode2kDCI9590,
    Mode2kDCI96 = bmdMode2kDCI96,
    Mode2kDCI100 = bmdMode2kDCI100,
    Mode2kDCI11988 = bmdMode2kDCI11988,
    Mode2kDCI120 = bmdMode2kDCI120,

    Mode4K2160p2398 = bmdMode4K2160p2398,
    Mode4K2160p24 = bmdMode4K2160p24,
    Mode4K2160p25 = bmdMode4K2160p25,
    Mode4K2160p2997 = bmdMode4K2160p2997,
    Mode4K2160p30 = bmdMode4K2160p30,
    Mode4K2160p4795 = bmdMode4K2160p4795,
    Mode4K2160p48 = bmdMode4K2160p48,
    Mode4K2160p50 = bmdMode4K2160p50,
    Mode4K2160p5994 = bmdMode4K2160p5994,
    Mode4K2160p60 = bmdMode4K2160p60,
    Mode4K2160p9590 = bmdMode4K2160p9590,
    Mode4K2160p96 = bmdMode4K2160p96,
    Mode4K2160p100 = bmdMode4K2160p100,
    Mode4K2160p11988 = bmdMode4K2160p11988,
    Mode4K2160p120 = bmdMode4K2160p120,

    Mode4kDCI2398 = bmdMode4kDCI2398,
    Mode4kDCI24 = bmdMode4kDCI24,
    Mode4kDCI25 = bmdMode4kDCI25,
    Mode4kDCI2997 = bmdMode4kDCI2997,
    Mode4kDCI30 = bmdMode4kDCI30,
    Mode4kDCI4795 = bmdMode4kDCI4795,
    Mode4kDCI48 = bmdMode4kDCI48,
    Mode4kDCI50 = bmdMode4kDCI50,
    Mode4kDCI5994 = bmdMode4kDCI5994,
    Mode4kDCI60 = bmdMode4kDCI60,
    Mode4kDCI9590 = bmdMode4kDCI9590,
    Mode4kDCI96 = bmdMode4kDCI96,
    Mode4kDCI100 = bmdMode4kDCI100,
    Mode4kDCI11988 = bmdMode4kDCI11988,
    Mode4kDCI120 = bmdMode4kDCI120,

    Mode8K4320p2398 = bmdMode8K4320p2398,
    Mode8K4320p24 = bmdMode8K4320p24,
    Mode8K4320p25 = bmdMode8K4320p25,
    Mode8K4320p2997 = bmdMode8K4320p2997,
    Mode8K4320p30 = bmdMode8K4320p30,
    Mode8K4320p4795 = bmdMode8K4320p4795,
    Mode8K4320p48 = bmdMode8K4320p48,
    Mode8K4320p50 = bmdMode8K4320p50,
    Mode8K4320p5994 = bmdMode8K4320p5994,
    Mode8K4320p60 = bmdMode8K4320p60,

    Mode8kDCI2398 = bmdMode8kDCI2398,
    Mode8kDCI24 = bmdMode8kDCI24,
    Mode8kDCI25 = bmdMode8kDCI25,
    Mode8kDCI2997 = bmdMode8kDCI2997,
    Mode8kDCI30 = bmdMode8kDCI30,
    Mode8kDCI4795 = bmdMode8kDCI4795,
    Mode8kDCI48 = bmdMode8kDCI48,
    Mode8kDCI50 = bmdMode8kDCI50,
    Mode8kDCI5994 = bmdMode8kDCI5994,
    Mode8kDCI60 = bmdMode8kDCI60,

    Mode640x480p60 = bmdMode640x480p60,
    Mode800x600p60 = bmdMode800x600p60,
    Mode1440x900p50 = bmdMode1440x900p50,
    Mode1440x900p60 = bmdMode1440x900p60,
    Mode1440x1080p50 = bmdMode1440x1080p50,
    Mode1440x1080p60 = bmdMode1440x1080p60,
    Mode1600x1200p50 = bmdMode1600x1200p50,
    Mode1600x1200p60 = bmdMode1600x1200p60,
    Mode1920x1200p50 = bmdMode1920x1200p50,
    Mode1920x1200p60 = bmdMode1920x1200p60,
    Mode1920x1440p50 = bmdMode1920x1440p50,
    Mode1920x1440p60 = bmdMode1920x1440p60,
    Mode2560x1440p50 = bmdMode2560x1440p50,
    Mode2560x1440p60 = bmdMode2560x1440p60,
    Mode2560x1600p50 = bmdMode2560x1600p50,
    Mode2560x1600p60 = bmdMode2560x1600p60
};

enum class Gamut {
    Rec601,
    Rec709,
    Rec2020
};

enum class Eotf {
    SDR = 0,
    HDR_Traditional = 1,
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

struct DisplayModeInfo {
    DisplayMode displayMode;
    std::string name;
    int width;
    int height;
    double framerate;
};

struct DeviceCapabilities {
    std::string name;
    bool supports_input;
    bool supports_output;
};

std::vector<std::string> getDeviceList();

DeviceCapabilities getDeviceCapabilities(int deviceIndex);

size_t calculateFrameBufferSize(const VideoSettings& settings);

IDeckLinkIterator* CreateDeckLinkIteratorInstance();

}
