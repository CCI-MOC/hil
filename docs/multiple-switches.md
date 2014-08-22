At some point or another we're going to want to deal with nodes on multiple
switches. Depending on the situation, we plan to handle this in one of two
ways:

1. Stack the switches. It's easy enough for us to support this without
   invasive changes to our existing code.
2. Shell out to a driver which deals with the complexity for us, e.g.
   OpenDaylight.
