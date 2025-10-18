cmake_minimum_required(VERSION 3.15...3.27)
project(blackmagic-output VERSION 0.14.0 LANGUAGES CXX)

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

    # Check if we need to compile IDL files
    set(DECKLINK_GENERATED_DIR "${CMAKE_CURRENT_BINARY_DIR}/decklink_generated")
    set(DECKLINK_IDL_FILE "${DECKLINK_INCLUDE_DIR}/DeckLinkAPI.idl")
    set(DECKLINK_HEADER_FILE "${DECKLINK_GENERATED_DIR}/DeckLinkAPI_h.h")

    if(NOT EXISTS "${DECKLINK_HEADER_FILE}")
        message(STATUS "Compiling DeckLink IDL files for Windows...")
        file(MAKE_DIRECTORY "${DECKLINK_GENERATED_DIR}")

        # Find MIDL compiler (part of Windows SDK)
        find_program(MIDL_EXECUTABLE midl
            HINTS
                "C:/Program Files (x86)/Windows Kits/10/bin/*/x64"
                "C:/Program Files (x86)/Windows Kits/10/bin/10.0.*/x64"
                "$ENV{WindowsSdkDir}/bin/*/x64"
        )
        if(NOT MIDL_EXECUTABLE)
            message(FATAL_ERROR "MIDL compiler not found. Please install Windows SDK.\nSearched paths: C:/Program Files (x86)/Windows Kits/10/bin/*/x64")
        endif()

        message(STATUS "Using MIDL: ${MIDL_EXECUTABLE}")
        message(STATUS "IDL file: ${DECKLINK_IDL_FILE}")
        message(STATUS "Output directory: ${DECKLINK_GENERATED_DIR}")

        # Find the C++ compiler directory for MIDL
        get_filename_component(MSVC_DIR "${CMAKE_CXX_COMPILER}" DIRECTORY)

        # Find Windows SDK include directories for system IDL files
        file(GLOB WINSDK_INCLUDE_DIRS "C:/Program Files (x86)/Windows Kits/10/Include/*/um")
        list(GET WINSDK_INCLUDE_DIRS 0 WINSDK_UM_DIR)

        if(NOT WINSDK_UM_DIR)
            message(FATAL_ERROR "Windows SDK um directory not found")
        endif()

        # Also need the shared directory for wtypes.idl, etc.
        get_filename_component(WINSDK_VERSION_DIR "${WINSDK_UM_DIR}" DIRECTORY)
        set(WINSDK_SHARED_DIR "${WINSDK_VERSION_DIR}/shared")

        message(STATUS "Windows SDK um: ${WINSDK_UM_DIR}")
        message(STATUS "Windows SDK shared: ${WINSDK_SHARED_DIR}")

        # Run MIDL to generate headers from IDL
        # Set the PATH to include the MSVC compiler directory so MIDL can find cl.exe
        # Use /I to specify include directories for dependent IDL files
        execute_process(
            COMMAND ${CMAKE_COMMAND} -E env "PATH=${MSVC_DIR};$ENV{PATH}"
                "${MIDL_EXECUTABLE}" /nologo
                /h DeckLinkAPI_h.h
                /iid DeckLinkAPI_i.c
                /I "${DECKLINK_INCLUDE_DIR}"
                /I "${WINSDK_UM_DIR}"
                /I "${WINSDK_SHARED_DIR}"
                "${DECKLINK_IDL_FILE}"
            WORKING_DIRECTORY "${DECKLINK_GENERATED_DIR}"
            RESULT_VARIABLE MIDL_RESULT
            OUTPUT_VARIABLE MIDL_OUTPUT
            ERROR_VARIABLE MIDL_ERROR
        )

        if(NOT MIDL_RESULT EQUAL 0)
            message(FATAL_ERROR "MIDL compilation failed:\nReturn code: ${MIDL_RESULT}\nOutput: ${MIDL_OUTPUT}\nError: ${MIDL_ERROR}")
        endif()

        message(STATUS "MIDL compilation successful")

        # Verify the generated files exist
        if(NOT EXISTS "${DECKLINK_GENERATED_DIR}/DeckLinkAPI_i.c")
            message(FATAL_ERROR "MIDL did not generate DeckLinkAPI_i.c")
        endif()
    endif()

    # Use generated headers directory and include the MIDL-generated source file
    set(DECKLINK_INCLUDE_DIR "${DECKLINK_GENERATED_DIR}")
    set(DECKLINK_SOURCES "${DECKLINK_GENERATED_DIR}/DeckLinkAPI_i.c")
    set(PLATFORM_LIBS ole32 oleaut32 comsuppw)
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
