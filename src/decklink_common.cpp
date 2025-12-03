#include "decklink_common.hpp"
#include <iostream>

#ifdef __APPLE__
    #include <CoreFoundation/CoreFoundation.h>
#endif

#ifdef _WIN32
    #include <comutil.h>
#endif

namespace DeckLink {

IDeckLinkIterator* CreateDeckLinkIteratorInstance() {
#ifdef _WIN32
    IDeckLinkIterator* iterator = nullptr;
    HRESULT result = CoCreateInstance(CLSID_CDeckLinkIterator, nullptr, CLSCTX_ALL,
                                     IID_IDeckLinkIterator, (void**)&iterator);
    if (FAILED(result)) {
        return nullptr;
    }
    return iterator;
#else
    return ::CreateDeckLinkIteratorInstance();
#endif
}

std::vector<std::string> getDeviceList()
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
            _bstr_t bstr(deviceNameBSTR, false);
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

DeviceCapabilities getDeviceCapabilities(int deviceIndex)
{
    DeviceCapabilities caps;
    caps.name = "";
    caps.supports_input = false;
    caps.supports_output = false;

    IDeckLinkIterator* deckLinkIterator = CreateDeckLinkIteratorInstance();
    if (!deckLinkIterator) {
        return caps;
    }

    IDeckLink* deckLink = nullptr;
    int currentIndex = 0;

    // Iterate to the requested device
    while (deckLinkIterator->Next(&deckLink) == S_OK) {
        if (currentIndex == deviceIndex) {
            // Get device name
#ifdef __APPLE__
            CFStringRef deviceNameRef = nullptr;
            if (deckLink->GetDisplayName(&deviceNameRef) == S_OK) {
                CFIndex length = CFStringGetLength(deviceNameRef);
                CFIndex maxSize = CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8) + 1;
                char* buffer = new char[maxSize];

                if (CFStringGetCString(deviceNameRef, buffer, maxSize, kCFStringEncodingUTF8)) {
                    caps.name = std::string(buffer);
                }

                delete[] buffer;
                CFRelease(deviceNameRef);
            }
#elif defined(_WIN32)
            BSTR deviceNameBSTR = nullptr;
            if (deckLink->GetDisplayName(&deviceNameBSTR) == S_OK) {
                _bstr_t bstr(deviceNameBSTR, false);
                caps.name = std::string((const char*)bstr);
                SysFreeString(deviceNameBSTR);
            }
#else
            const char* deviceName = nullptr;
            if (deckLink->GetDisplayName(&deviceName) == S_OK) {
                caps.name = std::string(deviceName);
                free((void*)deviceName);
            }
#endif

            // Query device attributes
            IDeckLinkProfileAttributes* attributes = nullptr;
            if (deckLink->QueryInterface(IID_IDeckLinkProfileAttributes, (void**)&attributes) == S_OK) {
                int64_t hasInput = 0;
                int64_t hasOutput = 0;

                if (attributes->GetInt(BMDDeckLinkVideoInputConnections, &hasInput) == S_OK) {
                    caps.supports_input = (hasInput != 0);
                }

                if (attributes->GetInt(BMDDeckLinkVideoOutputConnections, &hasOutput) == S_OK) {
                    caps.supports_output = (hasOutput != 0);
                }

                attributes->Release();
            }

            deckLink->Release();
            break;
        }

        deckLink->Release();
        currentIndex++;
    }

    deckLinkIterator->Release();
    return caps;
}

size_t calculateFrameBufferSize(const VideoSettings& settings)
{
    size_t frameSize;
    switch (settings.format) {
        case PixelFormat::Format8BitBGRA:
            frameSize = settings.width * settings.height * 4;
            break;
        case PixelFormat::Format10BitYUV:
            frameSize = ((settings.width + 5) / 6) * 16 * settings.height;
            break;
        case PixelFormat::Format10BitRGB:
            frameSize = settings.width * settings.height * 4;
            break;
        case PixelFormat::Format12BitRGB:
            frameSize = ((settings.width + 7) / 8) * 36 * settings.height;
            break;
        case PixelFormat::Format8BitYUV:
        default:
            frameSize = settings.width * settings.height * 2;
            break;
    }
    return frameSize;
}

}
