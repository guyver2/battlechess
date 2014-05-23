//
//  WaitingOpponentScene.h
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#ifndef __SampleGame__WaitingOpponentScene__
#define __SampleGame__WaitingOpponentScene__

#include <iostream>
#include "cocos2d.h"
#include "SocketService.h"

class WaitingOpponentLayer : public cocos2d::CCLayerColor
{
public:
    WaitingOpponentLayer():_label(NULL) {};
    virtual ~WaitingOpponentLayer();
    bool init();
    CREATE_FUNC(WaitingOpponentLayer);
    
    void waitingOpponentDone();
    void ccTouchesEnded(cocos2d::CCSet* touches, cocos2d::CCEvent* event);
    
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _label, Label);
};

class WaitingOpponentScene : public cocos2d::CCScene
{
public:
    WaitingOpponentScene():_layer(NULL) {};
    ~WaitingOpponentScene();
    bool init();
    void setSocket(SocketService *socket){
        this->ssSocket = socket;
    }
    CREATE_FUNC(WaitingOpponentScene);
    
    CC_SYNTHESIZE_READONLY(WaitingOpponentLayer*, _layer, Layer);
private:
    SocketService * ssSocket;
};

#endif /* defined(__SampleGame__WaitingOpponentScene__) */
