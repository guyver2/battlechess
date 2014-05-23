#include "GameLayerScene.h"
#include "GameOverScene.h"
#include "SimpleAudioEngine.h"
#include "WaitingOpponentScene.h"

using namespace cocos2d;
using namespace std;

const char *state_str[]={ "CONNECT",
    "GETNICK",
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
    "RECONNECT" };

GameLayer::GameLayer() : _state(GETNICK), _somethingChanged(true)
{
	CCLog("GameLayer Contructor...");


}

GameLayer::~GameLayer()
{
    
    delete _textInfoNode;
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
		//////////////////////////////////////////////////////////////////////////
		// super init first
		//////////////////////////////////////////////////////////////////////////

		CC_BREAK_IF(! CCLayerColor::initWithColor( ccc4(255,255,255,255) ) );

		//////////////////////////////////////////////////////////////////////////
		// add your codes below...
		/////////////////

        //TODO does this go here?
        _screenSize = CCDirector::sharedDirector()->getVisibleSize();
        
		// 1. Add a menu item with "X" image, which is clicked to quit the program.

		// Create a "close" menu item with close icon, it's an auto release object.
		CCMenuItemImage *pCloseItem = CCMenuItemImage::create(
			"CloseNormal.png",
			"CloseSelected.png",
			this,
			menu_selector(GameLayer::menuCloseCallback));
		CC_BREAK_IF(! pCloseItem);
        
		// Place the menu item bottom-right conner.
        CCPoint origin = CCDirector::sharedDirector()->getVisibleOrigin();
        
		pCloseItem->setPosition(ccp(origin.x + _screenSize.width - pCloseItem->getContentSize().width/2,
                                    origin.y + pCloseItem->getContentSize().height/2));

		// Create a menu with the "close" menu item, it's an auto release object.
		CCMenu* pMenu = CCMenu::create(pCloseItem, NULL);
		pMenu->setPosition(CCPointZero);
		CC_BREAK_IF(! pMenu);

		// Add the menu to GameLayer layer as a child layer.
		this->addChild(pMenu, 1);

        _tmpTextInfoNode = new cocos2d::CCNode();

        _textInfoNode = new cocos2d::CCNode();
        
        _turnLabel = CCLabelTTF::create("","Artial", 10);
        _turnLabel->setColor( ccc3(255, 255, 255) );
        _turnLabel->setPosition( board2screen(-2,-2) );
        _turnLabel->setAnchorPoint(ccp(0,1));
        _textInfoNode->addChild(_turnLabel);
        this->addChild(_textInfoNode);
        
        createBoard();
        
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
    this->addChild(_gameBatchNode);

    _boardSprite = CCSprite::createWithSpriteFrameName("board.png");
    _squaresize = _boardSprite->boundingBox().size.height/8;
    DEBUG2("board size %f so squaresize %d", _boardSprite->boundingBox().size.height, _squaresize);
/*
    sprite->setPosition(ccp(_screenSize.width * 0.5f, _screenSize.height * 0.5f));
    _gameBatchNode->addChild(sprite, Board::kBoard);
    
    for(int j=0; j<8; j++){
        for(int i=0; i<8; i++){
            float color = 1.0f;
            if((i+j)%2)
                color = 0.0f;
            string piece = _board._board[i][j];
            if(piece == "")
                continue;
            sprite = CCSprite::createWithSpriteFrameName(piece.c_str());
            sprite->setAnchorPoint(ccp(0,1));
            //TODO use relative positions and a trimmed board
            sprite->setPosition(board2screen(i,j));
            _gameBatchNode->addChild(sprite, Board::kPieces);
        }
    }
 */
    //todo MAYBE remove all children destroys the sprite //indeed
    boardPopulate(_board);

}

void GameLayer::boardPopulate(const Board& board){
    
    //FIXME maybe we can move sprites instead of destroying and recreating (deal with pawn promotion thought)
    _gameBatchNode->removeAllChildrenWithCleanup(true);
    
    _boardSprite = CCSprite::createWithSpriteFrameName("board.png");
    _boardSprite->setPosition(ccp(_screenSize.width * 0.5f, _screenSize.height * 0.5f));
    _gameBatchNode->addChild(_boardSprite, Board::kBoard);

    CCSprite * sprite;
    
    CCPoint pieceAnchorPoint = ccp(0,1);

    int takenW = 0;
    int takenB = 0;
    for(int i=0; i< _board._taken.size(); i++){
        std::string piece = _board._taken[i] + ".png";
        sprite = CCSprite::createWithSpriteFrameName(piece.c_str());
        sprite->setAnchorPoint(pieceAnchorPoint);
        if(piece.c_str()[1] == 'w'){
            sprite->setPosition(board2screen(takenW/2, -2 + takenW%2));
            takenW++;
        }else{
            sprite->setPosition(board2screen(7 - takenB/2, 8 + takenB%2));
            takenB++;
        }
        _gameBatchNode->addChild(sprite, Board::kPieces);
    }

    for(int j=0; j<8; j++){
        for(int i=0; i<8; i++){
            if(board.foggy(i,j,_gameInfo.playerColor)){
                sprite = CCSprite::createWithSpriteFrameName("blank.png");
                sprite->setAnchorPoint(pieceAnchorPoint);
                sprite->setPosition(board2screen(i,j));
                sprite->setOpacity(200);
                sprite->setColor(ccc3(0,0,0));
                _gameBatchNode->addChild(sprite, Board::kBoard);
            }else{
                string piece = board._board[i][j];
                if(piece == "")
                    continue;
                piece +=  + ".png";
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

    _textInfoNode->removeAllChildrenWithCleanup(true);
    //FIXME move the game info to somewhere else
    if(_state == MYTURN) {
        if(_gameInfo.playerColor == 'w')
            _turnLabel = CCLabelTTF::create(GameInfo::WHITE.c_str(),"Artial", 10);
        else
            _turnLabel = CCLabelTTF::create(GameInfo::BLACK.c_str(),"Artial", 10);

    }else if(_state == HISTURN) {
        if(_gameInfo.playerColor == 'w')
            _turnLabel = CCLabelTTF::create(GameInfo::BLACK.c_str(),"Artial", 10);
        else
            _turnLabel = CCLabelTTF::create(GameInfo::WHITE.c_str(),"Artial", 10);
    }else{
        _turnLabel = CCLabelTTF::create("","Artial", 10);
    }
    
    _turnLabel->setColor( ccc3(0, 0, 0) );
    _turnLabel->setPosition( board2screen(-1,0) );
    _turnLabel->setAnchorPoint(ccp(0,1));
    _textInfoNode->addChild(_turnLabel);
}

void GameLayer::menuCloseCallback(CCObject* pSender)
{
	// "close" menu item clicked
#if (CC_TARGET_PLATFORM == CC_PLATFORM_WINRT) || (CC_TARGET_PLATFORM == CC_PLATFORM_WP8)
    CCMessageBox("You pressed the close button. Windows Store Apps do not implement a close button.", "Alert");
#else
    CCDirector::sharedDirector()->end();
#endif
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
                    _board.setSelectedOrigin(i,j);
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
                    _board.setSelectedOrigin(i,j);
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
        case GETNICK:
            //todo fetch username through app use another scene
            changeState( CONNECT );
            break;
        case RECONNECT:
            //TODO connection was lost
            break;
        case CONNECT:
        	CCLog("about to connect");
            if(_ssSocket.ssconnect() >= 0){
            	CCLog("Connected starting thread...");
                _ssSocket.start();
                changeState( GETCOLOR );
            	//CCLog("Going to state GETCOLOR...");
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
                if(packet.body == GameInfo::WHITE)
                    _gameInfo.playerColor = 'w';
                else
                    _gameInfo.playerColor = 'b';

                //CCLog("Going to state SENDNICK...");
                changeState( SENDNICK );
            }
            break;
        case SENDNICK:
            {
                _gameInfo.playerName = "test";
                packet = Packet(std::string("NICK"),_gameInfo.playerName);
                _ssSocket.sendPacket(packet);

                //draw the waiting opponent scene
                DEBUG2("Waiting opponent...");
                CCSize winSize = CCDirector::sharedDirector()->getWinSize();
                _label = CCLabelTTF::create("Waiting Opponent...","Artial", 32);
                _label->setColor( ccc3(255, 0, 0) );
                _label->setPosition( ccp(winSize.width/2, winSize.height/2) );
                _tmpTextInfoNode->addChild(_label);
                this->addChild(_tmpTextInfoNode);
            	//CCLog("Going to state GETURL...");
                changeState( GETURL );
            }
            break;
        case GETURL:
            if(_ssSocket.getPacket(packet)){
                //FIXME handle waiting oponent through a scene
                _tmpTextInfoNode->removeAllChildrenWithCleanup(true);
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
                _textInfoNode->removeAllChildrenWithCleanup(true);
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
                //CCLog("Going to state MYTURN/HISTURN...");
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
            {
                WaitingOpponentScene *waitingOpponentScene = WaitingOpponentScene::create();
                waitingOpponentScene->getLayer()->getLabel()->setString("You Won. Waiting Opponent...");
                CCDirector::sharedDirector()->replaceScene(waitingOpponentScene);
                break;
            }
        case LOSEGAME:
            {
                WaitingOpponentScene *waitingOpponentScene = WaitingOpponentScene::create();
                waitingOpponentScene->getLayer()->getLabel()->setString("You Lost. Waiting Opponent...");
                CCDirector::sharedDirector()->replaceScene(waitingOpponentScene);
                break;
            }
        case UNDECIDEDGAME:
        {
            WaitingOpponentScene *waitingOpponentScene = WaitingOpponentScene::create();
            waitingOpponentScene->getLayer()->getLabel()->setString("Undecided game. Waiting Opponent...");
            CCDirector::sharedDirector()->replaceScene(waitingOpponentScene);
            break;
        }
        case OVER:
        case DECIDEWINNER:
            //already done by himself
            _ssSocket._terminate = true;
            //_gameInfo.playerColor = packet.body.c_str()[0];
            if(_board._winner == _gameInfo.playerColor)
                changeState( WINGAME );
            else if(_board._winner != _gameInfo.playerColor)
                changeState( LOSEGAME );
            else
                changeState( UNDECIDEDGAME );
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
