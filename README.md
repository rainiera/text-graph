# text-graph
graphs on graphs on graphs. Continuation of project from 6Sense Datahack for fun.

At the hackathon:
- Wrangling of data from GO SMS Text backups and processing into Python objects (OOP code was a bit messy)
- Implemented hashmap-like (word-for-word) named entity recognition on `TextMessage` objects to generate `Contact` nodes for the graph
- Added sentiment analysis of each `TextMessage` object using `Indico` API for high quality sentiment analysis, added to CSV file to store these results (did not want to do 18K API calls multiple times when I was limited to 100K a month)
- Did a tiny bit of a `Neo4j` CRUD wrapper
- Played around with `d3.js`, `alchemy.js` - unsuccessful because of some weird JS graphics calculation errors

To do:
- An extensible `Graph` implementation would be nice
- ORM API wrapper for the `Neo4j` REST client
- Sweet visualization dashboard? Python or d3?
