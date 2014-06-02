== iOs == 

For the xcode project I had to add the CocosDenshion and cocos2dx ios xcode projects to the BattleChess xcode project. Then added the header search paths $(SRCROOT)/../lib/cocos2dx/include and $(SRCROOT)/../lib/CocosDenshion/include 

then added the libraries libcocos2dx.a and libCocosDenshion.a from the workspace in the General tab->Linked Frameworks and Libraries section

