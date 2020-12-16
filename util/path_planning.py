import utils
import re
import nlp_util
import nltk
import math
import string
from quantulum3 import parser


def preprocess(text):
    """ 
    Returns the same text, with all numbers converted from English words to 
    decimal form. 
    Ex. "move five feet forward" returns "move 5 feet forward"

    @param text: the original text (must be in lowercase)
    """
    text = text.translate(str.maketrans('', '', string.punctuation))
    quant = parser.parse(text)
    for q in quant:
        words = str(q).split(' ')
        number_word = words[0]
        number = int(q.value)
        text = text.replace(number_word, str(number))
    lst = text.split(' ', 1)
    text = text if len(lst) <= 1 else lst[1]
    print(text)
    r_expr2 = r"""
    DirectionFirst: {(((<TO|IN>)<DT>)?<RB|VBD|JJ|VBP|NN|VBN><CD><NNS|NN>?)}
    NumberFirst: {(<CD><NNS|NN>?((<TO|IN>)<DT>)?<RB|VBD|JJ|VBP|NN|VBN>)}
    """
    target_verbs = ["move", "spin", "rotate",
                    "turn", "go", "drive", "stop", "travel"]
    target_words = ["degrees", "left", "right", "forward", "backward",
                    "clockwise", "counterclockwise"]

    locPhrase, keywords = nlp_util.match_regex_and_keywords(
        text, r_expr2, target_words)

    return locPhrase, keywords


def isLocCommand(text):
    '''
    Determines whether a string is a locomation command or not based on the
    sentence structure. A proper locomotion command includes what part to move,
    how much to move it, and the direction to move it. Without these three, the
    command will not be parsed. Some examples are "Move the body forward 10 steps"
    or "Rotate the precision arm left by 10 degrees"

    @param text: The sentence to check (must be in lowercase)
    @return: A boolean. True indicates that the input is a locomotion command
    '''
    # r_expr = r"""
    # VP: {(<JJ>)?<NN.*>+(<VB.*>)?<RB|VBD|JJ|CD>(<CD|JJ>)?}
    # """

    if text == "stop":
        return True

    locPhrase, keywords = preprocess(text)
    # print(locPhrase)

    target_verbs = ["move", "spin", "rotate",
                    "turn", "go", "drive", "stop", "travel"]
    for verb in target_verbs:
        if verb in text and len(locPhrase) > 0:
            return True
    return False


def get_loc_params(phrase):
    string = " ".join([word[0] for word in phrase])
    quant = parser.parse(string)[0]
    unit = quant.unit.name
    number = quant.value
    if phrase.label() == "NumberFirst":
        direction = phrase[-1][0]
    else:
        if unit == "dimensionless":
            direction = phrase[-2][0]
        else:
            direction = phrase[-3][0]
    return int(number), unit, direction


def process_loc(text):

    mode = 0  # 0 for garbage, 1 for turn, 2 for move

    locPhrase, keywords = preprocess(text)

    tagged_list = nltk.pos_tag(nltk.word_tokenize(text))
    verbs_and_nouns = [tup[0]
                       for tup in tagged_list if tup[1] == 'NN' or tup[1] == 'VB' or tup[1] == 'VBP']
    # DEBUG THISSSS
    words = nltk.word_tokenize(text)

    for verb in verbs_and_nouns:
        if verb == "stop":
            return ("stop", 0)
        elif verb in ["turn", "spin", "rotate"]:
            mode = 1
            break
        elif verb in ["move", "go", "drive", "travel"]:
            mode = 2
            break
    # print(locPhrase)
    if mode == 1:
        number, unit, direction = get_loc_params(locPhrase[0])
        if unit == "radian":
            number = number * 180 / math.pi
        if direction == "left" or direction == "counterclockwise":
            number = -1 * number
        return ("turn", number)
    if mode == 2:
        if len(locPhrase) > 1:
            x = 0
            y = 0
            prev_unit = None
            for phrase in locPhrase:
                number, unit, direction = get_loc_params(phrase)
                # if the unit isn't provided, assume it's the same
                # as the previous unit - if that's unspecified, assume meters
                if unit == "dimensionless":
                    if prev_unit:
                        unit = prev_unit
                    else:
                        unit = "metre"
                        prev_unit = "unit"
                else:
                    prev_unit = unit
                if unit == "foot":
                    number = number * 0.3048
                if direction == "forward":
                    y += number
                elif direction == "left":
                    x -= number
                elif direction == "right":
                    x += number
                elif direction == "backward":
                    y -= number
            return (float(round(x, 2)), float(round(y, 2)))
        elif len(locPhrase) > 0:
            number, unit, direction = get_loc_params(locPhrase[0])
            if unit == "foot":
                number = number * 0.3048
            number = float(round(number, 2))
            if direction == "forward":
                return ("move forward", number)
            elif direction == "left":
                return (-number, 0.0)
            elif direction == "right":
                return (number, 0.0)
            elif direction == "backward":
                return (0.0, -number)
            else:
                return ("unknown", 0)

        # 2. check if turn --> movement
        # 3. check if moving
        # a. check if 2 command --> coordinate
        # b. check if 1 command
        # i. check if forward --> movement
        # ii. check if other dir --> coordinate

    return "Not processed"


def pathPlanning(text):
    '''
    This function uses regular expressions to determine whether the input is
    a locomotion command and uses regular expressions to parse the necessary
    data from the inputed text.

    @param text: The sentence to check if it is a locomotion command and
    parse the direction and distance from it. ***MUST BE IN LOWERCASE***
    @return: A triple. The first element is the body part to move.  Second
    element is the direction (i.e. 90 if right, 0 if forward, -90 if left, or
    180 of backwards). The Third element is the
    distance. If the input text is not a locomation command, the function returns
    ("", -500, -500) by default.
    '''
    # return variables
    direction = -500
    moveAmmount = -500
    itemMove = ""
    target_directions = ["forward", "backward", "left",
                         "right", "up", "down", "forwards", "backwards"]
    target_movements = ["strong arm", "precision arm", "body", "C1C0", "head", "cico",
                        "c1c0", "kiko", "strongarm", "precisionarm", "strong-arm", "precision-arm"]
    # if we find a path related phrase
    if isLocCommand(text):
        ammountE = r"""
        RB: {<CD>}
        """
        # grabs the number of steps from the phrase
        movePhrase, keyword = nlp_util.match_regex_and_keywords(text, ammountE)
        firstItem = movePhrase[0]
        temp = firstItem[0]
        moveAmmount = temp[0]
        for item in target_movements:
            if item in text:
                itemMove = item
        # based on the direction, returns the corresponding degrees
        if "left" in text:
            direction = -90
        if "right" in text:
            direction = 90
        if "forward" in text or "up" in text:
            direction = 0
        if "backward" in text or "down" in text:
            direction = 180

    return(itemMove, direction, moveAmmount)


if __name__ == "__main__":
    with open("tests/path_planning_phrases.txt") as f:
        for line in f:
            if line[0] != "#":
                is_command = isLocCommand(line)
                if is_command:
                    print("{} \t {} \t {}".format(
                        line, is_command, process_loc(line)))
                else:
                    print("{} \t {}".format(line, is_command))
