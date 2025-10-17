cmake_minimum_required(VERSION 3.15...3.27)
project(pixel_reader LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Platform detection and SDK configuration
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    # macOS
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../_vendor/decklink_sdk/Mac")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "${DECKLINK_INCLUDE_DIR}/DeckLinkAPIDispatch.cpp")
    set(PLATFORM_LIBS "-framework CoreFoundation")
    set(PLATFORM_COMPILE_FLAGS "")
    set(PLATFORM_LINK_FLAGS "-framework CoreFoundation")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Linux")
    # Linux
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../_vendor/decklink_sdk/Linux")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "${DECKLINK_INCLUDE_DIR}/DeckLinkAPIDispatch.cpp")
    set(PLATFORM_LIBS pthread dl)
    set(PLATFORM_COMPILE_FLAGS "")
    set(PLATFORM_LINK_FLAGS "-lpthread -ldl")
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    # Windows
    set(DECKLINK_SDK_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../_vendor/decklink_sdk/Win")
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_SDK_PATH}/include")
    set(DECKLINK_SOURCES "")  # Windows doesn't need DeckLinkAPIDispatch.cpp
    set(PLATFORM_LIBS ole32 oleaut32)
    set(PLATFORM_COMPILE_FLAGS "")
    set(PLATFORM_LINK_FLAGS "-lole32 -loleaut32")
else()
    message(FATAL_ERROR "Unsupported platform: ${CMAKE_SYSTEM_NAME}")
endif()

# Check if DeckLink SDK is available
if(NOT EXISTS "${DECKLINK_INCLUDE_DIR}")
    message(FATAL_ERROR "DeckLink SDK not found at: ${DECKLINK_INCLUDE_DIR}")
else()
    message(STATUS "Found DeckLink SDK at: ${DECKLINK_INCLUDE_DIR}")
endif()

# Create the executable
add_executable(pixel_reader
    pixel_reader.cpp
    ${DECKLINK_SOURCES}
)

# Include directories
target_include_directories(pixel_reader PRIVATE
    ${DECKLINK_INCLUDE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/../_vendor
)

# Link libraries
if(PLATFORM_LIBS)
    target_link_libraries(pixel_reader PRIVATE ${PLATFORM_LIBS})
endif()

# Platform-specific compile and link options
if(CMAKE_SYSTEM_NAME STREQUAL "Darwin")
    target_compile_options(pixel_reader PRIVATE -framework CoreFoundation)
    target_link_options(pixel_reader PRIVATE -framework CoreFoundation)
elseif(CMAKE_SYSTEM_NAME STREQUAL "Windows")
    target_compile_definitions(pixel_reader PRIVATE WIN32_LEAN_AND_MEAN)
endif()

# Set output directory
set_target_properties(pixel_reader PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
)
