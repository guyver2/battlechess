EXECUTABLE = SimpleGame

INCLUDES = -I.. -I../Classes

SOURCES = main.cpp \
        ../Classes/AppDelegate.cpp \
        ../Classes/GameOverScene.cpp \
        ../Classes/GameLayerScene.cpp \
        ../Classes/SocketService.cpp \
        ../Classes/Board.cpp     \
        ../Classes/WaitingOpponentScene.cpp \
        ../Classes/GameInfo.cpp  \
        ../Classes/Packet.cpp \
#        ../Classes/StringParser.h \
        ../Classes/SocketService.h \
        ../Classes/Board.h       \
        ../Classes/constants.h   \
        ../Classes/GameOverScene.h   \
        ../Classes/WaitingOpponentScene.h \
        ../Classes/AppDelegate.h \
        ../Classes/GameInfo.h    \
        ../Classes/Packet.h

COCOS_ROOT = ../lib
include $(COCOS_ROOT)/cocos2dx/proj.linux/cocos2dx.mk

SHAREDLIBS += -lcocos2d -lcocosdenshion
COCOS_LIBS = $(LIB_DIR)/libcocos2d.so $(LIB_DIR)/libcocosdenshion.so
INCLUDES += -I$(COCOS_ROOT)/CocosDenshion/include

$(TARGET): $(OBJECTS) $(STATICLIBS) $(COCOS_LIBS) $(CORE_MAKEFILE_LIST)
	@mkdir -p $(@D)
	$(LOG_LINK)$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@ $(SHAREDLIBS) $(STATICLIBS)

$(OBJ_DIR)/%.o: %.cpp $(CORE_MAKEFILE_LIST)
	@mkdir -p $(@D)
	$(LOG_CXX)$(CXX) $(CXXFLAGS) $(INCLUDES) $(DEFINES) $(VISIBILITY) -c $< -o $@

$(OBJ_DIR)/%.o: ../%.cpp $(CORE_MAKEFILE_LIST)
	@mkdir -p $(@D)
	$(LOG_CXX)$(CXX) $(CXXFLAGS) $(INCLUDES) $(DEFINES) $(VISIBILITY) -c $< -o $@
