cmake_minimum_required(VERSION 2.8)
project(battlechess)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -DLINUX -MMD -fPIC ")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS} -fPIC -O3 ")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS} -fPIC -g3 -O1")

set(COCOS_ROOT ../../../.. CACHE STRING "Cocos root dir /cocos2dx/..")
set(COCOS_LIB_ROOT ../../../../.. CACHE STRING "Cocos root dir /cocos2dx/..")
#todo link to release/debug library depending on cmake build
include_directories(.. ../Classes ${COCOS_ROOT}/cocos2dx/proj.linux/)

include_directories(${COCOS_ROOT}/CocosDenshion/include)
set(COCOS_SRC ${COCOS_ROOT}/cocos2dx)
include_directories(
    ${COCOS_SRC} 
    ${COCOS_SRC}/cocoa
    ${COCOS_SRC}/include
    ${COCOS_SRC}/kazmath/include
    ${COCOS_SRC}/platform/linux
    ${COCOS_SRC}/platform/third_party/linux/libpng
    ${COCOS_SRC}/platform/third_party/linux/libjpeg
    ${COCOS_SRC}/platform/third_party/linux/libtiff/include
    ${COCOS_SRC}/platform/third_party/linux/libwebps)

message(STATUS "cocos include dir ${CMAKE_SOURCE_DIR}/${COCOS_SRC}/include")
#if long_bit == 64
include_directories(${COCOS_SRC}/platform/third_party/linux/include64)

link_directories(${COCOS_LIB_ROOT}/lib/linux/release/ ${COCOS_LIB_ROOT}/cocos2dx/platform/third_party/linux/libraries/lib64 ${COCOS_LIB_ROOT}/CocosDenshion/third_party/fmod/lib64/api/lib )

set(COCOS_LIBS cocos2d cocosdenshion)

set(bcsources main.cpp
        ../Classes/AppDelegate.cpp 
        ../Classes/GameOverScene.cpp 
        ../Classes/GameLayerScene.cpp 
        ../Classes/SocketService.cpp 
        ../Classes/Board.cpp     
        ../Classes/WaitingOpponentScene.cpp
        ../Classes/GameInfo.cpp)

add_executable(battlechess ${bcsources})
target_link_libraries(battlechess ${COCOS_LIBS} glfw GLEW fontconfig pthread GL fmodex64 png jpeg freetype webp)
