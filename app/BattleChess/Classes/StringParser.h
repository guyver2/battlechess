//
//  stringparser.h
//  SimpleGame
//
//  Created by Pol Monso-Purti on 5/16/14.
//
//

#ifndef SimpleGame_StringParser_h
#define SimpleGame_StringParser_h

class StringParser {
public:
static std::vector<std::string> &split(const std::string &s, char delim, std::vector<std::string> &elems) {
    std::stringstream ss(s);
    std::string item;
    while (std::getline(ss, item, delim)) {
        elems.push_back(item);
    }
    return elems;
}

static std::vector<std::string> split(const std::string &s, char delim) {
    std::vector<std::string> elems;
    split(s, delim, elems);
    return elems;
}
};

#endif
