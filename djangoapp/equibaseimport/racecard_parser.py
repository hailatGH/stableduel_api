from rest_framework.parsers import BaseParser

class RacecardParser(BaseParser):
    media_type = 'xml'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()

class RacecardAppXmlParser(BaseParser):
    media_type = 'application/xml'

    def parse(self, stream, media_type=None, parser_context=None):
        return stream.read()