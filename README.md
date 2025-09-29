# richmpris

rich presence for the linux MPRIS d-bus

# installation

head over to the [releases tab](https://github.com/Gapva/richmpris/releases/latest) and grab a binary

fire up a terminal, navigate to wherever you've downloaded the binary, and `./richmpris`.
you can add the `-h` or `--help` argument to view a list of all arguments and what they do

# features

### sanitized metadata by default
perhaps the most unique feature of richmpris is its automatic metadata cleansing.

this is primarily useful when listening to youtube videos. for example, automatically detecting the
artist and title from the video's title. youtube is full of reuploaded songs by people who are not actually
the artist, and this can make it difficult for your rich presence to look clean.

many redundant phrases are also blocked from showing up in the metadata,
including "(music video)", "(audio)", "(lyric video)", etc. just to name a few

### webhooks

richmpris has the ability to connect to discord webhooks througn an argument and post your
listening status that way.

<img width="414" height="720" alt="image" src="https://github.com/user-attachments/assets/e9018bea-2e06-43a3-a97b-3ceab48caaef" />

# contributing

fork and make a [pull request](https://github.com/Gapva/richmpris/compare)
