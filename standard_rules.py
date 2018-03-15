import pyif
import world
from world import Kind

#region create base kinds

def create_room(room):
    room.can_be(['lighted', 'dark'], usually='lighted')
    room.can_be(['visited', 'unvisited'], usually='unvisited')
    room.has('description', '')
    room.has('map region', Kind.nothing)
    room.has('map connections', {})
    room.has('location')


def create_thing(thing):
    thing.can_be(['lit', 'unlit'], usually='unlit')
    thing.can_be(['edible', 'inedible'], usually='inedible')
    thing.can_be(['fixed in place', 'portable'], usually='portable')
    thing.can_be('scenery')
    thing.can_be('wearable')
    thing.has('description', '')
    thing.has('location', 'nowhere')
    thing.can_be('pushable between rooms', usually=True)
    thing.can_be('handled')
    thing.can_be(['described', 'undescribed'], usually='described')
    thing.can_be(['mentioned', 'unmentioned'], usually='mentioned')
    thing.can_be(['marked for listing', 'unmarked for listing'], usually='unmarked for listing')
    thing.has('initial appearance', '')
    #room.has('map region', Kind.nothing)


def create_direction(direction):
    direction.has('opposite', Kind.nothing)


#neater to encapsulate this all here
def define_directions():
    n = pyif.direction('north', 'n')
    ne = pyif.direction('northeast', 'ne')
    nw =pyif.direction('northwest', 'nw')
    s = pyif.direction('south', 's')
    se = pyif.direction('southeast', 'se')
    sw = pyif.direction('southwest', 'sw')
    e = pyif.direction('east', 'e')
    w = pyif.direction('west', 'w')
    u = pyif.direction('up', 'u')
    d = pyif.direction('down', 'd')
    i = pyif.direction('inside', 'in')
    o = pyif.direction('outside', 'out')

    n.opposite = s
    s.opposite = n
    ne.opposite = sw
    nw.opposite = se
    se.opposite = nw
    sw.opposite = ne
    e.opposite = w
    w.opposite = e


def create_door(door):
    door.is_always('fixed in place')
    door.is_never('pushable between rooms')
    door.has('other side', Kind.nothing)

    door.can_be(['open', 'closed'], usually='closed')
    door.can_be(['openable', 'unopenable'], usually='openable')
    door.can_be('lockable', usually=False)
    door.can_be(['locked', 'unlocked'], usually='unlocked')
    door.has('matching key', Kind.nothing)


def create_container(container):
    container.can_be('enterable')
    container.can_be(['opaque', 'transparent'], usually='opaque')
    container.has('carrying capacity', usually=100)

    container.can_be(['open', 'closed'], usually='open')
    container.can_be(['openable', 'unopenable'], usually='unopenable')
    container.can_be('lockable', usually=False)
    container.can_be(['locked', 'unlocked'], usually='unlocked')
    container.has('matching key', Kind.nothing)

    container.implication(if_property='locked', then={'usually': 'lockable'})
    container.implication(if_property='locked', then={'never': 'edible'})


def create_supporter(supporter):
    supporter.can_be('enterable')
    supporter.is_usually('fixed in place')
    supporter.has('carrying capacity', usually=100)


def create_backdrop(backdrop):
    backdrop.is_usually('scenery')
    backdrop.is_always('fixed in place')
    backdrop.is_never('pushable between rooms')


def create_person(being):
    being.can_be(['male', 'female', 'neuter'], usually='neuter')
    being.has('carrying capacity', usually=100)


def create_device(device):
    device.can_be(['switched on', 'switched off'], usually='switched off')


def create_vehicle(vehicle):
    vehicle.is_always('enterable')
    vehicle.is_usually('not portable')


def create_holdall(holdall):
    holdall.is_always('portable')
    holdall.is_usually('openable')

#endregion

def create_base_rulebooks():
    def set_action_vars(world, actor, action, nouns):
        action.current_actor = actor
        action.current_nouns = nouns
        action['set action variables rules'].follow(action=action)

    def intro_text(world):
        story = world
        story.say('-------')
        story.say(story.title)
        story.say('-------\n')

    def descend_processing(world, actor, action, nouns):
        return world.rulebooks['specific action processing rules'].follow(actor=actor, action=action, nouns=nouns)

    def work_out_details(world, actor, action, nouns):
        pass

    def position_player(world):
        world.get_player().location = world.first_room_made

    begins = pyif.add_rulebook('when play begins rules')
    begins.add_rule_first('display banner rule', intro_text)
    begins.add_rule_first('position player in model world rule', position_player)
    begins.add_rule_first('initial room description rule', lambda world: pyif.try_action('looking'))


    pyif.add_rulebook('before rules')
    pyif.add_rulebook('instead rules')

    ap = pyif.add_rulebook('action processing rules')
    #announce multiple from list, set pronouns are skipped
    ap.add_rule_first('set action variables rule', set_action_vars)
    ap.add_rule_first('before stage rule', lambda world: world.rulebooks['before rules'].follow())
    ap.add_rule('carrying requirements rule', None)
    ap.add_rule('basic visibility rule', None)
    ap.add_rule('basic accessibility rule', None)

    ap.add_rule_last('instead stage rule', lambda world: world.rulebooks['instead rules'].follow())
    ap.add_rule_last('requested actions require persuasion rule', None)
    ap.add_rule_last('carry out requested actions rule', None)
    ap.add_rule_last('descend to specific action processing rule', descend_processing)
    ap.add_rule_last('end action processing rule', None)

    sap = pyif.add_rulebook('specific action processing rules')
    sap.add_rule_first('work out details of specific action processing rule', work_out_details)
    sap.add_rule('investigate player awareness before action rule', None)
    sap.add_rule('check stage rule', lambda world, actor, action, nouns: action.check_rules.follow(action=action))
    sap.add_rule('carry out stage rule', lambda world, actor, action, nouns: action.carry_out_rules.follow(action=action))
    sap.add_rule('after stage rule', None)
    sap.add_rule('investigate player awareness after action rule', None)
    sap.add_rule('report stage rule', lambda world, actor, action, nouns: action.report_rules.follow(action=action))
    sap.add_rule('last rule', lambda world: True)


def create_action(action):
    action.has('set action variables rules', world.Rulebook('setting ' + action.name + 'action variables rules',
                                                               world))
    action.has('applies to')
    action.has('before rules')
    action.has('check rules')
    action.has('carry out rules')
    action.has('report rules')
    action.has('current actor', None)
    action.has('current nouns', None)


def create_base_actions():
    #world._debug = world.VERBOSE
    create_looking()
    create_going()


def create_looking():
    def desc_heading_rule(world, action):
        w = world
        w.say(action.current_actor.location.name + ' (current room)')

    def desc_body_rule(world, action):
        #world.say('(describing the room)')
        world.say('\n'+action.current_actor.location.description+'\n\n')

    def check_arrival_rule(world, action):
        if action.current_actor.location.type == 'room':
            action.current_actor.location.visited = True

    look = pyif.action('looking', understand_as=['look'], applies_to=0)
    # what action was used to call look,
    look.has('room describing action', usually='look')
    look.has('visibility level count')
    look.has('visibility ceiling')
    look['set action variables rules'].add_rule('determine visibility ceiling rule')
    look.carry_out_rules.add_rule('room description heading rule', desc_heading_rule)
    look.carry_out_rules.add_rule('room description body rule', desc_body_rule)
    look.carry_out_rules.add_rule('room description paragraphs about objects rule', desc_obj_rule)
    look.carry_out_rules.add_rule('check new arrival rule', check_arrival_rule)
    look.report_rules.add_rule('other people looking rule', other_people_looking)


def create_going():
    def set_going(world, action):
        action.room_gone_from = action.current_actor.location

    def move_player_vehicle_rule(world, action):
        world.say('You head ' + action.current_nouns[0].id + '.\n')
        if action.vehicle_gone_by is None:
            world.move(action.current_actor, action.room_gone_to)
        else:
            world.move(action.current_actor.location, action.room_gone_to)

    def determine_conn(world, action):
        target = None
        if action.current_nouns[0].type == 'direction':
            target = world[action.room_gone_from.map_connections[action.current_nouns[0].id]]
        action.room_gone_to = target

    def describe_new_room(world, action):
        #guessed at here https://www.intfiction.org/forum/viewtopic.php?f=7&t=2948&start=10
        if action.current_actor is world.player:
            world.rulebooks['check looking rules'].follow(action=action)
            world.rulebooks['carry out looking rules'].follow(action=action)
            world.rulebooks['report looking rules'].follow(action=action)

    going = pyif.action('going', understand_as=['go'], applies_to=1)
    going.has('room gone from')
    going.has('door gone through')
    going.has('room gone to')
    going.has('vehicle gone by')
    going.has('thing gone with')
    going['set action variables rules'].add_rule('standard set going variables rule', set_going)
    going.check_rules.add_rule('determine map connection rule', determine_conn)
    going.carry_out_rules.add_rule('move player and vehicle rule', move_player_vehicle_rule)

    going.report_rules.add_rule('describe room gone into rule', describe_new_room)


def desc_obj_rule(r, action):
    pass


def other_people_looking(r, action):
    pass


def create_standard_rules():
    standard = world.World()
    pyif._current_world = standard

    room = pyif.kind('room', create_room)
    room('test')

    thing = pyif.kind('thing', create_thing)
    thing('test')

    pyif.kind('direction', create_direction)
    define_directions()

    door = pyif.kind('door', create_door, kindof='thing')
    door('test')

    container = pyif.kind('container', create_container, kindof='thing')
    container('test')

    supporter = pyif.kind('supporter', create_supporter, kindof='thing')
    supporter('test')
    backdrop = pyif.kind('backdrop', create_backdrop, kindof='thing')
    backdrop('test')

    being = pyif.kind('being', create_person, kindof='thing')
    being('test')
    person = pyif.kind('person', kindof='being')
    yourself = pyif.person('yourself', 'undescribed')
    yourself.description = 'As good-looking as ever'
    yourself.is_now('proper-named')

    pyif.kind('region')
    pyif.kind('action', create_action)

    man = pyif.kind('man', lambda m: m.is_always('male'), kindof='person')
    woman = pyif.kind('woman', lambda w: w.is_always('female'), kindof='person')
    animal = pyif.kind('animal', kindof='being')

    pyif.kind('device', create_device, kindof='thing')
    pyif.kind('vehicle', create_vehicle, kindof='container')
    pyif.kind('player\'s holdall', create_holdall, kindof='container')

    standard['player'] = Kind.nothing
    standard['location'] = Kind.nothing
    standard['turn count'] = 0
    standard['time of day'] = None
    standard['command prompt'] = '>'

    create_base_rulebooks()
    create_base_actions()
    return standard


#create_standard_rules()