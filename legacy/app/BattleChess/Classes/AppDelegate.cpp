#include "AppDelegate.h"
#include "GameLayerScene.h"
#include "IntroScene.h"

USING_NS_CC;

AppDelegate::AppDelegate() {

}

AppDelegate::~AppDelegate() 
{
    CCLog("AppDelegate destructor");
}

bool AppDelegate::applicationDidFinishLaunching() {
    // initialize director
    CCDirector *pDirector = CCDirector::sharedDirector();
    
    pDirector->setOpenGLView(CCEGLView::sharedOpenGLView());
    
    CCSize screenSize = CCEGLView::sharedOpenGLView()->getFrameSize();

    //default
    //CCSize designSize = CCSizeMake(480, 320);
    CCSize designSize = CCSizeMake(450, 680);
    
    std::vector<std::string> searchPaths;
    
    //TODO create the different image resolutions
    if (screenSize.height > designSize.height)
    {
    	CCLOG("using high res sd");
        searchPaths.push_back("hd");
        searchPaths.push_back("sd");
        pDirector->setContentScaleFactor(designSize.height/640.0f);

    }
    else
    {
    	CCLOG("using low res sd");
        searchPaths.push_back("sd");
        pDirector->setContentScaleFactor(designSize.height/640.0f);
    }
    
    CCLOG("screen size %f x %f", screenSize.width, screenSize.height);

    CCFileUtils::sharedFileUtils()->setSearchPaths(searchPaths);
    
#if (CC_TARGET_PLATFORM == CC_PLATFORM_WINRT) || (CC_TARGET_PLATFORM == CC_PLATFORM_WP8)
    CCEGLView::sharedOpenGLView()->setDesignResolutionSize(designSize.width, designSize.height, kResolutionShowAll);
#else
	CCEGLView::sharedOpenGLView()->setDesignResolutionSize(designSize.width, designSize.height, kResolutionShowAll);
#endif

    // turn on display FPS
    pDirector->setDisplayStats(false);

    // set FPS. the default value is 1.0/60 if you don't call this
    pDirector->setAnimationInterval(1.0 / 40);

    CCScene *pScene;
    
    if(cocos2d::CCUserDefault::sharedUserDefault()->getStringForKey("username") == "") {
        //create a scene. it's an autorelease object
        pScene = IntroScene::create();
    } else {
        pScene = GameLayer::scene();
    }
    // run
    pDirector->runWithScene(pScene);

    return true;
}

// This function will be called when the app is inactive. When comes a phone call,it's be invoked too
void AppDelegate::applicationDidEnterBackground() {
    CCDirector::sharedDirector()->stopAnimation();

    // if you use SimpleAudioEngine, it must be pause
    // CocosDenshion::SimpleAudioEngine::sharedEngine()->pauseBackgroundMusic();
}

// this function will be called when the app is active again
void AppDelegate::applicationWillEnterForeground() {
    CCDirector::sharedDirector()->startAnimation();

    // if you use SimpleAudioEngine, it must resume here
    // CocosDenshion::SimpleAudioEngine::sharedEngine()->resumeBackgroundMusic();
}
