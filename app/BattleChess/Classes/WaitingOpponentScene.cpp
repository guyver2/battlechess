//
//  WaitingOpponentScene.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#include "WaitingOpponentScene.h"
#include "GameLayerScene.h"

using namespace cocos2d;

bool WaitingOpponentScene::init()
{
	if( CCScene::init() )
	{
		this->_layer = WaitingOpponentLayer::create();
		this->_layer->retain();
		this->addChild(_layer);
		
		return true;
	}
	else
	{
		return false;
	}
}

WaitingOpponentScene::~WaitingOpponentScene()
{
	if (_layer)
	{
		_layer->release();
		_layer = NULL;
	}
}


bool WaitingOpponentLayer::init()
{
	if ( CCLayerColor::initWithColor( ccc4(255,255,255,255) ) )
	{
		CCSize winSize = CCDirector::sharedDirector()->getWinSize();
		this->_label = CCLabelTTF::create("","Artial", 32);
		_label->retain();
		_label->setColor( ccc3(0, 0, 0) );
		_label->setPosition( ccp(winSize.width/2, winSize.height/2) );
		this->addChild(_label);
		
        
        CCSprite * sprite = CCSprite::createWithSpriteFrameName("replay.png");
        sprite->setPosition(ccp(winSize.width/2 - 10, winSize.height/2 - 32));
        sprite->setAnchorPoint(ccp(1,0));
        this->addChild(sprite, Board::kForeground);
        
        sprite = CCSprite::createWithSpriteFrameName("new_game.png");
        sprite->setAnchorPoint(ccp(0,0));
        sprite->setPosition(ccp(winSize.width/2 + 10, winSize.height/2 - 32));
        this->addChild(sprite, Board::kForeground);

        
		this->runAction( CCSequence::create(
                                            CCDelayTime::create(10),
                                            CCCallFunc::create(this,
                                                               callfunc_selector(WaitingOpponentLayer::waitingOpponentDone)),
                                            NULL));
		this->setTouchEnabled(true);

		return true;
	}
	else
	{
		return false;
	}
}

void WaitingOpponentLayer::waitingOpponentDone()
{
}


void WaitingOpponentLayer::ccTouchesEnded(CCSet* touches, CCEvent* event)
{
    
	// Choose one of the touches to work with
	CCTouch* touch = (CCTouch*)( touches->anyObject() );
	CCPoint location = touch->getLocation();
    
	CCLog("touched  x:%f, y:%f", location.x, location.y);
    
    CCDirector::sharedDirector()->replaceScene( GameLayer::scene() );
    
    //CCSwipeGestureRecognizerDirection direction;
    
}



WaitingOpponentLayer::~WaitingOpponentLayer()
{
	if (_label)
	{
		_label->release();
		_label = NULL;
	}
}
