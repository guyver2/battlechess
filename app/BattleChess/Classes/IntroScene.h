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
    

private:
    void IntroDone();
    void ccTouchesEnded(cocos2d::CCSet* touches, cocos2d::CCEvent* event);
    void tick(float dt);
    
    cocos2d::extension::CCEditBox * _pEditName;
    void editboxEventHandler();
    
    
    virtual void menuCloseCallback(cocos2d::CCObject* pSender);
    void editBoxReturn(cocos2d::extension::CCEditBox* editBox);
    
    void registerWithTouchDispatcher();
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _label, Label);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _titleLabel, TitleLabel);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _battlechessTitleLabel, BattlechessTitleLabel);
    cocos2d::CCSprite * _backgroundGameSprite;
    
    CCSwipeGestureRecognizer * _swipe;
    void didSwipe(cocos2d::CCObject *swipeObj);


};

class IntroScene : public cocos2d::CCScene
{
public:
    IntroScene():_layer(NULL) {};
    ~IntroScene();
    bool init();
    CREATE_FUNC(IntroScene);
    
    CC_SYNTHESIZE_READONLY(IntroLayer*, _layer, Layer);
    
};

#endif /* defined(__SampleGame__IntroScene__) */
