//
//  IntroScene.cpp
//  SampleGame
//
//  Created by Pol Monso-Purti on 5/12/14.
//  Copyright (c) 2014 Bullets in a Burning Box, Inc. All rights reserved.
//

#include "IntroScene.h"
#include "GameLayerScene.h"

using namespace cocos2d;
using namespace cocos2d::extension;

bool IntroScene::init()
{
	if( CCScene::init() )
	{
		this->_layer = IntroLayer::create();
		this->_layer->retain();
		this->addChild(_layer);
        return true;
	}
	else
	{
		return false;
	}
}

IntroScene::~IntroScene()
{
	if (_layer)
	{
		_layer->release();
		_layer = NULL;
	}
}

bool IntroLayer::init()
{
	if ( CCLayerColor::initWithColor( ccc4(255,204,153,255) ) )
	{
		CCSize winSize = CCDirector::sharedDirector()->getWinSize();
        
        CCScale9Sprite * fieldSprite = CCScale9Sprite::create("field.png");
        //CCScale9Sprite * fieldSprite = CCScale9Sprite::create("blank.png", CCRectMake(0, 0, 32, 27));
        fieldSprite->setColor(ccc3(255,204,153));
        //CCSprite *fieldSprite = CCSprite::create("field.png");
        fieldSprite->setScale(0.7);
        fieldSprite->setPosition(ccp(winSize.width/2, winSize.height/2));
		//this->addChild(fieldSprite);
        
       
        cocos2d::CCLabelTTF* gameTitleLabel = CCLabelTTF::create("Welcome to BattleChess ","Artial", 15);
		gameTitleLabel->setColor( ccc3(102, 51, 51) );
		gameTitleLabel->setPosition( ccp(winSize.width/2, winSize.height/2 + fieldSprite->boundingBox().size.height) );
		this->addChild(gameTitleLabel);
        
        this->_titleLabel = CCLabelTTF::create("Username: ","Artial", 15);
		_titleLabel->setColor( ccc3(0, 0, 0) );
		_titleLabel->setPosition( ccp(winSize.width/2 - fieldSprite->boundingBox().size.height/2, winSize.height/2 + fieldSprite->boundingBox().size.height/2 + 10) );
		this->addChild(_titleLabel);
        
        std::string name = GameInfo::getUsername();
        
        _pEditName = CCEditBox::create(fieldSprite->boundingBox().size, fieldSprite);
        _pEditName->setPosition(ccp(winSize.width/2, winSize.height/2));
        _pEditName->setFontColor(ccRED);
        _pEditName->setPlaceHolder(name.c_str());
        _pEditName->setMaxLength(8);
        _pEditName->setReturnType(kKeyboardReturnTypeDone);
        _pEditName->setDelegate(this);
        this->addChild(_pEditName);
        
        /*
        _swipe = CCSwipeGestureRecognizer::create();
        _swipe->setTarget(this, callfuncO_selector(IntroLayer::didSwipe));
        _swipe->setDirection(kSwipeGestureRecognizerDirectionRight | kSwipeGestureRecognizerDirectionLeft);
        _swipe->setCancelsTouchesInView(true);
        this->addChild(_swipe);
        */
        this->setTouchEnabled(true);
        
       	schedule( schedule_selector(IntroLayer::tick) );
        
		return true;
	}
	else
	{
		return false;
	}
}

/**
 * This method is called when the return button was pressed or the outside area of keyboard was touched.
 * @param editBox The edit box object that generated the event.
 */
void IntroLayer::editBoxReturn(cocos2d::extension::CCEditBox* editBox) {
    
    if(_pEditName->getText() != NULL){
        fprintf(stderr,"username: %s", _pEditName->getText());
        cocos2d::CCUserDefault::sharedUserDefault()->setStringForKey("username", _pEditName->getText());
    
        CCScene * GameLayerScene = GameLayer::scene();
        CCLog("replacing scene");
        CCDirector::sharedDirector()->replaceScene( GameLayerScene );
    }

    
};

void IntroLayer::didSwipe(cocos2d::CCObject *swipeObj){
    CCLog("swipe detected");
    CCSwipe * swipe = (CCSwipe*)swipeObj;
    CCPoint p = swipe->location;
    
    CCLOG("swiped x pos: %f, y pos: %f", p.x, p.y);
    if(swipe->direction == kSwipeGestureRecognizerDirectionLeft){
        CCLOG("swiped left");
    } else {
        CCLOG("swiped right");
    }
    
}


void IntroLayer::ccTouchesEnded(CCSet* touches, CCEvent* event)
{
    
	// Choose one of the touches to work with
	CCTouch* touch = (CCTouch*)( touches->anyObject() );
	CCPoint location = touch->getLocation();
    
	CCLog("touched  x:%f, y:%f", location.x, location.y);

    //CCScene * pScene = new TextInputTestScene();
    
    
	CCScene * GameLayerScene = GameLayer::scene();

	CCLog("replacing scene");

    CCDirector::sharedDirector()->replaceScene( GameLayerScene );
    
 
}

void IntroLayer::tick(float dt){
    
    
    /*if(_pEditName->getText() != NULL){
        fprintf(stderr,"text: %s", _pEditName->getText());
    }*/
    
    
}

void IntroLayer::IntroDone()
{
	CCDirector::sharedDirector()->replaceScene( GameLayer::scene() );
}

IntroLayer::~IntroLayer()
{
    this->removeAllChildrenWithCleanup(true);
}
