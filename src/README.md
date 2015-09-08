
I have all of the SMS texts I've ever sent/received in XML format because I owned an app that would back up your texts. It's called GO SMS Pro, and has about 100 million users according to their Google Play.

I made a small library that takes that specific format, and creates a graph database of all your contacts and the people they mention. Based on every text that includes me or my contacts mentioning other contacts, I used Indico's high-quality version sentiment analysis API to determine our relationships with each other.

Nothing serious, just for fun :)

Some stuff that would make this really good!

- Used the `humanhash` library to make `hexdigest` more human-readable but still be able to obscure my contacts' names _prior_ to even sending the data to the API... this may have affected the sentiment analysis slightly, especially since a lot of the texts were really short.
- Didn't include emoji or use a different encoding for them because it was breaking Python's standard library csv file IO. Of course, I was going back and forth between `pandas` and `csvfile`.
- I have a contact named Will... maybe y'all could guess what happened then, or what _will_ happen if people use that word...
- I could have gotten Facebook's data dump or backed up all my texts from this year as well. But I think at like 18200 texts my computer could handle enough.


Some things I used:

- [Indico](http://indico.io)
- [Anaconda](https://store.continuum.io/cshop/anaconda/)
- [Flask](http://flask.pocoo.org/)
- `pandas`
- `networkx`
- `cElementTree`
- `humanhash`

Inspiration:

- [Neo4j](http://neo4j.com/developer/graph-database/)
- [Indico](http://indico.io)
- The movie _The Social Network_

Made with <3 from SF at the 6Sense DataHack  
Thanks
