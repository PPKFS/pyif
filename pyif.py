import world


_current_world = None


def current_world():
    """
    Get the current world.
    """

    return _current_world


def make_blank_world():
    """
    Make a blank world and populate it with the standard rules (directions, etc)
    """

    import standard_rules
    return standard_rules.create_standard_rules()


def title(t):
    _current_world.set_title(t)


def default_rule():
    pass


def last_message():
    return _current_world.last_message()


#region Object Creation


def kind(name, properties=None, kindof=None):
    """
    Helper function to make a new kind (class).
    """
    #quick check if it already exists
    if name in _current_world.kinds:
        raise world.AlreadyExistsError('Kind {0} already exists'.format(name))
    if kindof is None:
        kind = world.Kind
    else:
        if kindof not in _current_world.kinds:
            raise world.UnknownKindError('Kind {0} does not exist'.format(kindof))
        kind = _current_world.kinds[kindof]
    #make a fancy init function that appends all the extra creation logic, if needed

    def init(self, n, name_id=False):
        kind.__init__(self, n, name_id)
        if properties is not None:
            properties(self)

    newkind = type(name, (kind,), {'__init__': init})
    _current_world.kinds[name] = newkind
    return newkind


def direction(name, short_name=None):
    """
    Helper function to make a new direction
    """
    dir = make_object(name, 'direction', name_id=True, **({} if short_name is None else {'understand as': short_name}))
    #_current_world.dirs[name] = dir
    return dir


def person(name, *args, **kwargs):
    return make_object(name, 'person', *args, **kwargs)


def room(name, *args, **kwargs):
    """
    Helper function to make a new room. Will parse out map connections.
    """
    #remove the map connections and redo them properly afterwards
    #this ensures they don't get eaten up by the generic property parsing
    map_conns = []
    if 'map_connections' in kwargs:
        map_conns = kwargs['map_connections']
        del kwargs['map_connections']

    if 'description' not in kwargs:
        kwargs['description'] = 'It\'s the ' + name + '.'

    r = make_object(name, 'room', *args, **kwargs)
    #now we remake the connections
    if len(map_conns) > 0:
        make_map_connections(r, map_conns)
    return r


def thing(name, *args, **kwargs):
    return make_object(name, 'thing', *args, **kwargs)


def make_object(name, ty, name_id=False, *args, **kwargs):
    obj = _current_world.kinds[ty](name, name_id)
    for arg in args:
        obj[arg] = True
    for k, v in kwargs.items():
        k = str.replace(k, '_', ' ')
        obj[k] = v
    _current_world.add(obj)
    return obj

#endregion


def make_map_connections(fro, conns):
    """
    bulk-create a dictionary of connections from a room, taking into account reverse relations
    """
    #make sure we have an id
    if type(fro) is not str:
        fro = fro.id
    for dir, to in conns.items():
        if type(to) is not str:
            to = to.id
        if dir[-3:] == '_of':
            #X is south of Y ---> Y has a connection south: X.
            #this implies Y is north of X, but there may be another thing there
            #if there is, ignore it and carry on
            opposite = _current_world.directions[dir[:-3]].opposite
            direction = _current_world.directions[dir[:-3]]
            add_map_connection(to, fro, direction)
            add_map_connection(fro, to, opposite, softly=True)


def add_map_connection(fro, to, direction, softly=False):
    """
    Add a map connection between two rooms.
    If softly=True, it won't override any existing connections made
    """
    if direction.type is 'direction':
        direction = direction.id
    from_room = _current_world[fro]
    to_room = _current_world[to]
    if from_room.type is not 'room' or to_room.type is not 'room':
        raise world.LogicalError('can only make connections between rooms, not between {0} and {1}'
                                 .format(from_room.type, to_room.type))
    if direction in from_room['map connections']:
        if softly:
            world.debug_msg('{0} already has direction {1} going to {2}, softly failing to add {3}'.format(
                from_room.name, direction, _current_world[from_room['map connections'][direction]], to
            ))
            return
        world.debug_msg('connection from {0} to {1} going {2} will overwrite the original destination {3}'
                        .format(from_room.name, to, direction, from_room['map connections'][direction]))

    from_room['map connections'][direction] = to
    world.debug_msg('added connection from {0} ({3}) to {4} ({1}) going {2}'.format(from_room.name, to, direction,
                                                                                    fro, to_room.name))


def add_rulebook(name, default=None):
    if name in _current_world.rulebooks:
        raise world.LogicalError('Rulebook {0} already exists'.format(name))
    rules = world.Rulebook(name, _current_world, default)
    _current_world.add_rulebook(name, rules)
    return rules


def when_play_begins(rule_name='', rule=default_rule, before=False):
    add_rule('when play begins rules', rule_name, rule, before)


def add_rule(rulebook, name, rule, before=False):
    _current_world.add_rule(rulebook, name, rule, before)


def now_player_carries(*args):
    you = _current_world.get_player()
    now_carries(you, *args)


def now_carries(carrier, *args):
    pass


#region Actions
def action(name, understand_as, applies_to=1):
    #make a new action and its three rulebooks
    #action = kind(name, understand_as=understand_as, applies_to=applies_to)
    ac = make_object(name, 'action', True, understand_as=understand_as, applies_to=applies_to)
    ac.before_rules = add_rulebook('before '+name+' rules')
    ch = add_rulebook('check ' + name + ' rules')
    ca = add_rulebook('carry out ' + name + ' rules')
    rep = add_rulebook('report ' + name + ' rules')
    ac.check_rules = ch
    ac.carry_out_rules = ca
    ac.report_rules = rep
    return ac


def try_action(action, nouns=[], **kwargs):
    you = _current_world.get_player()
    actor_try_action(you, action, nouns, **kwargs)


def actor_try_action(actor, action, nouns=[], **kwargs):
    _current_world.try_action(actor, action, nouns, **kwargs)

#endregion


def test_with_actions(actions):
    for i, action in enumerate(actions):
        _current_world.say('TEST {0}: {1}'.format(i, action if type(action) is str else (action[0] + ' ' +
                                                                                         action[1][0].name)))
        _current_world.say('---')
        try_action(action if type(action) is str else action[0], [] if type(action) is str else action[1])

def go():
    _current_world.go()
