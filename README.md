# Weather and news station (e-paper and Raspberry Pi)

This is a fork of the project created originally by aerodynamics-py and enhanced by leonard-colin that changes how the update cycle works.

## Pre-requisite

First of all, please check [here](https://www.hackster.io/aerodynamics/weather-and-news-station-e-paper-and-raspberry-pi-a19fa3#toc-hardware-4) for the hardware used for this project, some explanations on how it works and then come back here to continue the software part. This project is theoretically compatible with all raspberry pi hardware as far as I know and you must use the same e-paper screen from the project for the best experience possible.

Next, you must make sur that your raspberry pi is fully updated and you have all following python modules otherwise you're in for some nasty surprises:
- colorama
- argparse
- crontab
- datetime

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install git
sudo apt-get install python3-colorama
sudo apt-get install python3-argparse
sudo apt-get install python3-crontab
sudo apt-get install python3-datetime
sudo apt-get install python3-pip
sudo apt-get install python3-pil
sudo apt-get install python3-numpy
sudo pip3 install spidev
```
Now, create a copy of the .env.example file and add your own coordonates/API keys 

```bash
cp .env.example .env
nano .env
```

If you want the weather station to say the dates in your own language, you can do that by adding your locale on the raspberry pi via raspi-config and change the ***locale.setlocale(locale.LC_TIME, 'YOUR_LOCALE')*** value on the weather.py script according to the locale you choosed before that. Please be aware that, as a french guy, most texts are in french so make sure that you translate it according to your language so you are not lost.

```bash
Raspberry Pi 3 Model B Rev 1.2, 1GB

┌──────────────────────┤ Raspberry Pi Software Configuration Tool (raspi-config) ├──────────────────────┐
│                                                                                                       │
│                   1 System Options       Configure system settings                                    │
│                   2 Display Options      Configure display settings                                   │
│                   3 Interface Options    Configure connections to peripherals                         │
│                   4 Performance Options  Configure performance settings                               │
│                   5 Localisation Options Configure language and regional settings                     │
│                   6 Advanced Options     Configure advanced settings                                  │
│                   8 Update               Update this tool to the latest version                       │
│                   9 About raspi-config   Information about this configuration tool                    │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                             <Select>                             <Finish>                             │
│                                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
```bash
┌──────────────────────┤ Raspberry Pi Software Configuration Tool (raspi-config) ├──────────────────────┐
│                                                                                                       │
│                     L1 Locale       Configure language and regional settings                          │
│                     L2 Timezone     Configure time zone                                               │
│                     L3 Keyboard     Set keyboard layout to match your keyboard                        │
│                     L4 WLAN Country Set legal wireless channels for your country                      │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                                                                                                       │
│                             <Select>                             <Back>                               │
│                                                                                                       │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```
```bash
Package configuration

 ┌──────────────────────────────────────┤ Configuring locales ├───────────────────────────────────────┐
 │ Locales are a framework to switch between multiple languages and allow users to use their          │
 │ language, country, characters, collation order, etc.                                               │
 │                                                                                                    │
 │ Please choose which locales to generate. UTF-8 locales should be chosen by default, particularly   │
 │ for new installations. Other character sets may be useful for backwards compatibility with older   │
 │ systems and software.                                                                              │
 │                                                                                                    │
 │ Locales to be generated:                                                                           │
 │                                                                                                    │
 │  [ ] All locales                                                                               ↑   │
 │  [ ] aa_DJ.UTF-8 UTF-8                                                                         ▒   │
 │  [ ] aa_ER UTF-8                                                                               ▒   │
 │  [ ] aa_ER@saaho UTF-8                                                                         ▒   │
 │  [ ] aa_ET UTF-8                                                                               ▒   │
 │  [ ] af_ZA.UTF-8 UTF-8                                                                         ▒   │
 │  [ ] agr_PE UTF-8                                                                              ▒   │
 │  [ ] ak_GH UTF-8                                                                               ↓   │
 │                                                                                                    │
 │                                                                                                    │
 │                            <Ok>                                <Cancel>                            │
 │                                                                                                    │
 └────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

Last but not least, you need to create a cronjob that, in case of the raspberry pi shutting down due to a power outage or you have to restart it, it will launch at startup the start_weathernews.py that will check if the cronjob that launches periodically the Assistant_main.py script exists. If it's not the case, it will recreate it and will log all actions on the cronjob_creation.log.

```bash
crontab -e
@reboot /usr/bin/python3 /path/to/start_weathernews.py >> /path/to/cronjob_creation.log
```
## Installation

Just download the files from Github, launch the start_weathernews.py and enjoy some weather forecast and some news. Just make sure to check all file/folder paths and variables on the scripts before proceeding or else weired stuff could happen.

```bash
cd my/path/to/the/project
git clone https://github.com/depuntism/WEATHER_STATION_PI.git
python3 /path/to/startweathernews.py
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.


## Credits

All credits goes to areodynamics-py for creating this project which can be found [here](https://www.hackster.io/aerodynamics/weather-and-news-station-e-paper-and-raspberry-pi-a19fa3) and leonard-colin for making some welcoming tweaks to the original project.
