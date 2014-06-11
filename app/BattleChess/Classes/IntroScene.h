//
//  IntroScene.h
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#ifndef __SampleGame__IntroScene__
#define __SampleGame__IntroScene__

#include <iostream>
#include "cocos2d.h"
#include "SocketService.h"
#include "CCSwipeGestureRecognizer.h"
#include "cocos-ext.h"

class IntroLayer : public cocos2d::CCLayerColor, public cocos2d::extension::CCEditBoxDelegate
{
public:
    IntroLayer():_label(NULL) {};
    virtual ~IntroLayer();
    virtual bool init();
    CREATE_FUNC(IntroLayer);
    
    void IntroDone();
    void ccTouchesEnded(cocos2d::CCSet* touches, cocos2d::CCEvent* event);
    void tick(float dt);
    
    CCSwipeGestureRecognizer * _swipe;
    void didSwipe(cocos2d::CCObject *swipeObj);
    
    cocos2d::extension::CCEditBox * _pEditName;
    void editboxEventHandler();
    
    virtual void menuCloseCallback(cocos2d::CCObject* pSender);
    void editBoxReturn(cocos2d::extension::CCEditBox* editBox);
    
    void registerWithTouchDispatcher();
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _label, Label);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _titleLabel, TitleLabel);

};

class IntroScene : public cocos2d::CCScene
{
public:
    IntroScene():_layer(NULL) {};
    ~IntroScene();
    bool init();
    void setSocket(SocketService *socket){
        this->ssSocket = socket;
    }
    CREATE_FUNC(IntroScene);
    
    CC_SYNTHESIZE_READONLY(IntroLayer*, _layer, Layer);
    
private:
    SocketService * ssSocket;
};

#endif /* defined(__SampleGame__IntroScene__) */
