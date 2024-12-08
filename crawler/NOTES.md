

# NEW 2024-12

Reget all race results

After finding the json on the root of livetrail, I save it as config-raw-event-list-from-livetrail.json

~~~bash
alias batch='python3 livetrail_get_batch.py'
batch fetch-all-events
# ^ repeat as it stops on error and some years do not exist (we can find them back as --parcours.xml is empty, but they really don't work)

batch compile-race-infos | sort -g
# ^ WIP on producing some csv to describe races

# maybe in a loop
batch fetch_all_race_runners
#monitor with
cat data/livetrail--*runners.xml|grep 'ruri'|sed 's@.*ruri="\([^"]*\)".*@\1@g'|wc
 213292  213292 4964361
cat data/livetrail--*runners.xml|grep 'ruri'|sed 's@.*ruri="\([^"]*\)".*@\1@g'|sort|uniq|wc
 126109  126109 2943049
cat data/livetrail--*runners.xml|grep 'ruri'|sed 's@.*ruri="\([^"]*\)".*@\1@g'|sort|uniq -c|sort -g
cat data/livetrail--*runners.xml|grep 'ruri'|sed 's@.*ruri="\([^"]*\)".*@\1@g'|sort|uniq -c|sort -g|awk '{print $1 " races"}'|uniq -c
  78807 1 races
  26205 2 races
  11374 3 races
   5023 4 races
   2450 5 races
   1165 6 races
    568 7 races
    277 8 races
    119 9 races
     61 10 races
     31 11 races
      9 12 races
     10 13 races
      1 14 races
      4 15 races
      1 16 races
      1 17 races
      1 19 races
      1 20 races
      1 23 races

~~~

xmllint --format data/livetrail--utmj--2020--utmj---stats.xml


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

