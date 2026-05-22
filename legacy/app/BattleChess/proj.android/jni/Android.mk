LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := game_shared

LOCAL_MODULE_FILENAME := libgame

LOCAL_SRC_FILES := hellocpp/main.cpp \
                   ../../Classes/AppDelegate.cpp \
                   ../../Classes/GameLayerScene.cpp \
                   ../../Classes/IntroScene.cpp \
                   ../../Classes/Board.cpp ../../Classes/SocketService.cpp ../../Classes/GameInfo.cpp \
                   ../../lib/cocos2d-x-extensions/CCGestureRecognizer/CCSwipeGestureRecognizer.cpp \
                   ../../lib/cocos2d-x-extensions/CCGestureRecognizer/CCGestureRecognizer.cpp# \
                   #../../lib/cocos2d-x-extensions/network/CCHttpRequest.cpp \
                   #../../lib/cocos2d-x-extensions/network/CCNetwork.cpp

                   
LOCAL_C_INCLUDES := $(LOCAL_PATH)/../../Classes                   
LOCAL_C_INCLUDES += $(LOCAL_PATH)/../../lib/cocos2d-x-extensions/CCGestureRecognizer                   
#LOCAL_C_INCLUDES += $(LOCAL_PATH)/../../lib/cocos2d-x-extensions/                   
#LOCAL_C_INCLUDES += $(LOCAL_PATH)/../../lib/cocos2d-x-extensions/network                   

LOCAL_WHOLE_STATIC_LIBRARIES := cocos2dx_static cocosdenshion_static

LOCAL_WHOLE_STATIC_LIBRARIES += cocos_testcpp_common
LOCAL_WHOLE_STATIC_LIBRARIES += cocosdenshion_static
LOCAL_WHOLE_STATIC_LIBRARIES += box2d_static
LOCAL_WHOLE_STATIC_LIBRARIES += chipmunk_static
LOCAL_WHOLE_STATIC_LIBRARIES += cocos_extension_static

include $(BUILD_SHARED_LIBRARY)

$(call import-module,CocosDenshion/android)
$(call import-module,cocos2dx)
$(call import-module,cocos2dx/platform/third_party/android/prebuilt/libcurl)
$(call import-module,CocosDenshion/android)
$(call import-module,extensions)
$(call import-module,external/Box2D)
$(call import-module,external/chipmunk)
