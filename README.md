Service Planner is an app that allows you to plan live production actions & schedule them through Planning Center Online, simplifying the live production environment.


# A few tasks to get things working:
- Install Python 3.7 with pip + add to PATH
- Item cues are stored in a planning center item app category named "App Cues". For each service category that you intend to use this with, create a item note category named "App Cues".
- Global cues are stored in a plan note named "App Cues". Same as before, for each service category, create a plan note category named "App Cues".
- Get an Application ID and Secret [Personal Access Tokens](https://api.planningcenteronline.com/oauth/applications). You will be asked to enter this info upon first launch.
- Run the program by running "main.py" (Python 3.7)
- Load up any plan and go to utilities(gear button at the top)>device editor. Add all devices that you wish to control


## Running a Service
The idea of this app is to simplify a live service production **as much as possible** by moving all of the thought into equipment cues/actions to BEFORE the service.
During a serivce, the only thing you should have to do is press the "NEXT" button. 
- Next: Advances to the next item, cueing any cues on the next item
- Previous: Goes to previous item, cueing any cues on the previous item
- Next (No actions) Advances to next item only. No cues are activated.
- Previous (No actions) Goes to previous item only. No cues are activated.

## Actions/Cues can be in 2 forms:
### Global Cues
Cue/list of cues that is saved as a button at the bottom of the plan and is accessable at any time
### Item Cues
Cue/list of cues that is saved on a plan item. Cues are activated when that item goes live.

## Current actions available:

### ProVideoPlayer:
- Get list of playlist & cues
- Cue playlist items

### Resi:
- Play
- Pause
- Play and fade from black
- Fade to black and pause
- Fade from black
- Fade to black
  
### AJA KiPro:
- Start recording (appends date/time to file name)
- Stop recording
- Format all
- Get media storage remaining
 
### Rosstalk:
- Custom Controls
- You can add custom CC labels by editing carbonite_cc_name_template.ods and saving it as a new file. Add the new file under device manager>carbonite>add Custom Control labels
 
### Reminders:
- Strictly a reminder to do something, after a set amount of time. (Ex. After 2 minutes: get confidence monitor notes ready)

## Utilites Menu:
### Start Live Service:
If a service is not currently live, **Start Live Service** will advance to the first item.
### Advance to Next Service
If you have multiple service times scheduled, this will advance through each item and stop on the first item of the next scheduled service. No action is taken if no service is scheduled after the current one.
### Reload plan
Simply reloads the plan. Useful for if someone reorders or adds items 
### Load Adjacent Plan
Keep track of another live plan. Most useful if you have other areas or plans that you need to keep an eye on. In my case, we're a multi-campus church that we stream live video to, so it's helpful to see where the satellite campus is at in their service.
### Download KiPro Clips:
Not working yet
### Add Global Cue
As referenced above, add a action or set of actions with a custom name to a button at the bottom of the screen that can be accessed at any time
### Remove Global Cue
Remove a global cue after it's been added, if desired
### Device Editor
Add/remove physical devices
