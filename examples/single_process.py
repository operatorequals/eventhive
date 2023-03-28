import eventhive

eventhive.EVENTS.append('bee_stuff',
                        # The place to document what this Event does
                        help="""What worker bees do
  for a living"""
                        )

# Subscribe to 'bee_stuff'


@eventhive.hook("bee_stuff")
def fly_around(arg1):
    print("Looking for {} flowers!".format(
        arg1)
    )


@eventhive.hook("bee_stuff")
def get_pollen(work):
    print("Gathering pollen from a {} flower!".format(
        work)
    )


@eventhive.hook("bee_stuff")
def come_back(arg, optional=False):
    if not optional:
        print("Bringing {} pollen back to beehive!".format(
            arg)
        )


# Publish 'daisy' to 'bee_stuff'
eventhive.EVENTS['bee_stuff']("daisy")
