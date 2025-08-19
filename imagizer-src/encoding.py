#!/usr/bin/env python
# coding: utf-8
#
#******************************************************************************\
# * $Source$
# * $Id$
# *
# * Copyright (C) 2006 - 2010,  Jérôme Kieffer <kieffer@terre-adelie.org>
# * Conception : Jérôme KIEFFER, Mickael Profeta & Isabelle Letard
# * Licence GPL v2
# *
# * This program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; if not, write to the Free Software
# * Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# *
#*****************************************************************************/
"""
Utility function to convert string to ASCII
"""
from __future__ import with_statement, division, print_function, absolute_import
__author__ = "Jérôme Kieffer"
__date__ = "28/07/2019"
__copyright__ = "Jerome Kieffer"
__license__ = "GPLv3+"
__contact__ = "Jerome.Kieffer@terre-adelie.org"

import sys
PY3 = (sys.version_info[0] > 2)
if PY3:
    unicode = str
    def u(s):
        return s
else:
    bytes = str
    def u(s):
        return unicode(s, "unicode_escape")



LATIN_TO_ASCII = {0x99: 'oe',
                  0xc0:'A',
                  0xc1:'A',
                  0xc2:'A',
                  0xc3:'A',
                  0xc4:'A',
                  0xc5:'A',
                  0xc6:'AE',  # Æ
                  0xe6:'ae',  # æ
                  0xc7:'C',
                  0xc8:'E', 0xc9:'E', 0xca:'E', 0xcb:'E',
                  0xcc:'I', 0xcd:'I', 0xce:'I', 0xcf:'I',
                  0xd0:'Th',  # Ð
                  0xf0:'th',  # ð
                  0xde:'Th',  # Þ
                  0xfe:'th',  # þ
                  0xd1:'N',
                  0xd2:'O', 0xd3:'O', 0xd4:'O', 0xd5:'O', 0xd6:'O', 0xd8:'O',
                  0xd9:'U', 0xda:'U', 0xdb:'U', 0xdc:'U',
                  0xdd:'Y', 0xdf:'ss',
                  0xe0:'a', 0xe1:'a', 0xe2:'a', 0xe3:'a', 0xe4:'a', 0xe5:'a',
                  0xe7:'c',
                  0xe8:'e', 0xe9:'e', 0xea:'e', 0xeb:'e',
                  0xec:'i', 0xed:'i', 0xee:'i', 0xef:'i',
                  0xf1:'n',
                  0xf2:'o', 0xf3:'o', 0xf4:'o', 0xf5:'o', 0xf6:'o', 0xf8:'o',
                  0xf9:'u', 0xfa:'u', 0xfb:'u', 0xfc:'u',
                  0xfd:'y', 0xff:'y',
                  0xa1:'!', 0xa2:'{cent}', 0xa3:'{pound}', 0xa4:'{currency}',
                  0xa5:'{yen}', 0xa6:'|', 0xa7:'{section}', 0xa8:'{umlaut}',
                  0xa9:'{C}', 0xaa:'{^a}', 0xab:'<<', 0xac:'{not}',
                  0xad:'-', 0xae:'{R}', 0xaf:'_', 0xb0:'{degrees}',
                  0xb1:'{+/-}', 0xb2:'{^2}', 0xb3:'{^3}', 0xb4:"'",
                  0xb5:'{micro}', 0xb6:'{paragraph}', 0xb7:'*', 0xb8:'{cedilla}',
                  0xb9:'{^1}', 0xba:'{^o}', 0xbb:'>>',
                  0xbc:'{1/4}', 0xbd:'{1/2}', 0xbe:'{3/4}', 0xbf:'?',
                  0xd7:'*', 0xf7:'/',
                  0xe2:"'",
                 }
UNICODE_TO_ASCII = { u'\x99': 'oe',
                     u'\xa1': '!',
                     u'\xa2': '{cent}',
                     u'\xa3': '{pound}',
                     u'\xa4': '{currency}',
                     u'\xa5': '{yen}',
                     u'\xa6': '|',
                     u'\xa7': '{section}',
                     u'\xa8': '{umlaut}',
                     u'\xa9': '{C}',
                     u'\xaa': '{^a}',
                     u'\xab': '<<',
                     u'\xac': '{not}',
                     u'\xad': '-',
                     u'\xae': '{R}',
                     u'\xaf': '_',
                     u'\xb0': '{degrees}',
                     u'\xb1': '{+/-}',
                     u'\xb2': '{^2}',
                     u'\xb3': '{^3}',
                     u'\xb4': "'",
                     u'\xb5': '{micro}',
                     u'\xb6': '{paragraph}',
                     u'\xb7': '*',
                     u'\xb8': '{cedilla}',
                     u'\xb9': '{^1}',
                     u'\xba': '{^o}',
                     u'\xbb': '>>',
                     u'\xbc': '{1/4}',
                     u'\xbd': '{1/2}',
                     u'\xbe': '{3/4}',
                     u'\xbf': '?',
                     u'\xc0': 'A',
                     u'\xc1': 'A',
                     u'\xc2': 'A',
                     u'\xc3': 'A',
                     u'\xc4': 'A',
                     u'\xc5': 'A',
                     u'\xc6': 'AE',
                     u'\xc7': 'C',
                     u'\xc8': 'E',
                     u'\xc9': 'E',
                     u'\xca': 'E',
                     u'\xcb': 'E',
                     u'\xcc': 'I',
                     u'\xcd': 'I',
                     u'\xce': 'I',
                     u'\xcf': 'I',
                     u'\xd0': 'Th',
                     u'\xd1': 'N',
                     u'\xd2': 'O',
                     u'\xd3': 'O',
                     u'\xd4': 'O',
                     u'\xd5': 'O',
                     u'\xd6': 'O',
                     u'\xd7': '*',
                     u'\xd8': 'O',
                     u'\xd9': 'U',
                     u'\xda': 'U',
                     u'\xdb': 'U',
                     u'\xdc': 'U',
                     u'\xdd': 'Y',
                     u'\xde': 'Th',
                     u'\xdf': 'ss',
                     u'\xe0': 'a',
                     u'\xe1': 'a',
                     u'\xe2': "'",
                     u'\xe3': 'a',
                     u'\xe4': 'a',
                     u'\xe5': 'a',
                     u'\xe6': 'ae',
                     u'\xe7': 'c',
                     u'\xe8': 'e',
                     u'\xe9': 'e',
                     u'\xea': 'e',
                     u'\xeb': 'e',
                     u'\xec': 'i',
                     u'\xed': 'i',
                     u'\xee': 'i',
                     u'\xef': 'i',
                     u'\xf0': 'th',
                     u'\xf1': 'n',
                     u'\xf2': 'o',
                     u'\xf3': 'o',
                     u'\xf4': 'o',
                     u'\xf5': 'o',
                     u'\xf6': 'o',
                     u'\xf7': '/',
                     u'\xf8': 'o',
                     u'\xf9': 'u',
                     u'\xfa': 'u',
                     u'\xfb': 'u',
                     u'\xfc': 'u',
                     u'\xfd': 'y',
                     u'\xfe': 'th',
                     u'\xff': 'y',
                     u'\x99': 'oe',
                     u'\u2019': "'",
                     }

UNICODE_TO_HTML = { u('\u0022'): '&quot;',
                    u('\u0026'): '&amp;',
                    u('\u0027'): '&apos;',
                    u('\u003C'): '&lt;',
                    u('\u003E'): '&gt;',
                    u('\u00A0'): '&nbsp;',
                    u('\u00A1'): '&iexcl;',
                    u('\u00A2'): '&cent;',
                    u('\u00A3'): '&pound;',
                    u('\u00A4'): '&curren;',
                    u('\u00A5'): '&yen;',
                    u('\u00A6'): '&brvbar;',
                    u('\u00A7'): '&sect;',
                    u('\u00A8'): '&uml;',
                    u('\u00A9'): '&copy;',
                    u('\u00AA'): '&ordf;',
                    u('\u00AB'): '&laquo;',
                    u('\u00AC'): '&not;',
                    u('\u00AD'): '&shy;',
                    u('\u00AE'): '&reg;',
                    u('\u00AF'): '&macr;',
                    u('\u00B0'): '&deg;',
                    u('\u00B1'): '&plusmn;',
                    u('\u00B2'): '&sup2;',
                    u('\u00B3'): '&sup3;',
                    u('\u00B4'): '&acute;',
                    u('\u00B5'): '&micro;',
                    u('\u00B6'): '&para;',
                    u('\u00B7'): '&middot;',
                    u('\u00B8'): '&cedil;',
                    u('\u00B9'): '&sup1;',
                    u('\u00BA'): '&ordm;',
                    u('\u00BB'): '&raquo;',
                    u('\u00BC'): '&frac14;',
                    u('\u00BD'): '&frac12;',
                    u('\u00BE'): '&frac34;',
                    u('\u00BF'): '&iquest;',
                    u('\u00C0'): '&Agrave;',
                    u('\u00C1'): '&Aacute;',
                    u('\u00C2'): '&Acirc;',
                    u('\u00C3'): '&Atilde;',
                    u('\u00C4'): '&Auml;',
                    u('\u00C5'): '&Aring;',
                    u('\u00C6'): '&AElig;',
                    u('\u00C7'): '&Ccedil;',
                    u('\u00C8'): '&Egrave;',
                    u('\u00C9'): '&Eacute;',
                    u('\u00CA'): '&Ecirc;',
                    u('\u00CB'): '&Euml;',
                    u('\u00CC'): '&Igrave;',
                    u('\u00CD'): '&Iacute;',
                    u('\u00CE'): '&Icirc;',
                    u('\u00CF'): '&Iuml;',
                    u('\u00D0'): '&ETH;',
                    u('\u00D1'): '&Ntilde;',
                    u('\u00D2'): '&Ograve;',
                    u('\u00D3'): '&Oacute;',
                    u('\u00D4'): '&Ocirc;',
                    u('\u00D5'): '&Otilde;',
                    u('\u00D6'): '&Ouml;',
                    u('\u00D7'): '&times;',
                    u('\u00D8'): '&Oslash;',
                    u('\u00D9'): '&Ugrave;',
                    u('\u00DA'): '&Uacute;',
                    u('\u00DB'): '&Ucirc;',
                    u('\u00DC'): '&Uuml;',
                    u('\u00DD'): '&Yacute;',
                    u('\u00DE'): '&THORN;',
                    u('\u00DF'): '&szlig;',
                    u('\u00E0'): '&agrave;',
                    u('\u00E1'): '&aacute;',
                    u('\u00E2'): '&acirc;',
                    u('\u00E3'): '&atilde;',
                    u('\u00E4'): '&auml;',
                    u('\u00E5'): '&aring;',
                    u('\u00E6'): '&aelig;',
                    u('\u00E7'): '&ccedil;',
                    u('\u00E8'): '&egrave;',
                    u('\u00E9'): '&eacute;',
                    u('\u00EA'): '&ecirc;',
                    u('\u00EB'): '&euml;',
                    u('\u00EC'): '&igrave;',
                    u('\u00ED'): '&iacute;',
                    u('\u00EE'): '&icirc;',
                    u('\u00EF'): '&iuml;',
                    u('\u00F0'): '&eth;',
                    u('\u00F1'): '&ntilde;',
                    u('\u00F2'): '&ograve;',
                    u('\u00F3'): '&oacute;',
                    u('\u00F4'): '&ocirc;',
                    u('\u00F5'): '&otilde;',
                    u('\u00F6'): '&ouml;',
                    u('\u00F7'): '&divide;',
                    u('\u00F8'): '&oslash;',
                    u('\u00F9'): '&ugrave;',
                    u('\u00FA'): '&uacute;',
                    u('\u00FB'): '&ucirc;',
                    u('\u00FC'): '&uuml;',
                    u('\u00FD'): '&yacute;',
                    u('\u00FE'): '&thorn;',
                    u('\u00FF'): '&yuml;',
                    u('\u0152'): '&OElig;',
                    u('\u0153'): '&oelig;',
                    u('\u0160'): '&Scaron;',
                    u('\u0161'): '&scaron;',
                    u('\u0178'): '&Yuml;',
                    u('\u0192'): '&fnof;',
                    u('\u02C6'): '&circ;',
                    u('\u02DC'): '&tilde;',
                    u('\u0391'): '&Alpha;',
                    u('\u0392'): '&Beta;',
                    u('\u0393'): '&Gamma;',
                    u('\u0394'): '&Delta;',
                    u('\u0395'): '&Epsilon;',
                    u('\u0396'): '&Zeta;',
                    u('\u0397'): '&Eta;',
                    u('\u0398'): '&Theta;',
                    u('\u0399'): '&Iota;',
                    u('\u039A'): '&Kappa;',
                    u('\u039B'): '&Lambda;',
                    u('\u039C'): '&Mu;',
                    u('\u039D'): '&Nu;',
                    u('\u039E'): '&Xi;',
                    u('\u039F'): '&Omicron;',
                    u('\u03A0'): '&Pi;',
                    u('\u03A1'): '&Rho;',
                    u('\u03A3'): '&Sigma;',
                    u('\u03A4'): '&Tau;',
                    u('\u03A5'): '&Upsilon;',
                    u('\u03A6'): '&Phi;',
                    u('\u03A7'): '&Chi;',
                    u('\u03A8'): '&Psi;',
                    u('\u03A9'): '&Omega;',
                    u('\u03B1'): '&alpha;',
                    u('\u03B2'): '&beta;',
                    u('\u03B3'): '&gamma;',
                    u('\u03B4'): '&delta;',
                    u('\u03B5'): '&epsilon;',
                    u('\u03B6'): '&zeta;',
                    u('\u03B7'): '&eta;',
                    u('\u03B8'): '&theta;',
                    u('\u03B9'): '&iota;',
                    u('\u03BA'): '&kappa;',
                    u('\u03BB'): '&lambda;',
                    u('\u03BC'): '&mu;',
                    u('\u03BD'): '&nu;',
                    u('\u03BE'): '&xi;',
                    u('\u03BF'): '&omicron;',
                    u('\u03C0'): '&pi;',
                    u('\u03C1'): '&rho;',
                    u('\u03C2'): '&sigmaf;',
                    u('\u03C3'): '&sigma;',
                    u('\u03C4'): '&tau;',
                    u('\u03C5'): '&upsilon;',
                    u('\u03C6'): '&phi;',
                    u('\u03C7'): '&chi;',
                    u('\u03C8'): '&psi;',
                    u('\u03C9'): '&omega;',
                    u('\u03D1'): '&thetasym;',
                    u('\u03D2'): '&upsih;',
                    u('\u03D6'): '&piv;',
                    u('\u2002'): '&ensp;',
                    u('\u2003'): '&emsp;',
                    u('\u2009'): '&thinsp;',
                    u('\u200C'): '&zwnj;',
                    u('\u200D'): '&zwj;',
                    u('\u200E'): '&lrm;',
                    u('\u200F'): '&rlm;',
                    u('\u2013'): '&ndash;',
                    u('\u2014'): '&mdash;',
                    u('\u2018'): '&lsquo;',
                    u('\u2019'): '&rsquo;',
                    u('\u201A'): '&sbquo;',
                    u('\u201C'): '&ldquo;',
                    u('\u201D'): '&rdquo;',
                    u('\u201E'): '&bdquo;',
                    u('\u2020'): '&dagger;',
                    u('\u2021'): '&Dagger;',
                    u('\u2022'): '&bull;',
                    u('\u2026'): '&hellip;',
                    u('\u2030'): '&permil;',
                    u('\u2032'): '&prime;',
                    u('\u2033'): '&Prime;',
                    u('\u2039'): '&lsaquo;',
                    u('\u203A'): '&rsaquo;',
                    u('\u203E'): '&oline;',
                    u('\u2044'): '&frasl;',
                    u('\u20AC'): '&euro;',
                    u('\u2111'): '&image;',
                    u('\u2118'): '&weierp;',
                    u('\u211C'): '&real;',
                    u('\u2122'): '&trade;',
                    u('\u2135'): '&alefsym;',
                    u('\u2190'): '&larr;',
                    u('\u2191'): '&uarr;',
                    u('\u2192'): '&rarr;',
                    u('\u2193'): '&darr;',
                    u('\u2194'): '&harr;',
                    u('\u21B5'): '&crarr;',
                    u('\u21D0'): '&lArr;',
                    u('\u21D1'): '&uArr;',
                    u('\u21D2'): '&rArr;',
                    u('\u21D3'): '&dArr;',
                    u('\u21D4'): '&hArr;',
                    u('\u2200'): '&forall;',
                    u('\u2202'): '&part;',
                    u('\u2203'): '&exist;',
                    u('\u2205'): '&empty;',
                    u('\u2207'): '&nabla;',
                    u('\u2208'): '&isin;',
                    u('\u2209'): '&notin;',
                    u('\u220B'): '&ni;',
                    u('\u220F'): '&prod;',
                    u('\u2211'): '&sum;',
                    u('\u2212'): '&minus;',
                    u('\u2217'): '&lowast;',
                    u('\u221A'): '&radic;',
                    u('\u221D'): '&prop;',
                    u('\u221E'): '&infin;',
                    u('\u2220'): '&ang;',
                    u('\u2227'): '&and;',
                    u('\u2228'): '&or;',
                    u('\u2229'): '&cap;',
                    u('\u222A'): '&cup;',
                    u('\u222B'): '&int;',
                    u('\u2234'): '&there4;',
                    u('\u223C'): '&sim;',
                    u('\u2245'): '&cong;',
                    u('\u2248'): '&asymp;',
                    u('\u2260'): '&ne;',
                    u('\u2261'): '&equiv;',
                    u('\u2264'): '&le;',
                    u('\u2265'): '&ge;',
                    u('\u2282'): '&sub;',
                    u('\u2283'): '&sup;',
                    u('\u2284'): '&nsub;',
                    u('\u2286'): '&sube;',
                    u('\u2287'): '&supe;',
                    u('\u2295'): '&oplus;',
                    u('\u2297'): '&otimes;',
                    u('\u22A5'): '&perp;',
                    u('\u22C5'): '&sdot;',
                    u('\u2308'): '&lceil;',
                    u('\u2309'): '&rceil;',
                    u('\u230A'): '&lfloor;',
                    u('\u230B'): '&rfloor;',
                    u('\u27E8'): '&lang;',
                    u('\u27E9'): '&rang;',
                    u('\u25CA'): '&loz;',
                    u('\u2660'): '&spades;',
                    u('\u2663'): '&clubs;',
                    u('\u2665'): '&hearts;',
                    u('\u2666'): '&diams;',
                    }

def unicode2ascii(unicrap):
    """
    This takes a UNICODE string and replaces unicode characters with
    something equivalent in 7-bit ASCII. It returns a plain ASCII string.
    This function makes a best effort to convert unicode characters into
    ASCII equivalents. It does not just strip out the Latin-1 characters.
    All characters in the standard 7-bit ASCII range are preserved.
    In the 8th bit range all the Latin-1 accented letters are converted
    to unaccented equivalents. Most symbol characters are converted to
    something meaningful. Anything not converted is deleted.
    """
    str_out = ""
    if PY3:
        if isinstance(unicrap, bytes):
            byte_crap = unicrap
        else:
            byte_crap = unicrap.encode("latin-1")
        for i in byte_crap:
            if i in LATIN_TO_ASCII:
                str_out += LATIN_TO_ASCII[i]
            elif i >= 0x80:
                pass
            else:
                str_out += chr(i)

    else:  # Python2
        if isinstance(unicrap, unicode):
            str_out = "".join(UNICODE_TO_ASCII.get(i, "")  if ord(i) > 128 else i for i in unicrap)
        else:
            byte_crap = unicrap
            for i in byte_crap:
                ordi = ord(i)
                if ordi in LATIN_TO_ASCII:
                    str_out += LATIN_TO_ASCII[ordi]
                elif ordi >= 0x80:
                    pass
                else:
                    str_out += str(i)
    return str_out


def unicode2html(unicrap):
    """
    Converts an unicode input into a "html" like string

    @param unicrap: input unicode
    @return: html string
    """
    strout = ""
    if unicrap is not None:
        if not isinstance(unicrap, unicode):
            unicrap = unicrap.decode("utf-8")
        strout = "".join(UNICODE_TO_HTML[i] if i in UNICODE_TO_HTML else str(i) for i in unicrap)
    return strout

def test():
    if PY3:
        inp = 'Jérôme'
    else:
        inp = 'Jérôme'.decode("utf8")

    assert unicode2ascii(inp) == "Jerome"
    assert unicode2html(inp) == 'J&eacute;r&ocirc;me'

if __name__ == "__main__":
    test()
