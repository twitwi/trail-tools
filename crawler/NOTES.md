

# Scripts

,,* files can be ignored

Trying to remember what each script does.
The scripts actually use xpath when requesting XML data.
NB: I call strain some combination of distance plus D+.

### livetrail_timedist.py

This one is interesting to actually use the data.

- accepts any number of table file(s)
- accepts also parameters like BOF=516 to override some global variables
- it is an example that collect all segments for all people in the race
  - then plots as a function of strain (dist + D+), the negative time (in -hours) (higher is faster)
  - also does a scatter plot of time at R1 vs time at the end (colored by at which ravito they drop off)

### livetrail_digest.py

Mostly like livetrail_timedist
- (written before so utility functions might be slightly less advanced)
- plots the speed (strain/h), to observe the decrease in speed during the race
- tries 3 different strain coefficients (100, 150 and 200mD+/km)
  - I don't remember but the goal was to find which coefficient is a best predictor across runners, and I think I was supposing that a bad coefficient will increase the variance of the speed, so I plot this variance...
  - huge peaks in variance usually mean there is a wrong distance/d+ in the route description (or that there is a notable aid station ?)
  


### livetrail_get.py ((crawler))

- receives a course_url (either full http... or just an livetrail id like utmb)
- it possibly receives a second parameter which is the course id, in case the url is not containing the id, or we want to force it (as it is used for saving files), e.g., it is used to get the latest race but save its year, e.g. use python livetrail_get.py utmb utmb2022
- it then gets the info file for the event
- and for each subcourse (actual race), it gets the passages.php and stats.php
- it also prints the history of previous events (when available)

### livetrail_get_runners_for.py ((crawler))

- receives table files (and possible VAR=... override)
- it will create one file per runner with its information, including the itra id (not sure all races provide it)
- there is a comment about how we (at the time at least) could request itra to get some stats



# Notes Livetrail

home of a race is data + link to a php-xsl that formats it
where the subrace id is $e/@id (e.g. utmj, linx)


getting the table for a race at https://utmj.livetrail.run/passages.php, with some formdata
but in the end it is
https://utmj.livetrail.run/passages.php?course=utmj&cat=scratch&from=1&to=1000


The distance and D+ are in a single /parcours.php url for all subcourses

The starting time might need to be taken from hp(remier) hd(ernier) in the first parcours point.

... got slightly less than 1 million bibs

