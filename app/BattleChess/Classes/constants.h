//
//  constants.h
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/16/14.
//
//

#ifndef SimpleGame_constants_h
#define SimpleGame_constants_h

#include "cocos2d.h"

#define COCOS2D_DEBUG 1

#define DEBUG 1

#define DEBUGNOCC(...) \
do { if (DEBUG){  fprintf(stderr, "\n"); fprintf(stderr, __VA_ARGS__); \
fprintf(stderr, " [%s:%d:%s()]\n", __FILE__, __LINE__, __func__); }} while (0)

#define DEBUG2(...) \
do { if (DEBUG){  fprintf(stderr, "\n"); cocos2d::CCLog(__VA_ARGS__); fprintf(stderr, __VA_ARGS__); \
fprintf(stderr, " [%s:%d:%s()]\n", __FILE__, __LINE__, __func__); }} while (0)


#endif
