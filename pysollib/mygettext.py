import gettext


class myLocalGettext:
    def __init__(self, lang):
        self.language = lang

    def translation(self):
        domain = gettext._current_domain
        localedir = gettext._localedirs.get(domain, None)
        if self.language == "":
            t = gettext.translation(domain, localedir)
        else:
            t = gettext.translation(
                domain, localedir, languages=[self.language])
        return t

    def maketext(self, msg):
        if not isinstance(msg, str):
            return str(msg, 'utf-8')
        return msg

    def ungettext(self, msgid1, msgid2, n):
        # unicoded ngettext
        msgid1 = self.maketext(msgid1)
        msgid2 = self.maketext(msgid2)
        try:
            t = self.translation()
        except IOError:
            if n == 1:
                return msgid1
            return msgid2
        return t.ngettext(msgid1, msgid2, n)

    def ugettext(self, message):
        # unicoded gettext
        message = self.maketext(message)
        try:
            t = self.translation()
        except IOError:
            return message
        return t.gettext(message)


myGettext = myLocalGettext('')


def n_(x):
    return x


def fix_gettext():
    gettext.ugettext = myGettext.ugettext
    gettext.ungettext = myGettext.ungettext


fix_gettext()

_ = gettext.ugettext
ungettext = gettext.ungettext


def pgettext(context, message):
    key = "%s\x04%s" % (context, message)
    translated = _(key)
    return message if translated == key else translated
