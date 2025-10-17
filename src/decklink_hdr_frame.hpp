#pragma once

#include <atomic>
#include "decklink_wrapper.hpp"

#ifdef _WIN32
    #include <windows.h>
    #include <combaseapi.h>
    #include "DeckLinkAPI_h.h"
#else
    #include "DeckLinkAPI.h"
#endif

struct HdrMetadata {
    struct ChromaticityCoordinates {
        double RedX;
        double RedY;
        double GreenX;
        double GreenY;
        double BlueX;
        double BlueY;
        double WhiteX;
        double WhiteY;
    };

    ChromaticityCoordinates referencePrimaries;
    double maxMasteringLuminance;
    double minMasteringLuminance;
    double maxContentLightLevel;
    double maxFrameAverageLightLevel;
    DeckLinkOutput::Eotf eotf;
    DeckLinkOutput::Gamut colorimetry;

    static ChromaticityCoordinates rec709() {
        return {0.64, 0.33, 0.30, 0.60, 0.15, 0.06, 0.3127, 0.3290};
    }

    static ChromaticityCoordinates rec2020() {
        return {0.708, 0.292, 0.170, 0.797, 0.131, 0.046, 0.3127, 0.3290};
    }

    static HdrMetadata defaultSdr() {
        return {rec709(), 100, 0.0001, 100, 50, DeckLinkOutput::Eotf::SDR, DeckLinkOutput::Gamut::Rec709};
    }

    static HdrMetadata defaultHlg() {
        return {rec2020(), 1000, 0.0001, 1000, 50, DeckLinkOutput::Eotf::HLG, DeckLinkOutput::Gamut::Rec2020};
    }

    static HdrMetadata defaultPq() {
        return {rec2020(), 1000, 0.0001, 1000, 50, DeckLinkOutput::Eotf::PQ, DeckLinkOutput::Gamut::Rec2020};
    }

    static HdrMetadata custom(DeckLinkOutput::Gamut colorimetry, DeckLinkOutput::Eotf eotf,
                             const ChromaticityCoordinates& primaries,
                             double maxMasteringLuminance, double minMasteringLuminance,
                             double maxContentLightLevel, double maxFrameAverageLightLevel) {
        return {primaries, maxMasteringLuminance, minMasteringLuminance,
                maxContentLightLevel, maxFrameAverageLightLevel, eotf, colorimetry};
    }
};

class DeckLinkHdrVideoFrame : public IDeckLinkVideoFrame, public IDeckLinkVideoFrameMetadataExtensions {
public:
    DeckLinkHdrVideoFrame(IDeckLinkMutableVideoFrame* frame, const HdrMetadata& metadata);
    virtual ~DeckLinkHdrVideoFrame();

    virtual HRESULT STDMETHODCALLTYPE QueryInterface(REFIID iid, LPVOID* ppv) override;
    virtual ULONG STDMETHODCALLTYPE AddRef() override;
    virtual ULONG STDMETHODCALLTYPE Release() override;

    virtual long GetWidth() override { return m_frame->GetWidth(); }
    virtual long GetHeight() override { return m_frame->GetHeight(); }
    virtual long GetRowBytes() override { return m_frame->GetRowBytes(); }
    virtual BMDPixelFormat GetPixelFormat() override { return m_frame->GetPixelFormat(); }
    virtual BMDFrameFlags GetFlags() override { return m_frame->GetFlags() | bmdFrameContainsHDRMetadata; }
    virtual HRESULT GetBytes(void** buffer) override { return m_frame->GetBytes(buffer); }
    virtual HRESULT GetTimecode(BMDTimecodeFormat format, IDeckLinkTimecode** timecode) override {
        return m_frame->GetTimecode(format, timecode);
    }
    virtual HRESULT GetAncillaryData(IDeckLinkVideoFrameAncillary** ancillary) override {
        return m_frame->GetAncillaryData(ancillary);
    }

    virtual HRESULT GetInt(BMDDeckLinkFrameMetadataID metadataID, int64_t* value) override;
    virtual HRESULT GetFloat(BMDDeckLinkFrameMetadataID metadataID, double* value) override;
#ifdef _WIN32
    // Windows uses BOOL and BSTR types
    virtual HRESULT GetFlag(BMDDeckLinkFrameMetadataID metadataID, BOOL* value) override {
        return E_INVALIDARG;
    }
    virtual HRESULT GetString(BMDDeckLinkFrameMetadataID metadataID, BSTR* value) override {
        return E_INVALIDARG;
    }
#elif defined(__APPLE__)
    virtual HRESULT GetFlag(BMDDeckLinkFrameMetadataID metadataID, bool* value) override {
        return E_INVALIDARG;
    }
    virtual HRESULT GetString(BMDDeckLinkFrameMetadataID metadataID, CFStringRef* value) override {
        return E_INVALIDARG;
    }
#else
    // Linux
    virtual HRESULT GetFlag(BMDDeckLinkFrameMetadataID metadataID, bool* value) override {
        return E_INVALIDARG;
    }
    virtual HRESULT GetString(BMDDeckLinkFrameMetadataID metadataID, const char** value) override {
        return E_INVALIDARG;
    }
#endif
    virtual HRESULT GetBytes(BMDDeckLinkFrameMetadataID metadataID, void* buffer, uint32_t* bufferSize) override {
        *bufferSize = 0;
        return E_INVALIDARG;
    }

private:
    IDeckLinkMutableVideoFrame* m_frame;
    HdrMetadata m_metadata;
    std::atomic<ULONG> m_refCount;
};
