#include "GameLayerScene.h"
#include "IntroScene.h"
#include "SimpleAudioEngine.h"

using namespace cocos2d;
using namespace std;

const char *state_str[]={
    "CONNECT",
    "GETCOLOR",
    "SENDNICK",
    "GETURL",
    "GETOPPONENT",
    "MYTURN",
    "WAITMOVEVALIDATION",
    "HISTURN",
    "UPDATEBOARD",
    "WINGAME",
    "LOSEGAME",
    "UNDECIDEDGAME",
    "OVER",
    "DECIDEWINNER",
    "REPLAY",
    "RECONNECT" };

GameLayer::GameLayer() : _state(CONNECT), _somethingChanged(true)
{
	CCLog("GameLayer Contructor...");
    _replayBoardCount = 0;

}

GameLayer::~GameLayer()
{
    
	// cpp don't need to call super dealloc
	// virtual destructor will do this
}

CCScene* GameLayer::scene()
{

	CCScene * scene = NULL;
	do 
	{
		// 'scene' is an autorelease object
		scene = CCScene::create();
		CC_BREAK_IF(! scene);
		// 'layer' is an autorelease object
		GameLayer *layer = GameLayer::create();

		CC_BREAK_IF(! layer);

		// add layer as a child to scene
		scene->addChild(layer);

	} while (0);

	// return the scene
	return scene;
}

GameLayer* GameLayer::create()
{
	GameLayer *pRet;
	pRet = new GameLayer();
    if (pRet && pRet->init())
    {
        pRet->autorelease();
        return pRet;
    }
    else
    {
        delete pRet;
        pRet = NULL;
        return NULL;
    }
}

// on "init" you need to initialize your instance
bool GameLayer::init()
{
	bool bRet = false;
	do 
	{
		CC_BREAK_IF(! CCLayerColor::initWithColor( ccc4(204,204,204,255) ) );

        //TODO does this go here?
        _screenSize = CCDirector::sharedDirector()->getVisibleSize();
        
		// 1. Add a menu item with "X" image, which is clicked to quit the program.
        cocos2d::CCArray* pMenuItems = cocos2d::CCArray::create();
        
		// Create a "close" menu item with close icon, it's an auto release object.
		CCMenuItemImage *pCloseItem = CCMenuItemImage::create(
			"CloseNormal.png",
			"CloseSelected.png",
			this,
			menu_selector(GameLayer::menuCloseCallback));
        CC_BREAK_IF(! pCloseItem);
        pMenuItems->addObject(pCloseItem);

        /*
        CCMenuItemImage *pSoundItem = CCMenuItemImage::create(
            "SoundOn.png",
            "SoundOff.png",
            this,
            menu_selector(GameLayer::menuSoundCallback));
        */
        
        CCMenuItemSprite* p1 = CCMenuItemSprite::create(CCSprite::create("SoundOn.png"), CCSprite::create("SoundOff.png"));
        CCMenuItemSprite* p2 = CCMenuItemSprite::create(CCSprite::create("SoundOff.png"), CCSprite::create("SoundOn.png"));
        
        _pSoundItem = CCMenuItemToggle::createWithTarget(this, menu_selector(GameLayer::menuSoundCallback), p1, p2,NULL);
        CC_BREAK_IF(! _pSoundItem);
        //TODO get sound from default user
        _pSoundItem->setSelectedIndex(0);
        pMenuItems->addObject(_pSoundItem);
        
        _pSettingsItem = CCMenuItemImage::create(
            "SettingsOn.png",
            "SettingsOff.png",
            this,
            menu_selector(GameLayer::menuSettingsCallback));
        CC_BREAK_IF(! _pSettingsItem);
        pMenuItems->addObject(_pSettingsItem);
                              
        _pHomeItem = CCMenuItemImage::create(
            "HomeOn.png",
            "HomeOff.png",
            this,
            menu_selector(GameLayer::menuHomeCallback));
		CC_BREAK_IF(! _pHomeItem);
        pMenuItems->addObject(_pHomeItem);
        
        CCMenu* pMenu = CCMenu::createWithArray(pMenuItems);
        
		// Place the menu item bottom-right conner.
        CCPoint origin = CCDirector::sharedDirector()->getVisibleOrigin();
        
        CCPoint lastItemPosition = ccp(origin.x + _screenSize.width - pCloseItem->getContentSize().width/2,
                                       origin.y + pCloseItem->getContentSize().height/2);
        //TODO 'for' this
		pCloseItem->setPosition(lastItemPosition);
        lastItemPosition = lastItemPosition - ccp(_pSoundItem->getContentSize().width,0);
        _pSoundItem->setPosition(lastItemPosition);
        lastItemPosition = lastItemPosition - ccp(_pSettingsItem->getContentSize().width,0);
        _pSettingsItem->setPosition(lastItemPosition);
        lastItemPosition = lastItemPosition - ccp(_pHomeItem->getContentSize().width,0);
		_pHomeItem->setPosition(lastItemPosition);

		// Create a menu with the "close" menu item, it's an auto release object.
		pMenu->setPosition(CCPointZero);
		CC_BREAK_IF(! pMenu);

		// Add the menu to GameLayer layer as a child layer.
		this->addChild(pMenu, 1);

        createBoard();
        
        _tmpTextInfoNode = new cocos2d::CCNode();
        _label = CCLabelTTF::create("Connecting...","Artial", 32);
         _label->setColor( ccc3(255, 0, 0) );
         _label->setPosition( ccp(_screenSize.width/2, _screenSize.height/2) );
         _tmpTextInfoNode->addChild(_label);
         this->addChild(_tmpTextInfoNode, Board::kForeground);

        _infoNode = new cocos2d::CCNode();
        _subtitleLabel = CCLabelTTF::create("","Artial", 12);
        _subtitleLabel->setColor( ccc3(255, 0, 0) );
        CCPoint subtitlePoint = board2screen(-1,0);
        subtitlePoint.y -= 5;
        _subtitleLabel->setPosition( subtitlePoint );
        _subtitleLabel->setAnchorPoint(ccp(0,1));
        _infoNode->addChild(_subtitleLabel);

        std::string title = _gameInfo.playerName + " Game";
        _titleLabel = CCLabelTTF::create(title.c_str(), "Artial", 24);
        _titleLabel->setColor( ccc3(0, 0, 0) );
        CCPoint titlePoint = board2screen(-1,3);
        titlePoint.y += 15;
        //titlePoint.y = _screenSize.height/2;
        _titleLabel->setPosition( titlePoint );
        _titleLabel->setAnchorPoint(ccp(0,0.5f));
        _infoNode->addChild(_titleLabel);

        this->addChild(_infoNode, Board::kForeground);

        //_backgroundGameSprite = CCSprite::createWithSpriteFrameName("background.png");
        _backgroundGameSprite = CCSprite::create("background.png");
        if(_backgroundGameSprite) {

            _backgroundGameSprite->setScale(max(_screenSize.width/_backgroundGameSprite->boundingBox().size.width,_screenSize.height/_backgroundGameSprite->boundingBox().size.height));

            _backgroundGameSprite->setOpacity(100);
            _backgroundGameSprite->setPosition(ccp(_screenSize.width/2, _screenSize.height/2));
            _backgroundGameSprite->setVisible(true);

            this->addChild(_backgroundGameSprite, Board::kBackground);
        } else {
            DEBUG2("Background image could not be loaded. Ignoring it.");
        }

        //todo MAYBE remove all children destroys the sprite //indeed
        boardPopulate(_board);

        _replayGameSprite = CCSprite::createWithSpriteFrameName("replay.png");
        _replayGameSprite->setAnchorPoint(ccp(1,0));
        _replayGameSprite->setPosition(ccp(_screenSize.width/2, _screenSize.height/2 - 64));
        _replayGameSprite->setVisible(false);
        this->addChild(_replayGameSprite, Board::kForeground);
        
        _newGameSprite = CCSprite::createWithSpriteFrameName("new_game.png");
        _newGameSprite->setAnchorPoint(ccp(0,0));
        _newGameSprite->setPosition(ccp(_screenSize.width/2, _screenSize.height/2 - 64));
        _newGameSprite->setVisible(false);
        this->addChild(_newGameSprite, Board::kForeground);
        
        //TODO implement sender if sprite cliecked, go to new game or replay
        _swipe = CCSwipeGestureRecognizer::create();
        _swipe->setTarget(this, callfuncO_selector(GameLayer::didSwipe));
        _swipe->setDirection(kSwipeGestureRecognizerDirectionRight | kSwipeGestureRecognizerDirectionLeft);
        _swipe->setCancelsTouchesInView(true);
        this->addChild(_swipe);

		this->setTouchEnabled(true);

		// use updateGame instead of update, otherwise it will conflit with SelectorProtocol::update
		// see http://www.cocos2d-x.org/boards/6/topics/1478
		this->schedule( schedule_selector(GameLayer::updateGame) );

        //music
		//CocosDenshion::SimpleAudioEngine::sharedEngine()->playBackgroundMusic("background-music-aac.wav", true);

		bRet = true;

	} while (0);

	return bRet;
}

//coordinate system: www.cocos2d-x.org/wiki/Coordinate_System
// bottom left (0,0)
//top left (0,winSize)
//So when using coordinates top left (0,0) bottom left (7,0) everything is mirroed in both axis
bool GameLayer::screen2board(int xScreen, int yScreen, int& boardX, int& boardY){
    boardY = (xScreen  - _screenSize.width  * 0.5f + 4.0f*_squaresize)/_squaresize;
    boardX = (-yScreen + _screenSize.height * 0.5f + 4.0f*_squaresize)/_squaresize;
    if(!Board::isIn(boardX, boardY))
        return false;
    return true;
}

cocos2d::CCPoint GameLayer::board2screen(int boardX, int boardY){
    int xScreen = _screenSize.width * 0.5f - 4.0f*_squaresize + boardY*_squaresize;
    int yScreen = _screenSize.height * 0.5f + 4.0f*_squaresize - boardX*_squaresize;
    return ccp(xScreen, yScreen);
}

void GameLayer::createBoard(){
    
    CCSpriteFrameCache::sharedSpriteFrameCache()->addSpriteFramesWithFile("battlechessSprites.plist");
    _gameBatchNode = CCSpriteBatchNode::create("battlechessSprites.png");
    this->addChild(_gameBatchNode, Board::kPieces);

    _gameBatchNodeBoard = CCSpriteBatchNode::create("battlechessSprites.png");
    this->addChild(_gameBatchNodeBoard, Board::kBoard);
    
    _boardSprite = CCSprite::createWithSpriteFrameName("board.png");
    _squaresize = _boardSprite->boundingBox().size.height/8;
    DEBUG2("board size %f so squaresize %d", _boardSprite->boundingBox().size.height, _squaresize);

    _boardSprite->setPosition(ccp(_screenSize.width * 0.5f, _screenSize.height * 0.5f));
    _gameBatchNodeBoard->addChild(_boardSprite, Board::kBoard);
    

}

void GameLayer::nextBoard(){
    assert(_board._collectedBoardStrings.size() > 0);
    _replayBoardCount = (_replayBoardCount+1)%_board._collectedBoardStrings.size();
    _board.fromStringWithoutSave(_board._collectedBoardStrings[_replayBoardCount]);
}

void GameLayer::previousBoard(){
    assert(_board._collectedBoardStrings.size() > 0);
    _replayBoardCount = (_replayBoardCount-1+_board._collectedBoardStrings.size())%_board._collectedBoardStrings.size();
    _board.fromStringWithoutSave(_board._collectedBoardStrings[_replayBoardCount]);
}


void GameLayer::boardPopulate(const Board& board){
    
    //FIXME maybe we can move sprites instead of destroying and recreating (deal with pawn promotion thought)
    _gameBatchNode->removeAllChildrenWithCleanup(true);
  
    CCSprite * sprite;
    CCPoint pieceAnchorPoint = ccp(0,1);

    int takenW = 0;
    int takenB = 0;
    for(int i=0; i< _board._taken.size(); i++){
        std::string piece = _board._taken[i] + ".png";
        sprite = CCSprite::createWithSpriteFrameName(piece.c_str());
        sprite->setAnchorPoint(pieceAnchorPoint);
        float scale = 0.5f;
        sprite->setScale(scale);
        if(piece.c_str()[1] == 'w'){
            //horizontal
            //sprite->setPosition(board2screen(takenW/2, -2 + takenW%2));
            CCPoint screenPoint = board2screen(0,0);
            screenPoint.y += _squaresize/2 + 10;
            screenPoint.x += takenW*_squaresize/2;
            sprite->setPosition(screenPoint);
            takenW++;
        }else{
            //horizontal
            //sprite->setPosition(board2screen(7 - takenB/2, 8 + takenB%2));
            CCPoint screenPoint = board2screen(8,0);
            screenPoint.y += -_squaresize/2 + 10;
            screenPoint.x += takenB*_squaresize/2;
            sprite->setPosition(screenPoint);
            takenB++;
        }
        _gameBatchNode->addChild(sprite, Board::kPieces);
    }

    for(int j=0; j<8; j++){
        for(int i=0; i<8; i++){
            if(_state != WINGAME && _state != LOSEGAME){
                char color;
                if(_state == REPLAY)
                    color = (_replayBoardCount%2 == 0 ? 'w' : 'b' );
                else
                    color = _gameInfo.playerColor;
                
                if(board.foggy(i,j,color)){
                    sprite = CCSprite::createWithSpriteFrameName("blank.png");
                    sprite->setAnchorPoint(pieceAnchorPoint);
                    sprite->setPosition(board2screen(i,j));
                    sprite->setOpacity(100);
                    sprite->setColor(ccc3(0,0,0));
                    _gameBatchNode->addChild(sprite, Board::kBoard);
                }
            }
            string piece = board._board[i][j];
            if(piece == "")
                continue;
            piece += ".png";
            sprite = CCSprite::createWithSpriteFrameName(piece.c_str());
            sprite->setAnchorPoint(pieceAnchorPoint);
            sprite->setPosition(board2screen(i,j));
            if(_board._move._validOrigin && _board._move._originI == i && _board._move._originJ == j){
                sprite->setOpacity(100);
                sprite->setColor(ccc3(255,0,0));
            }
            _gameBatchNode->addChild(sprite, Board::kPieces);
            
        }
    }
    
    if(_board._move._validOrigin){
        sprite = CCSprite::createWithSpriteFrameName("blank.png");
        sprite->setAnchorPoint(pieceAnchorPoint);
        sprite->setPosition(board2screen(_board._move._originI,_board._move._originJ));
        sprite->setOpacity(100);
        sprite->setColor(ccc3(255,0,0));
        _gameBatchNode->addChild(sprite, Board::kBoard);
        
    }
    
    if(_state == MYTURN){
        //modified on Board.cpp::updatePossiblePositions() when valid move origin
        for(int i=0; i<_board._possiblePositions.size();i++){
            std::pair<int,int> position = _board._possiblePositions.at(i);
            sprite = CCSprite::createWithSpriteFrameName("blank.png");
            sprite->setAnchorPoint(pieceAnchorPoint);
            sprite->setPosition(board2screen(position.first,position.second));
            sprite->setOpacity(100);
            sprite->setColor(ccc3(255,0,0));
            _gameBatchNode->addChild(sprite, Board::kBoard);
        }
    }

    //FIXME move the game info to somewhere else
    if(_state == MYTURN) {
        if(_gameInfo.playerColor == 'w')
            _subtitleLabel->setString(GameInfo::WHITE.c_str());
        else
            _subtitleLabel->setString(GameInfo::BLACK.c_str());
    }else if(_state == HISTURN) {
        if(_gameInfo.playerColor == 'w')
            _subtitleLabel->setString(GameInfo::BLACK.c_str());
        else
            _subtitleLabel->setString(GameInfo::WHITE.c_str());
    }else{
        //_subtitleLabel->setString("");
    }
    
}

void GameLayer::menuCloseCallback(CCObject* pSender)
{
	// "close" menu item clicked
#if (CC_TARGET_PLATFORM == CC_PLATFORM_WINRT) || (CC_TARGET_PLATFORM == CC_PLATFORM_WP8)
    CCMessageBox("You pressed the close button. Windows Store Apps do not implement a close button.", "Alert");
#else
    CCDirector::sharedDirector()->end();
//#if (CC_TARGET_PLATFORM == CC_PLATFORM_IOS)
    //Android fails to close too
    exit(0);
//#endif
#endif
}

void GameLayer::menuSoundCallback(CCObject* pSender)
{
    //TODO use setEffectVolume(0) and setBackgroundMusicVolume(0)
    
    bool sound = cocos2d::CCUserDefault::sharedUserDefault()->getBoolForKey("sound", false);
    cocos2d::CCUserDefault::sharedUserDefault()->setBoolForKey("sound", !sound);
    if(sound)
        _pSoundItem->setSelectedIndex(0);
    else
        _pSoundItem->setSelectedIndex(1);


}
void GameLayer::menuSettingsCallback(CCObject* pSender)
{
    changeState(OVER);
    IntroScene * IntroScene = IntroScene::create();
    CCDirector::sharedDirector()->replaceScene( IntroScene );

}
void GameLayer::menuHomeCallback(CCObject* pSender)
{
    changeState(OVER);
    CCScene * gameScene = GameLayer::scene();
    CCDirector::sharedDirector()->replaceScene( gameScene );

}

void GameLayer::didSwipe(cocos2d::CCObject *swipeObj){
    CCSwipe * swipe = (CCSwipe*)swipeObj;
    CCPoint p = swipe->location;
    
    if(_state == REPLAY) {
        _somethingChanged = true;
        if(swipe->direction == kSwipeGestureRecognizerDirectionLeft){
            CCLOG("swiped left");
            nextBoard();
        } else {
            CCLOG("swiped right");
            previousBoard();
        }
    }
}


}
void GameLayer::menuSettingsCallback(CCObject* pSender)
{
    changeState(OVER);
    IntroScene * IntroScene = IntroScene::create();
    CCDirector::sharedDirector()->replaceScene( IntroScene );

}
void GameLayer::menuHomeCallback(CCObject* pSender)
{
    changeState(OVER);
    CCScene * gameScene = GameLayer::scene();
    CCDirector::sharedDirector()->replaceScene( gameScene );

}

void GameLayer::didSwipe(cocos2d::CCObject *swipeObj){
    CCSwipe * swipe = (CCSwipe*)swipeObj;
    CCPoint p = swipe->location;
    
    if(_state == REPLAY) {
        _somethingChanged = true;
        if(swipe->direction == kSwipeGestureRecognizerDirectionLeft){
            CCLOG("swiped left");
            nextBoard();
        } else {
            CCLOG("swiped right");
            previousBoard();
        }
    }
}


void GameLayer::ccTouchesMoved(CCSet* touches, CCEvent* event)
{
    _somethingChanged = true;
}

void GameLayer::ccTouchesEnded(CCSet* touches, CCEvent* event)
{
    
	// Choose one of the touches to work with
	CCTouch* touch = (CCTouch*)( touches->anyObject() );
	CCPoint location = touch->getLocation();
    
	CCLog("touched  x:%f, y:%f", location.x, location.y);

    _somethingChanged = true;
    
    switch(_state){
        case MYTURN:
            {
                int i,j;
                if(!screen2board(location.x, location.y, i, j))
                    break;
                CCLog("board coords i:%d, j:%d",i,j);
                if(!_board._move._validOrigin) {
                    _board.setSelectedOrigin(i,j, _gameInfo.playerColor);
                    break;
                }
                if(!_board._move._validDest)
                    _board.setSelectedDest(i,j);
                if(!_board._move._validDest)
                    break;
                std::string prevSelPiece = _board.getSelectedPiece();
                std::string newSelPiece = _board._board[i][j];
                if(newSelPiece != "" && newSelPiece.c_str()[1] == _gameInfo.playerColor){
                    //we clicked at a piece of ours, change last selected piece
                    _board.setSelectedOrigin(i,j, _gameInfo.playerColor);
                    //invalidate dest
                    _board._move._validDest = false;
                // }else if(newSelPiece == "" || newSelPiece.c_str()[1] != _gameInfo.playerColor){
                    //we had a selected piece and now we're trying to move or kill
                    //_board.setSelectedDest(i,j);
                }else{
                    //clicked at an empty spot or at an enemy piece
                    //cancel
                    //_board._move._validOrigin = false;
                    //_board._move._validDest = false;
                }
            }
            break;
        case WINGAME:
        case LOSEGAME:
        case UNDECIDEDGAME:
        case OVER:
        case DECIDEWINNER:
            if (_newGameSprite->boundingBox().containsPoint(location))
            //FIXME maybe we can do something else rather than replacing the scnee with a new one
                CCDirector::sharedDirector()->replaceScene( GameLayer::scene() );
            else if(_replayGameSprite->boundingBox().containsPoint(location)){
                 std::string content;
                _ssSocket.openUrl(_gameInfo.gameUrl, content);
                if(content == "") {
                    DEBUG2("Connection failed. Defaulting to same scene.");
                    _label->setString("Replay connection failed.");
                    _label->setVisible(true);
                    break;
                }
                //retrieve all board strings //FIXME creating Boards causes error on destructor
                _board._collectedBoardStrings = _board.boardsStringsFromMoves(content);
                
                if(_board._collectedBoardStrings.size() == 0){
                    DEBUG2("Connection failed. Defaulting to same scene.");
                    _label->setString("Replay connection failed.");
                    _label->setVisible(true);
                    break;
                }
                    
                //go to last board
                _replayBoardCount = _board._collectedBoardStrings.size()-1;
                
                //_replayBoards = _board.boardsFromStrings();
                _newGameSprite->setVisible(false);
                _replayGameSprite->setVisible(false);
                _label->setVisible(false);
                _subtitleLabel->setString("Swipe left/right for replay");
                _subtitleLabel->setVisible(true);
                changeState(REPLAY);
            } else {
                DEBUG2("Clicked somewhere else. Defaulting to new game.");
                CCDirector::sharedDirector()->replaceScene( GameLayer::scene() );
            }
            break;
        case REPLAY:
            
            break;
        default:
            //do nothing for now
            break;
    }
}

void GameLayer::changeState(int newState){
    CCLog("Changing state %s -> %s...", state_str[_state], state_str[newState]);
    _state = newState;
    _somethingChanged = true;
}

void GameLayer::updateGame(float dt)
{

    Packet packet;
    switch(_state){
        case RECONNECT:
            //TODO connection was lost
            break;
        case CONNECT:
        	CCLog("About to connect");
#if USELOCALHOST
            if(_ssSocket.ssconnect("localhost",8887) >= 0){
#else
            if(_ssSocket.ssconnect("sxbn.org",8887) >= 0){
#endif
            	CCLog("Connected starting thread...");
                _ssSocket.start();
                changeState( GETCOLOR );
            	//CCLog("Going to state GETCOLOR...");
            }else{
                std::stringstream ss;
                ss << "Connection failed. " << _ssSocket._host << ":" << _ssSocket._port;
                _label->setString(ss.str().c_str());
            }
            break;
        case GETCOLOR:
            //socket
        	CCLog("about to connect");
            if(_ssSocket.getPacket(packet)){
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                if(packet.header != "COLR"){
                    //error
                    DEBUG2("Expecting COLR got %s:%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                fprintf(stderr,"I'll be player %s\n", packet.body.c_str());
                _gameInfo.setPlayerColor(packet.body);
                //CCLog("Going to state SENDNICK...");
                changeState( SENDNICK );
            }
            break;
        case SENDNICK:
            {
                packet = Packet(std::string("NICK"),_gameInfo.playerName);
                _ssSocket.sendPacket(packet);

                //draw the waiting opponent scene
                DEBUG2("Waiting opponent...");
                _label->setString("Waiting Opponent...");
            	//CCLog("Going to state GETURL...");
                changeState( GETURL );
            }
            break;
        case GETURL:
            if(_ssSocket.getPacket(packet)){
                //FIXME handle waiting oponent through a scene
                _label->setVisible(false);
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                if(packet.header != "URLR"){
                    //error
                    DEBUG2("Expecting URLR got %s%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                _gameInfo.gameUrl = packet.body;
            	//CCLog("Going to state GETOPPONENT...");
                changeState( GETOPPONENT );
            }
            break;
        case GETOPPONENT:
            if(_ssSocket.getPacket(packet)){
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                if(packet.header != "NICK"){
                    //error
                    DEBUG2("Expecting NICK got %s%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                _gameInfo.opponentName = packet.body;
                
                _titleLabel->setString((_gameInfo.playerName + " vs. " + _gameInfo.opponentName).c_str());
                if(_gameInfo.playerColor == 'w')
                    changeState( MYTURN );
                else
                    changeState( HISTURN );
                break;
            }
            break;
        case MYTURN:
            //get movement (done automatically by touches)
            {
                if(!_board._move._validOrigin)
                    break;
                std::string selPiece = _board.getSelectedPiece();
                if(selPiece == "")
                    break;
                if(_board._move.isValid()){
                    DEBUG2("piece = %s.",selPiece.c_str());
                    _board._move._validOrigin = false;
                    _board._move._validDest = false;
                    //send movement
                    packet.header = "MOVE";
                    std::stringstream sstm;

                    sstm << _board._move._originI <<  _board._move._originJ <<  _board._move._destI <<  _board._move._destJ;
                    packet.body = sstm.str();
                    _ssSocket.sendPacket(packet);
                    changeState( WAITMOVEVALIDATION );

                }
            }
            break;
        case WAITMOVEVALIDATION:
            if(_ssSocket.getPacket(packet)){
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                if(packet.header != "VALD"){
                    //error
                    DEBUG2("Expecting VALD got %s%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                if(packet.body == "T"){
                    changeState( UPDATEBOARD );
                    _board._possiblePositions.clear();
                }
                else if(packet.body == "F"){
                    _board._move._validDest = false;
                    changeState( MYTURN );
                } else {
                    DEBUG2("Unrecognized valid reply. Aborting.");
                    changeState( OVER );
                }
            }
            break;
        case UPDATEBOARD:
            if(_ssSocket.getPacket(packet)){
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                //we got an updated board
                if(packet.header != "BORD"){
                    //error
                    DEBUG2("Expecting BORD got %s%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                _board.fromString(packet.body);
                if(_board._winner == 'n')
                    changeState( HISTURN );
                else
                    changeState( DECIDEWINNER );
            }

            break;
        case HISTURN:
            //retrieve board
            if(_ssSocket.getPacket(packet)){

                if(cocos2d::CCUserDefault::sharedUserDefault()->getBoolForKey("sound", true))
                    CocosDenshion::SimpleAudioEngine::sharedEngine()->playEffect("pew-pew-lei.wav");
                if(packet.header == "OVER"){
                    changeState( OVER );
                    break;
                }
                //we got an updated board
                if(packet.header != "BORD"){
                    //error
                    DEBUG2("Expecting BORD got %s%s",packet.header.c_str(),packet.body.c_str());
                    changeState( OVER );
                    break;
                }
                _board.fromString(packet.body);
                if(_board._winner == 'n')
                    changeState( MYTURN );
                else
                    changeState( DECIDEWINNER );
            }
            break;
        case WINGAME:
            _label->setString("You killed the King! You Won.");
            _label->setVisible(true);
            _newGameSprite->setVisible(true);
            _replayGameSprite->setVisible(true);            
            break;
        case LOSEGAME:
            _label->setString("Your King died. You Lost.");
            _label->setVisible(true);
            _newGameSprite->setVisible(true);
            _replayGameSprite->setVisible(true);
            break;
        case UNDECIDEDGAME:
            _label->setString("Undecided game.");
            _label->setVisible(true);
            _newGameSprite->setVisible(true);
            _replayGameSprite->setVisible(true);
            break;
        case OVER:
        case DECIDEWINNER:
            _ssSocket.ssshutdown();
            //_gameInfo.playerColor = packet.body.c_str()[0];
            if(_board._winner == _gameInfo.playerColor)
                changeState( WINGAME );
            else if(_board._winner != _gameInfo.playerColor)
                changeState( LOSEGAME );
            else
                changeState( UNDECIDEDGAME );
            break;
        case REPLAY:
            //DEBUG2("Replay state\n");
            break;
        default:
            assert(!"Unrecognized state!\n");
            DEBUG2("Unrecognized state!\n");
            break;
    }
    if(_somethingChanged){
        _somethingChanged = false;
        boardPopulate(_board);
    }
    
}

void GameLayer::registerWithTouchDispatcher()
{
	// CCTouchDispatcher::sharedDispatcher()->addTargetedDelegate(this,0,true);
    CCDirector::sharedDirector()->getTouchDispatcher()->addStandardDelegate(this,0);
}
