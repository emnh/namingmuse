#!/usr/bin/python
import sys,re,os

def namefix(filename):
    ''' Tries to prettify a MP3 filename '''

    name, ext = os.path.splitext(filename)
    ext = ext.lower()
    name = re.escape(name)
    print "name:",name


    regexes = {
        "%20":            " ",         #replace %20 with space
        "^[^[:alnum:]]*": "",          #remove non-alnum starting chars
        "warez":          "",          #unwanted words
        " *- *":          " - ",       #surround dash with spaces
        " *& *":          " & ",       #surround ampersand with spaces
        "^\s+":           "",          #trim left space
        "\s+$":           "",          #trim right space
        "-*$":            "",          #remove trailing dashes
        "\s+":            "",          #remove duplicate spaces
        "\s*\.\s*":       "",          #no spaces surrounding extension dot
        #"(\..*)$/\L$1/g;              #lowercase extension
        #"(^|\s|\()(\w+)"\u$1\u$2/g;   #capitalize first char in each word
        " -.- ":          " - ",       #no double dashes
        #"- (\d\d) - ":"- $1 /;        #no dash after track numbers
        #"(\d\d)([A-Z])"$1 $2/;        #space after track numbers
        #s/[- ]*(\.|$)"$1/g;           #kill off inappropriate ending chars
        #tr/[{/(/;                     #translate [,{ to ()
        #tr/]}/)/;                     #translate },] to ()
        "\(\)":           "",          #kill empty parantheses
        #s/^([^(]*)\)/$1/g;            #kill stray right parantheses
        #s/\(([^)]*)$/$1/g;            #kill stray right parantheses
        "\d{3}kbps":      "",          #erase bitrate info in filename
        #s/\((\d\d)\)/$1/;             #no paranthesized track numbers
        #"(for|and|a|as|at|it|the|in|of|into|from|or|us|are|to|be|your)":/ \l$1 /i; #decapitalize short common words
        "/":              "",
        }

    for regex in regexes.keys():
        #print "reggie:",regex
        name = re.sub(regex,regexes[regex],name)

    name = re.sub("\\\\","",name)
    
    #([A-Z])\.(?![^A-Z])/$1/gx;     #R.E.M -> REM
    ##if ($nametype == $type_file) {
    #        $lastdot = rindex($_, '.');    #save position of extension dot
    #} else {
    #        $lastdot = 0;
    #}
    #tr/._/ /;                        #replace dot and underscore with space
    #if ($lastdot > 0) { 
    #        substr($_, $lastdot, 1) = '.'; #restore extension dot
    #} 
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
#    
    #mp3 gang advertisements
#    s/(.*-.*) - (Bke|Bmi|Bpm|Chr|Cmg|Cms|CSR|Csr|Dmg|Dps|Ego|ENT|Esc|Fnt|Fsp|Fua|Hcu|Idx|Its|Jce|Ksi|LLF|Mod|Nbd|OSi|PMS|Pms|Rev|Rns|Sdc|Sdr|Ser|Sms|Ssr|Sur|Sut|TiS|Twc|Wcr|Wlm)\./$1./;
#
#    #some case fixing stuff
#    s/(^|\s)(Cd|Dj)(\s|\.|$)/$1\U$2$3/;      #uppercase words like CD, DJ
#    no locale;
#    return $_;
    filename = name + ext
    return filename

if __name__ == '__main__':
    for i in sys.argv[1:]:
        print namefix(i)
