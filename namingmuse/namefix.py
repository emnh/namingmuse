"""
Provides a function for prettifying a string according to the tast of the namingmuse developers. We don't like ugly file names, so we run every filename trough this function and this functio is in charge of un-uglify them.

Example: MOBY_--_01_-_honEY.MP3
Becomes: Moby - 01 - Honey.mp3

"""
import os
import re
import sys

def namefix(filename):
    ''' Tries to prettify a MP3 filename '''

    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    def wordcap(matchobj, words = []):
        '''Fix capitalization of words.'''
        abbreviations = ("CD", "DJ")
        lcaseword = ("for", "and", "a", "as", "at", "it", "the",
                     "in", "of", "into", "from", "or", "us", 
                     "are", "to", "be", "your")
        word = matchobj.group(1)
        tail = matchobj.group(2)
        tailword = re.search("\w+\s+$", "".join(words))
        if word.upper() in abbreviations:
            word = word.upper()
        elif word.lower() in lcaseword and tailword:
            word = word.lower()
        else:
            word = word.capitalize()
        if tail.strip() == "":
            firstword = False
        words.append(word)
        words.append(tail)
        return word + tail

    regexes = {
        "%20":            " ",         #replace %20 with space
        "^\W*":           "",          #remove non-alnum starting chars
        " *- *":          " - ",       #surround dash with spaces
        " *& *":          " & ",       #surround ampersand with spaces
        "^\s+":           "",          #trim left space
        "\s+$":           "",          #trim right space
        "-*$":            "",          #remove trailing dashes
        "\s+":            " ",         #remove duplicate spaces

        "(\w+)(\W*)":     wordcap,     #capitalize first char in each word

        " -\s*(- )+":        " - ",    #no double dashes
        "- (\d\d) - ":    "- \\1 /",   #no dash after track numbers
        #"(\d\d)([A-Z])"$1 $2/;        #space after track numbers
        #s/[- ]*(\.|$)"$1/g;           #kill off inappropriate ending chars
        "\/":             "(",
        "\[":             "(",
        "\{":             "(",         #translate [,{ to ()
        "\]":             ")",
        "\}":             ")",
        "\.":             " ",         #replace dot and underscore with space
        "_":              " ",
        "\(\)":           "",          #kill empty parantheses
        "^([^(]*)\)":     "\\1",       #kill stray right parantheses
        "\(([^)]*)$":     "\\1",       #kill stray right parantheses
        "\d{3}\s*kbps(\s*\+)?":"",     #erase bitrate info in filename
        "\((\d+)\)":      "\\1",       #no paranthesized numbers
        " Dont ":         " Don't ",   #spelling error
        "(.*-.*) - (Bke|Bmi|Bpm|Chr|Cmg|Cms|CSR|Csr|Dmg|Dps|Ego|ENT|Esc|Fnt|Fsp|Fua|Hcu|Idx|Its|Jce|Ksi|LLF|Mod|Nbd|OSi|PMS|Pms|Rev|Rns|Sdc|Sdr|Ser|Sms|Ssr|Sur|Sut|TiS|Twc|Wcr|Wlm)":    "\\.\\1\\."   #mp3 gang advertisements
        }

    oldname = "" 
    while oldname != name:
        oldname = name
        for regex in regexes.keys():
            #print "reggie:",regex
            name = re.sub(regex,regexes[regex],name)
        
    #([A-Z])\.(?![^A-Z])/$1/gx;     #R.E.M -> REM
#    
#    if ($nametype == $type_dir) {
#            #s/^The([^-]*)$/$1, The/;
#            s/(\d+) - (\d+)/$1-$2/;  #allow unspaced dash for numeric ranges
#
#            s/\(*(\d{4})\)*/$1/g;  #release year should not be paranthesized
#            if (!/\d{4}.*\d{4}/) { #don't mess if more than one year in filename
#                    #s/^(.*)[ -]+([12][09]\d{2})(\s|$)/$2 $1 $3/g;  #and it should be first
#                    ;
#            }
#    }

    filename = name + ext
    return filename

if __name__ == '__main__':
    for i in sys.argv[1:]:
        print namefix(i)
