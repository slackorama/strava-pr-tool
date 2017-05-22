Strava PR by Bike
======================

About
-----

Do you have more than one bike and want to know which you rode to get your
personal record? Then this is the app for you.

Do you want to know how far off you were your PR on a ride? Then this app is for
you.

This will pull all your efforts from an activity and find yoru Personal Record
for the segments on that activity and output a CSV that you can either import
into Excel or some other CSV processing tool.

Usage
-----

Either pass it a activity id like:

    python app.py 12345 > myride.csv
    
or just run it with no arguments and it'll grab the most recent activity:

    python app.python > myride.csv
    
The columns in the CSV are:

name | description
---- | -------------
id | segment id
name |  segment name
starred | is the segment starred
bike | name of bike with PR
distance | length (in miles) of segment
time | amount of time this effort took
pr | amount of time your PR took
diff | difference between this effort and your PR
 
    
Dependencies
-------------

Requires the most excellent [stravalib](https://github.com/hozn/stravalib).

Also, you'll need a client id and a way to get an access token. There's
`get_auth_code` in `app.py` but it's kind of a kludge. When you have both of
those, put them in a file named `strava-pr.cfg` in this directory, in your home
directory or in `$HOME/.config/strava-pr/config.`

Also, this file outputs CSV and [csvkit](https://github.com/wireservice/csvkit)
is kind of invaluable if you want to do everything from the command line.

For example:
    
    ; python app.py > myride.csv
    ; csvsort -c diff myride.csv  | csvlook | head
    |-----------|-----------|---------|---------------|----------|----------|----------|---------|
    |  id       | name      | starred | bike          | distance | time     | pr       | diff    |
    |-----------|-----------|---------|---------------|----------|----------|----------|---------|
    |  3783188  | Segment 1 |         | Fancy Bike    | 2.751    | 00:12:06 | 00:09:50 | -136.0  |
    |  8168280  | Segment 2 |         | Fancy Bike    | 1.517    | 00:05:55 | 00:04:35 | -80.0   |
    |  1484912  | Segment 3 |         | Crappy Beater | 1.751    | 00:07:12 | 00:06:01 | -71.0   |
    |  6786795  | Segment 4 |         | Fancy Bike    | 0.342    | 00:01:33 | 00:00:59 | -34.0   |
    |  6449743  | Segment 5 |         | Fancy Bike    | 0.839    | 00:02:42 | 00:02:09 | -33.0   |
    |  8168293  | Segment 6 |         | Fancy Bike    | 0.522    | 00:01:52 | 00:01:20 | -32.0   |
    |  2785851  | Segment 7 |         | Fancy Bike    | 0.47     | 00:01:35 | 00:01:06 | -29.0   |


TODO
----

- Better way to get access token.
- Don't just output csv
- Ability to output in metric or English
- Lots more.
