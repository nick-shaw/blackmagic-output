#include "decklink_hdr_frame.hpp"
#include <cstring>
#include <iostream>

#ifdef __APPLE__
#include <CoreFoundation/CoreFoundation.h>
#endif

DeckLinkHdrVideoFrame::DeckLinkHdrVideoFrame(IDeckLinkMutableVideoFrame* frame, const HdrMetadata& metadata)
    : m_frame(frame), m_metadata(metadata), m_refCount(1)
{
    m_frame->AddRef();
}

DeckLinkHdrVideoFrame::~DeckLinkHdrVideoFrame()
{
    m_frame->Release();
}

ULONG DeckLinkHdrVideoFrame::AddRef()
{
    return ++m_refCount;
}

ULONG DeckLinkHdrVideoFrame::Release()
{
    ULONG newRefValue = --m_refCount;
    if (newRefValue == 0) {
        delete this;
    }
    return newRefValue;
}

#ifdef __APPLE__
#define CompareREFIID(iid1, iid2) (memcmp(&iid1, &iid2, sizeof(REFIID)) == 0)

HRESULT DeckLinkHdrVideoFrame::QueryInterface(REFIID iid, LPVOID* ppv)
{
    CFUUIDBytes iunknown = CFUUIDGetUUIDBytes(IUnknownUUID);

    if (CompareREFIID(iid, iunknown)) {
        *ppv = static_cast<IDeckLinkVideoFrame*>(this);
    } else if (CompareREFIID(iid, IID_IDeckLinkVideoFrame)) {
        *ppv = static_cast<IDeckLinkVideoFrame*>(this);
    } else if (CompareREFIID(iid, IID_IDeckLinkVideoFrameMetadataExtensions)) {
        *ppv = static_cast<IDeckLinkVideoFrameMetadataExtensions*>(this);
    } else {
        *ppv = nullptr;
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}
#else
HRESULT DeckLinkHdrVideoFrame::QueryInterface(REFIID iid, LPVOID* ppv)
{
    if (iid == IID_IUnknown) {
        *ppv = static_cast<IDeckLinkVideoFrame*>(this);
    } else if (iid == IID_IDeckLinkVideoFrame) {
        *ppv = static_cast<IDeckLinkVideoFrame*>(this);
    } else if (iid == IID_IDeckLinkVideoFrameMetadataExtensions) {
        *ppv = static_cast<IDeckLinkVideoFrameMetadataExtensions*>(this);
    } else {
        *ppv = nullptr;
        return E_NOINTERFACE;
    }

    AddRef();
    return S_OK;
}
#endif

HRESULT DeckLinkHdrVideoFrame::GetInt(BMDDeckLinkFrameMetadataID metadataID, int64_t* value)
{
    switch (metadataID) {
        case bmdDeckLinkFrameMetadataHDRElectroOpticalTransferFunc:
            *value = static_cast<int64_t>(m_metadata.eotf);
            break;

        case bmdDeckLinkFrameMetadataColorspace:
            *value = m_metadata.colorimetry == DeckLinkOutput::Gamut::Rec709 ? bmdColorspaceRec709 : bmdColorspaceRec2020;
            break;

        default:
            return E_INVALIDARG;
    }
    return S_OK;
}

HRESULT DeckLinkHdrVideoFrame::GetFloat(BMDDeckLinkFrameMetadataID metadataID, double* value)
{
    switch (metadataID) {
        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesRedX:
            *value = m_metadata.referencePrimaries.RedX;
            break;

        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesRedY:
            *value = m_metadata.referencePrimaries.RedY;
            break;

        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesGreenX:
            *value = m_metadata.referencePrimaries.GreenX;
            break;

        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesGreenY:
            *value = m_metadata.referencePrimaries.GreenY;
            break;

        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesBlueX:
            *value = m_metadata.referencePrimaries.BlueX;
            break;

        case bmdDeckLinkFrameMetadataHDRDisplayPrimariesBlueY:
            *value = m_metadata.referencePrimaries.BlueY;
            break;

        case bmdDeckLinkFrameMetadataHDRWhitePointX:
            *value = m_metadata.referencePrimaries.WhiteX;
            break;

        case bmdDeckLinkFrameMetadataHDRWhitePointY:
            *value = m_metadata.referencePrimaries.WhiteY;
            break;

        case bmdDeckLinkFrameMetadataHDRMaxDisplayMasteringLuminance:
            *value = m_metadata.maxMasteringLuminance;
            break;

        case bmdDeckLinkFrameMetadataHDRMinDisplayMasteringLuminance:
            *value = m_metadata.minMasteringLuminance;
            break;

        case bmdDeckLinkFrameMetadataHDRMaximumContentLightLevel:
            *value = m_metadata.maxContentLightLevel;
            break;

        case bmdDeckLinkFrameMetadataHDRMaximumFrameAverageLightLevel:
            *value = m_metadata.maxFrameAverageLightLevel;
            break;

        default:
            return E_INVALIDARG;
    }
    return S_OK;
}
