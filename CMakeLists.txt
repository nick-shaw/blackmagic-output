cmake_minimum_required(VERSION 3.15...3.27)
project(blackmagic-output VERSION 0.13.0 LANGUAGES CXX)

# Find required packages
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# Use scikit-build-core's pybind11 integration
find_package(pybind11 CONFIG REQUIRED)

# Platform detection and SDK configuration
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    # macOS
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/_vendor/decklink_sdk/Mac")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "${DECKLINK_INCLUDE_DIR}/DeckLinkAPIDispatch.cpp")
    set(PLATFORM_LIBS "-framework CoreFoundation")
    set(WRAPPER_SOURCE "src/decklink_wrapper_mac.cpp")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    # Linux
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/_vendor/decklink_sdk/Linux")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "${DECKLINK_INCLUDE_DIR}/DeckLinkAPIDispatch.cpp")
    set(PLATFORM_LIBS pthread dl)
    set(WRAPPER_SOURCE "src/decklink_wrapper.cpp")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    # Windows
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/_vendor/decklink_sdk/Win")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "")  # Windows doesn't need DeckLinkAPIDispatch.cpp
    set(PLATFORM_LIBS ole32 oleaut32)
    set(WRAPPER_SOURCE "src/decklink_wrapper.cpp")
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_SYSTEM_NAME}")
endif()

# Check if DeckLink SDK is available
if(NOT EXISTS "${DECKLINK_INCLUDE_DIR}")
    message(FATAL_ERROR "DeckLink SDK not found at: ${DECKLINK_INCLUDE_DIR}")
endif()

# Create the Python extension module
pybind11_add_module(decklink_output
    src/python_bindings.cpp
    ${WRAPPER_SOURCE}
    src/decklink_hdr_frame.cpp
    ${DECKLINK_SOURCES}
)

# Set C++ standard
target_compile_features(decklink_output PRIVATE cxx_std_17)

# Include directories
target_include_directories(decklink_output PRIVATE
    ${DECKLINK_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# Link libraries
if(PLATFORM_LIBS)
    target_link_libraries(decklink_output PRIVATE ${PLATFORM_LIBS})
endif()

# Platform-specific compile options
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    target_compile_options(decklink_output PRIVATE -framework CoreFoundation)
    target_link_options(decklink_output PRIVATE -framework CoreFoundation)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    target_compile_definitions(decklink_output PRIVATE WIN32_LEAN_AND_MEAN)
endif()

# Install the module
install(TARGETS decklink_output DESTINATION .)
