#ifndef __GameLayer_SCENE_H__
#define __GameLayer_SCENE_H__

#include "cocos2d.h"

#include "SimpleAudioEngine.h"
#include "Board.h"
#include "SocketService.h"
#include "GameInfo.h"
#include "CCSwipeGestureRecognizer.h"

#define USELOCALHOST 0

class GameLayer : public cocos2d::CCLayerColor
{
public:
    
    enum state {
        CONNECT,
        GETCOLOR,
        SENDNICK,
        GETURL,
        GETOPPONENT,
        MYTURN,
        WAITMOVEVALIDATION,
        HISTURN,
        UPDATEBOARD,
        WINGAME,
        LOSEGAME,
        UNDECIDEDGAME,
        OVER,
        DECIDEWINNER,
        REPLAY,
        RECONNECT
    };

    cocos2d::CCSprite * _boardSprite;
    
    Board _board;
    cocos2d::CCSpriteBatchNode * _gameBatchNode;
    cocos2d::CCSpriteBatchNode * _gameBatchNodeBoard;
    cocos2d::CCNode * _infoNode;
    cocos2d::CCNode * _tmpTextInfoNode;
    cocos2d::CCSprite * _newGameSprite;
    cocos2d::CCSprite * _replayGameSprite;
    cocos2d::CCSprite * _backgroundGameSprite;
    
    cocos2d::CCMenuItemToggle * _pSoundItem;
    cocos2d::CCMenuItemImage * _pSettingsItem;
    cocos2d::CCMenuItemImage * _pHomeItem;
    
    //cocos2d::CCArray * _players;
    //cocos2d::CCArray * _takenPieces;
        
    GameInfo _gameInfo;
    
    cocos2d::CCSize _screenSize;

    bool _somethingChanged;
    int _state;
    
    SocketService _ssSocket;
    
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _battlechessTitleLabel, BattlechessTitleLabel);
    
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _infoLabel, InfoLabel);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _titleLabel, TitleLabel);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _subtitleLabel, TurnLabel);
    CC_SYNTHESIZE_READONLY(cocos2d::CCLabelTTF*, _label, Label);
    
    GameLayer();
    ~GameLayer();

    // Here's a difference. Method 'init' in cocos2d-x returns bool, 
    // instead of returning 'id' in cocos2d-iphone
    virtual bool init();  

    // there's no 'id' in cpp, so we recommand to return the exactly class pointer
    static cocos2d::CCScene* scene();
    bool screen2board(int xScreen, int yScreen, int& boardX, int& boardY);
    cocos2d::CCPoint board2screen(int boardX, int boardY);
    void createBoard();
    void boardPopulate(const Board& board);

    // a selector callback
    virtual void menuCloseCallback(cocos2d::CCObject* pSender);
    virtual void menuSoundCallback(cocos2d::CCObject* pSender);
    virtual void menuSettingsCallback(cocos2d::CCObject* pSender);
    virtual void menuHomeCallback(cocos2d::CCObject* pSender);

    // implement the "static node()" method manually
    static GameLayer* create();

    void changeState(int newState);
    void updateGame(float dt);

    void registerWithTouchDispatcher();
    CCSwipeGestureRecognizer * _swipe;
    void didSwipe(cocos2d::CCObject *swipeObj);
    void ccTouchesEnded(cocos2d::CCSet* touches, cocos2d::CCEvent* event);
    void ccTouchesMoved(cocos2d::CCSet* touches, cocos2d::CCEvent* event);

    void nextBoard();
    void previousBoard();
    
protected:
    int _replayBoardCount;
    int _squaresize;

};

#endif  // __GameLayer_SCENE_H__
