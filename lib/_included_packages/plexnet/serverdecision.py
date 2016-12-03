import mediachoice
import util


class ServerDecision(object):
    DECISION_DIRECT_PLAY = "directplay"
    DECISION_COPY = "copy"
    DECISION_TRANSCODE = "transcode"
    DIRECT_PLAY_OK = 1000
    TRANSCODE_OK = 1001

    def __init__(self, original, response, player):
        self.original = original
        self.response = response
        self.player = player

        self.init()

    def init(self):
        self.isSupported = self.response.server.supportsFeature("streamingBrain")
        self.item = self.response.items[0]

        if self.item and self.item.mediaItems:
            self.original.transcodeDecision = mediachoice.MediaChoice(self.item.mediaItems[0])

        # Decision codes and text
        self.decisionsCodes = {}
        self.decisionsTexts = {}
        for key in ["directPlayDecision", "generalDecision", "mdeDecision", "transcodeDecision", "termination"]:
            self.decisionsCodes[key] = self.response.container.get(key + "Code", "-1").asInt()
            self.decisionsTexts[key] = self.response.container.get(key + "Text")

    def __str__(self):
        if self.isSupported:
            obj = []
            for v in self.decisionsTexts.values():
                if v:
                    obj.append(v)
            return ' '.join(obj)
        else:
            return "Server version does not support decisions."

    def __repr__(self):
        return self.__str__()

    def getDecision(self, requireDecision=True):
        if not self.item:
            # Return no decision. The player will either continue with the original
            # or terminate if a valid decision was required.

            if requireDecision:
                # Terminate the player by default if there was no decision returned.
                code = self.decisionsCodes["generalDecision"]
                reason = ' '.join([self.decisionsTexts["transcodeDecision"], self.decisionsTexts["generalDecision"]])
                self.player.terminate(str(code), reason)
            return None

        # Rebuild the original item with the new item.
        util.WARN_LOG("Server requested new playback decision: {0}".format(self))
        self.original.rebuild(self.item, self)
        return self.original

    def isSuccess(self):
        code = self.decisionsCodes["mdeDecision"]
        return not self.isSupported or code >= 1000 and code < 2000

    def isDecision(self, requireItem=False):
        # Server has provided a valid decision if there was a valid decision code
        # or if the response returned zero items (could not play).

        return self.isSupported and (self.decisionsCodes["mdeDecision"] > -1 or requireItem and not self.item)

    def isTimelineDecision(self):
        return self.isSupported and self.item

    def isTermination(self):
        return self.isSupported and self.decisionsCodes["termination"] > -1

    def getTermination(self):
        return {
            'code': str(self.decisionsCodes["termination"]),
            'text': self.decisionsTexts["termination"] or "Unknown"  # TODO: Translate Unknown
        }

    def getDecisionText(self):
        for key in ["mdeDecision", "directPlayDecision", "generalDecision", "transcodeDecision"]:
            if self.decisionsTexts.get(key):
                return self.decisionsTexts[key]
        return None
