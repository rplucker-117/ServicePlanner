import asyncio
from bscpylgtv import WebOsClient
from pprint import pprint

class WebOSTV:
    def __init__(self, ip: str):
        self.ip: str = ip

    async def _get_inputs_async(self) -> dict:
        client = await WebOsClient.create(self.ip)
        await client.connect()
        result = await client.get_inputs()
        await client.disconnect()
        return result

    def get_inputs(self) -> dict:
        return asyncio.run(self._get_inputs_async())

    async def _switch_to_input_async(self, input_id: str) -> None:
        client = await WebOsClient.create(self.ip)
        await client.connect()
        await client.set_input(input_id)
        await client.disconnect()
        client.button()

    def switch_to_input(self, input_id: str) -> None:
        return asyncio.run(self._switch_to_input_async(input_id))

    async def _set_volume_async(self, volume: int) -> None:
        client = await WebOsClient.create(self.ip)
        await client.connect()
        await client.set_volume(volume)
        await client.disconnect()

    def set_volume(self, volume: int) -> None:
        return asyncio.run(self._set_volume_async(volume))

    async def _set_mute_state_async(self, mute: bool) -> None:
        client = await WebOsClient.create(self.ip)
        await client.connect()
        await client.set_muted_state(mute)
        await client.disconnect()

    def set_mute_state(self, mute: bool) -> None:
        return asyncio.run(self._set_mute_state_async(mute))

    async def _set_power_off_async(self) -> None:
        client = await WebOsClient.create(self.ip)
        await client.connect()
        await client.power_off()
        await client.disconnect()

    def set_power_off(self) -> None:
        return asyncio.run(self._set_power_off_async())

    async def _press_button_async(self, button: str) -> None:
        """
        :param button:
                "LEFT",
                "RIGHT",
                "UP",
                "DOWN",
                "RED",
                "GREEN",
                "YELLOW",
                "BLUE",
                "CHANNELUP",
                "CHANNELDOWN",
                "VOLUMEUP",
                "VOLUMEDOWN",
                "PLAY",
                "PAUSE",
                "STOP",
                "REWIND",
                "FASTFORWARD",
                "ASTERISK",
                "BACK",
                "EXIT",
                "ENTER",
                "AMAZON",
                "NETFLIX",
                "3D_MODE",
                "AD",                   # Audio Description toggle
                "ADVANCE_SETTING",
                "ALEXA",                # Amazon Alexa
                "AMAZON",               # Amazon Prime Video app
                "ASPECT_RATIO",         # Quick Settings Menu - Aspect Ratio
                "CC",                   # Closed Captions
                "DASH",                 # Live TV
                "EMANUAL",              # User Guide
                "EZPIC",                # Pictore mode preset panel
                "EZ_ADJUST",            # EzAdjust Service Menu
                "EYE_Q",                # Energy saving panel
                "GUIDE",
                "HCEC",                 # SIMPLINK toggle
                "HOME",                 # Home Dashboard
                "INFO",                 # Info button
                "IN_START",             # InStart Service Menu
                "INPUT_HUB",            # Home Dashboard
                "IVI",
                "LIST",                 # Live TV
                "LIVE_ZOOM",            # Live Zoom
                "MAGNIFIER_ZOOM",       # Focus Zoom
                "MENU",                 # Quick Settings Menu
                "MUTE",
                "MYAPPS",               # Home Dashboard
                "NETFLIX",              # Netflix app
                "POWER",                # Power button
                "PROGRAM",              # TV Guide
                "QMENU",                # Quick Settings Menu
                "RECENT",               # Home Dashboard - Recent Apps or last app
                "RECLIST",              # Recording list
                "RECORD",
                "SAP",                  # Multi Audio Setting
                "SCREEN_REMOTE",        # More Actions panel
                "SEARCH",
                "SOCCER",               # Sport preset
                "TELETEXT",
                "TEXTOPTION",
                "TIMER",                # Sleep Timer panel
                "TV",
                "TWIN",                 # Twin View
                "UPDOWN",               # Always Ready app
                "USP",                  # Movie, TVshow, app list
                "YANDEX",
                "0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9"
        :return:
        """

        client = await WebOsClient.create(self.ip)
        await client.connect()
        await client.button(str(button))
        await client.disconnect()

    def press_button(self, button: str) -> None:
        return asyncio.run(self._press_button_async(button))

if __name__ == '__main__':
    tv = WebOSTV('10.1.60.90')
    tv.press_button('BACK')


