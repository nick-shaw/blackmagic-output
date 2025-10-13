# Makefile for pixel_reader

CXX = g++
TARGET = pixel_reader

# Detect platform
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
    # macOS
    CXXFLAGS = -std=c++11 -I.. -I../decklink_sdk/Mac/include
    LDFLAGS = -framework CoreFoundation
    DECKLINK_DISPATCH = ../decklink_sdk/Mac/include/DeckLinkAPIDispatch.cpp
else ifeq ($(UNAME_S),Linux)
    # Linux
    CXXFLAGS = -std=c++11 -I.. -I../decklink_sdk/Linux/include
    LDFLAGS = -lpthread -ldl
    DECKLINK_DISPATCH = ../decklink_sdk/Linux/include/DeckLinkAPIDispatch.cpp
else
    # Windows (MinGW)
    CXXFLAGS = -std=c++11 -I.. -I../decklink_sdk/Win/include
    LDFLAGS = -lole32 -loleaut32
    DECKLINK_DISPATCH =
endif

SOURCES = pixel_reader.cpp $(DECKLINK_DISPATCH)
OBJECTS = $(SOURCES:.cpp=.o)

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(OBJECTS) $(LDFLAGS) -o $(TARGET)

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

clean:
	rm -f $(OBJECTS) $(TARGET)

.PHONY: all clean
