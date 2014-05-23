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
//using namespace cocos2d::extension;

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
	if ( CCLayerColor::initWithColor( ccc4(255,255,255,255) ) )
	{
		CCSize winSize = CCDirector::sharedDirector()->getWinSize();
        
        //CCScale9Sprite * fieldSprite = CCScale9Sprite::create("field.png");
        CCSprite *fieldSprite = CCSprite::create("field.png");
        fieldSprite->setPosition(ccp(winSize.width/2, winSize.height/2));
		this->addChild(fieldSprite);
        
        this->_titleLabel = CCLabelTTF::create("Username: ","Artial", 15);
		_titleLabel->setColor( ccc3(0, 0, 0) );
		_titleLabel->setPosition( ccp(winSize.width/2, winSize.height/2 + fieldSprite->boundingBox().size.height) );
		this->addChild(_titleLabel);

        
        /* I couldn't get this to work
        m_pEditName = CCEditBox::create(fieldSprite->boundingBox().size, fieldSprite);
        
        m_pEditName->setPosition(ccp(winSize.width/2, winSize.height/2));
        
        m_pEditName->setFontColor(ccRED);
        
        m_pEditName->setPlaceHolder("Name:");
        
        m_pEditName->setMaxLength(8);
        
        m_pEditName->setReturnType(kKeyboardReturnTypeDone);
        
        //m_pEditName->setDelegate(this);
        
        this->addChild(m_pEditName);
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


void IntroLayer::ccTouchesEnded(CCSet* touches, CCEvent* event)
{
    
	// Choose one of the touches to work with
	CCTouch* touch = (CCTouch*)( touches->anyObject() );
	CCPoint location = touch->getLocation();
    
	CCLog("touched  x:%f, y:%f", location.x, location.y);

	CCScene * GameLayerScene = GameLayer::scene();

	CCLog("replacing scene");

    CCDirector::sharedDirector()->replaceScene( GameLayerScene );

    
 
}

void IntroLayer::tick(float dt){
    
    /*
    if(m_pEditName->getText() != NULL){
        fprintf(stderr,"text: %s", m_pEditName->getText());
    }
     */
    
    
}

void IntroLayer::IntroDone()
{
	CCDirector::sharedDirector()->replaceScene( GameLayer::scene() );
}

IntroLayer::~IntroLayer()
{
    this->removeAllChildrenWithCleanup(true);
}
