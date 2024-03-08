# AvoidBalls

Run avoiding balls. If the character crosses the finish line, terrain will be changed.

I made this game to learn how to use GeoMipTerrain in BulletWorld of Panda3D. In this game, four heightmaps are arranged in tiles to make a large terrain. These heightmaps are created from elevation data in text files. Trees, rocks, water surfaces and flowers are dynamically arranged on the terrain. And I made my own simple character controller without using BulletCharacterControllerNode.  I unfortunately did not find the way of dropping the character's shadow on the terrain. I want to keep doing trial and error.

![demo](https://github.com/taKana671/AvoidBalls/assets/48859041/ab0f561e-7f6f-468f-b9cd-c16db2699bb7)

# Requirements
* Panda3D 1.10.13
* pandas 1.5.2
* numpy 1.23.5

# Environment
* Python 3.11
* Windows 11

# Usage
* Execute a command below on your command line.
```
>>>python avoid_balls.py
```

# Controls:
* Press [Esc] to quit.
* Press [up arrow] key to go foward.
* Press [left arrow] key to turn left.
* Press [right arrow] key to turn right.
* Press [down arrow] key to go back.
* Press [ D ] key to toggle debug ON and OFF.
