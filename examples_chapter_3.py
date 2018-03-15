import unittest
import pyif
import world
from world import LazyString


class Chapter3(unittest.TestCase):

    def setUp(self):
        world._debug = False
        pyif.make_blank_world()
        #world._debug = world.DEFAULT
        print('========')

    def tearDown(self):
        pyif._current_world.say('----------')
        del pyif._current_world

    def test_example2(self):
        def run_checks(world):
            for id, thing in world.things():
                if thing.check_for_property('description') and thing.description == "":
                    world.say('{0} has no description.', thing)

        pyif.title('Bic')
        pyif.when_play_begins('run through property checks at the start of play rule', run_checks, before=True)

        pyif.room('Staff Break Room')
        orange = pyif.thing('orange', description="It's a small hard pinch-skinned thing from the lunch room, \
            probably with lots of pips and no juice.")
        pen = pyif.thing('Bic pen')
        napkin = pyif.thing('napkin', description="Slightly crumpled")
        pyif.now_player_carries(orange, pen, napkin)

        pyif.go()
        self.assertTrue(pyif.last_message() == 'Bic pen has no description.')

    @unittest.skip('no clue what brief room descriptions mean')
    def test_example3(self):
        self.fail('not implemented')
    #this is the one that deals with brief room descriptions.

    def test_example4(self):
        pyif.title('Slightly Wrong')
        awning = pyif.room('Awning', description="A tan awning is stretched on tent poles over the dig-site, providing a \
little shade to the workers here; you are at the bottom of a square twenty feet on a side, marked out with \
pegs and lines of string. Uncovered in the south face of this square is an awkward opening into the earth.")
        chamber = pyif.room('Slightly Wrong Chamber',  map_connections={'south_of': awning})
        chamber.description = LazyString("{Main_description}A mural on the far wall depicts a woman with a staff, \
tipped with a pine-cone. She appears to be watching you.", {'Main_description': lambda story: 'When you first \
step into the room, you are bothered by the sense that something is not quite right: perhaps the lighting, \
perhaps the angle of the walls. ' if chamber.unvisited else ''}, pyif.current_world())
        pyif.go()
        pyif.test_with_actions(['looking', ('going', [pyif.current_world().directions['south']]), 'looking'])



if __name__ == "__main__":
    unittest.main()