# The Carcassonne Companion App
My wife an I mreavid board game hobbyist,s with a 50+ fgame collection. We like all sorts of games from classics like Catan, to newer releases like Arcs. Carcassonne sits as an all time favorite for my wife, and I can't argue it is a solid game that serves well as gateway for newcomers, while keeping seasoned players engaged.
arcassonne is the classic rtile-laying game. You place a tile in a valid configuration and _optionally_ place a meeple. You have a limited supply of meeples and meeples are left on the board until they score. At the end of the game, remaining meeples are scored. This last step can be tedious since you have to keep track of unfinished cities, roads, monasteries, and farmers.
My vision is to create an app where you take one picture of the board and it calculates the score for you.
There are 2 main steps in this process:
1. Recognizing the board state
2. Calculating the final Sscore. 
## Recognizing the board state
### Meeples
Meeples can be upright or layigng down. If laying down, these are *farmers*. If standing up we will need to determine in what unfinished construction are they.

### Tiles
Carcassonne tiles are square. Each tile can be defined by the type of construction they have at the edge except monasteries, which are placed in the center of the tile.
1. City
2. City with shield
3. Field
4. Road 
5. Monastery  
