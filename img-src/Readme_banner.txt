Banner was build with help of copilot, gemini and mistral ai to renew the background.
I described the original banner from Nils Liberg (abclogo.png)
I described then how I would like it to be renewed trying to keep the original colors and remind EasyABC.

After some trials, I finally decided to redo something easier to maintain and modify later on.
Thus I've build some svg image that will be used to build
* icons of app and abc file
* banner of the welcome page, about page and documentation
* background of DMG file for Mac

So I reused some colors from the original abclogo.png.
I then on one side worked on the text EasyABC and also on the note to be used accross the various images.

I put the svg in the img-src folder. This is not embedded in the app when build but kept in case needed.
For the banner to emphasize the job of EasyABC, instead of putting just the music score that was in the banner,
I've put two panels to be able to show on one side the editor part of the ABC code and on the other part the music score.
I reused the abc code transcribed by Nils Liberg for the exact same music.
To feat in the screenshot I just modified a bit the abc code to remove some of the comments and details.
The completa Abc is taken from http://www.folkwiki.se/Musik/231 transcribed by Nils itself back when he created EasyABC.

Once screenshots done, the merge is done with the help of GIMP.

First open the Background-Header.svg
Then add as a new layer the abc-code2.png
Use the tool perspective to be able to align with the left panel of the background.
Once done valide the transformation in the perspective dialog.
Then go to the background and use the tool to select all part in red.
On the layer with the screenshot right click and add a mask checking the option selection and validate

Repeat the operation with the Partition.png and the blue panel.

Then you can replace the red and blue area by a very light green.

Especially on the right panel it can help to rework the scrore rendering.
Indeed once you've replace by light green you can the go to the musicscore layer and replace the white color by the alpha (transparent).

The xcf file is saved for further modification if needed.

Then jpg and png file are exported.
They can be used in the About page, the new welcome page and the refreshed documentation.

Frédéric Aupépin