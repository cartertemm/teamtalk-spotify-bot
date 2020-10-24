# TeamTalk Spotify Bot

A text only TeamTalk controller for Spotify, allowing management of playback on a host machine.

Users can effortlessly play/pause, adjust volume, find and play tracks/artists/playlists, manage the queue and more.

## Running

### Prerequisites

To get this working, you'll need a couple things.

* a Spotify premium account. This is an API requirement and unlikely to ever change.
* Python. Tested on 3.8.
* a TeamTalk installation capable of transmitting audio.
* the ability to route audio (see below)

Install our dependencies with

```
pip install -r requirements.txt
```

You should then be able to run the program:

```
python spotify-bot.py
```

If running for the first time, you'll get a message informing you that a configuration was successfully created. Open up config.ini in a text editor of your choice, follow the instructions, save and run the script again.
Assuming nothing went wrong a Spotify account authorization page will have been opened in your browser. Follow the steps.
When you return to the command window, select a playback device.

You can optionally provide the name of a configuration file as a parameter for easily keeping track of multiple servers:

```
python spotify-bot.py uspublic.ini
```

### Routing Audio

A full setup guide would be out of scope, but the basics are thus.
On windows, I like [VB Audio Cable](https://www.vb-audio.com/Cable/) (the free trial provides everything you need). [Virtual Audio Cable](https://vac.muzychenko.net/en/) is paid, but works as well.
On Mac OS, [Loopback](https://rogueamoeba.com/loopback/) is where it's at, though the single-user $99 price tag is a bit stiff. For free alternatives there's [BlackHole](https://github.com/ExistentialAudio/BlackHole) and it's less modern counterpart [SoundFlour](https://github.com/mattingalls/Soundflower).
You then want to configure Spotify so that it outputs to your virtual device. This is annoyingly not a feature in the app.
The simplest solution is to pipe your entire system through the virtual device by setting it as default. To get sound from a mic, input from your microphone and output to the virtual device. On windows you can use listen to this device in control panel. Loopback itself provides this capability, otherwise line in or hijack.

However, this may prove undesirable for many reasons. For one, it makes gameplay and other playback on the host machine difficult. There thankfully is another way.
You may be able to get just Spotify. Starting in windows 10 version 1803 Microsoft added a per app outputs feature, settings/system/sound/app volume and device preferences.
Note that Spotify will only show up in the list if music is playing or has been played after the app was opened.
Loopback can do the same.

Lastly, start a TeamTalk instance for streaming and input from your capture device under sound system.
