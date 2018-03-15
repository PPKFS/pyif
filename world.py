import uuid


class AlreadyExistsError(Exception):
    pass


class UnknownKindError(Exception):
    pass


class LogicalError(Exception):
    pass


class LazyString:
    def __init__(self, string, format_options, story):
        self.string = string
        self.format_options = format_options
        self.story = story

    def __str__(self):
        opts = {name: val(self.story) for name, val in self.format_options.items()}
        return self.string.format(**opts)

    def __add__(self, other):
        return str(self)+other

    def __radd__(self, other):
        return other+str(self)


class Value:
    def __init__(self, ops, **kwargs):
        #keep a dictionary of our options for this value and set them all to false
        self.options = {}
        self.implications = {}
        self.always = None
        self.never = None

        for option in ops:
            self.options[option] = False
        if len(kwargs) == 0:
            return
        if len(kwargs) > 1:
            raise LogicalError('Value with options {0} cannot have more than 1 condition'.format(ops))

        #add on these always/usually qualifiers
        for key, val in kwargs.items():
            if val not in ops and len(ops) > 1:
                raise LogicalError('Value with options {0} cannot be {1}'.format(ops, key))
            #setattr(self, key, val)
            if key == 'usually' or key == 'always':
                self.options[val] = True
            if key == 'always':
                self.is_always(val)

    def set(self, prop, val=True):
        if self.never == prop and val:
            print('raaaa')
        elif self.always is not None and self.always != prop:
            print('bbaaaa')
        if val:
            self.options = {key: (key == prop) for key, p in self.options.items()}
        else:
            self.options[prop] = False
            #set the default being the first
            for default in self.options:
                if default == prop:
                    continue
                if len(self.options) > 2:
                    print('warning, setting a default with multiple choices')
                self.set(default)
                return
        for implication in self.implications:
            #for each implication, if the implication is now true
            if prop == implication and val:
                #print('uh', prop, val)
                self.update_implication(prop)

    def update_implication(self, implied_by):
        for rel, prop, val in self.implications[implied_by]:
            #print('up', rel, prop, val)
            if rel == 'usually':
                prop.is_usually(val)
            elif rel == 'always':
                prop.is_always(val)
            elif rel == 'never':
                #print('here')
                prop.is_never(val)

    def implication(self, if_property, relation, implied_prop, val):
        if if_property not in self.implications:
            self.implications[if_property] = []
        self.implications[if_property].append((relation, implied_prop, val))
        #check if we have it on by default
        if self.options[if_property]:
            self.update_implication(if_property)

    def is_always(self, prop):
        self.always = prop
        self.set(prop)

    def is_never(self, prop):
        self.never = prop
        self.set(prop, False)

    def is_usually(self, prop):
        self.set(prop, True)


def generate_id(name):
    return (name.lower()[:8] if len(name) > 8 else name.lower()).replace(' ', '') + uuid.uuid4().hex[:8]


class Kind:
    def __init__(self, name, name_id=False):
        self._properties = {}
        self.has('name', name)
        self.has('id', name if name_id else generate_id(name))
        self.has('indefinite article', '')
        self.has('understand as', [name])
        self.has('type', type(self).__name__)
        self.can_be(['single-named', 'plural-named'], usually='plural-named')
        self.can_be(['proper-named', 'improper-named'], usually='improper-named')

    def __getitem__(self, key):
        try:
            prop = self._properties[key]
            if isinstance(prop, Value):
                return prop.options[key]
            else:
                return prop
        except KeyError:
            raise LogicalError('{2} (a {0}) doesn\'t have the property {1}'.format(self.type, key, self.name))

    def __setitem__(self, key, val):
        key = key.replace('_', ' ')
        try:
            prop = self._properties[key]
        except KeyError:
            raise LogicalError('{2} (a {0}) doesn\'t have the property {1}'.format(self.type, key, self.name))

        item = prop
        if isinstance(item, Value):
            item.set(key, val)
        else:
            self._properties[key] = val

    def __getattr__(self, name):
        return self[name.replace('_', ' ')]

    def __setattr__(self, key, value):
        if key == '_properties' or key in self.__dict__:
            super(Kind, self).__setattr__(key, value)
        else:
            self[key] = value

    def __str__(self):
        return self.name

    def check_for_property(self, prop):
        return prop in self._properties

    def has(self, prop, usually=None):
        if prop in self._properties:
            raise LogicalError('Kind {0} already has the property {1}'.format(self.name, prop))
        self._properties[prop] = usually

    def can_be(self, options, **kwargs):
        #e.g. can_be('scenery')
        if isinstance(options, str):
            if len(kwargs) > 1:
                raise LogicalError('Kind {0} cannot have multiple qualifiers on the property {1}'.format(self.name, options))
            #make it a regular value and give it an inverse
            #e.g. a thing can be wearable - which automatically makes a 'not wearable' property
            options = [options, 'not ' + options]
            if len(kwargs) > 0:
                kwarg_key = list(kwargs.keys())[0]
                if kwarg_key == 'usually' or kwarg_key == 'always':
                    kwargs[kwarg_key] = options[0] if kwargs[kwarg_key] else options[1]
                elif kwarg_key == 'seldom' or kwarg_key == 'never':
                    kwargs[kwarg_key] = options[1] if kwargs[kwarg_key] else options[0]
                else:
                    raise LogicalError('Value with options {0} cannot be {1}'.format(options, kwarg_key))
            else:
                kwargs['usually'] = options[1]
        value = Value(options, **kwargs)
        for option in options:
            if option in self._properties:
                raise LogicalError('Kind {0} already has the property {1}'.format(self.name, option))
            self._properties[option] = value

    def implication(self, if_property, then):
        #of the form 'if if_property is true, then the properties in then are also true'
        #e.g. scenery is usually fixed in place
        prop = self._properties[if_property]
        for key, val in then.items():
            implied_prop = self._properties[val]
            prop.implication(if_property, key, implied_prop, val)

    def is_now(self, prop):
        p = self._properties[prop]
        p.set(prop)

    def is_always(self, prop):
        p = self._properties[prop]
        p.is_always(prop)

    def is_never(self, prop):
        p = self._properties[prop]
        p.is_never(prop)

    def is_usually(self, prop):
        p = self._properties[prop]
        p.is_usually(prop)


Kind.nothing = Kind('nothing', name_id=True)


_debug = False
DEFAULT = 1
VERBOSE = 2


def debug_msg(*args, **kwargs):
    if not _debug:
        return
    if len(kwargs) == 0:
        kwargs['verbose'] = DEFAULT
    if _debug >= kwargs['verbose']:
        print('DEBUG:', *args)


class World:
    def __init__(self):
        self.kinds = {}
        self.objects = {}
        self.variables = {}
        self.rulebooks = {}
        self.directions = {}
        self.actions = {}
        self.message_log = []
        self.player = None
        self.action_processing = None
        self.first_room_made = None

    def get_ap_rulebook(self):
        if self.action_processing is None:
            self.action_processing = self.rulebooks['action processing rules']
        return self.action_processing

    def get_player(self):
        if self.player is None:
            self.player = self.objects['yourself']
        return self.player

    def things(self):
        for k, v in self.objects.items():
            if v.type == 'thing':
                yield k, v

    def say(self, msg, *args):
        formatted = msg.format(*args)
        print(formatted)
        self.message_log.append(formatted)

    def last_message(self):
        return "" if len(self.message_log) == 0 else self.message_log[-1]

    def go(self):
        self.rulebooks['when play begins rules'].follow()

    def add(self, obj):
        debug_msg('added {0} (a {2}) with id {1}'.format(obj, obj.id, obj.type))
        self.objects[obj.id] = obj
        if obj.type == 'action':
            self.actions[obj.id] = obj
        elif obj.type == 'direction':
            self.directions[obj.id] = obj
        elif obj.type == 'room' and self.first_room_made is None:
            self.first_room_made = obj

    def add_rulebook(self, name, rulebook):
        self.rulebooks[name] = rulebook
        return rulebook

    def add_rule(self, rulebook, name, rule, before=False):
        self.rulebooks[rulebook].add_rule(name, rule, before)

    def move(self, obj, new_loc):
        debug_msg('moved {0} from {1} to {2}'.format(obj.name, obj.location, new_loc))
        obj.location = new_loc

    def __getitem__(self, key):
        try:
            prop = self.variables[key]
            if isinstance(prop, Value):
                return prop.options[key]
            else:
                return prop
        except KeyError:
            return self.objects[key]

    def __setitem__(self, key, val):
        try:
            item = self.variables[key]
            if isinstance(item, Value):
                item[key] = val
            self.variables[key] = val
        except KeyError:
            self.variables[key] = val

    def __getattr__(self, name):
        return self[name.replace('_', ' ')]

    def set_title(self, title):
        self['title'] = title

    def try_action(self, actor, action, nouns=[]):
        debug_msg('{0} is trying to do {1}'.format('the player' if actor.name == 'yourself' else actor.name, action))
        #print(nouns)
        outcome = self.get_ap_rulebook().follow(actor=actor, action=self.actions[action], nouns=nouns)
        if outcome is not None:
            debug_msg('outcome of {0} trying to do {1} is {2}'.format('the player' if actor.name == 'yourself' else
                                                                   actor.name, action, outcome))
        debug_msg('{0} has finished trying to perform the action {1}'.format('the player' if actor.name == 'yourself'
                                                                            else actor.name, action))
        return outcome


class Rule:
    def __init__(self, name, rule):
        self.name = name
        self.rule = rule

    def evaluate(self, story, **kwargs):
        return self.rule(story, **kwargs)


class Rulebook:

    def __init__(self, name, world, default_outcome=None):
        self.name = name
        self.default_outcome = default_outcome
        self.first_rules = []
        self.rules = []
        self.last_rules = []
        self.variables = {}
        self.world = world

    def __getitem__(self, key):
        if key.endswith(' rule'):
            return self.get_rule(key)
        prop = self.variables[key]
        if isinstance(prop, Value):
            return prop.options[key]
        else:
            return prop

    def __setitem__(self, key, val):
        if key.endswith(' rule'):
            self.add_rule(key)
            return
        try:
            item = self.variables[key]
            if isinstance(item, Value):
                item[key] = val
            self.variables[key] = val
        except KeyError:
            self.variables[key] = val

    def get_rule(self, rule):
        rule = next((x for x in self.first_rules if x.name == rule), None)
        if rule is None:
            rule = next((x for x in self.rules if x.name == rule), None)
            if rule is None:
                rule = next((x for x in self.rules if x.name == rule), None)
                if rule is None:
                    raise KeyError('rule {0} not found in rulebook {1}'.format(rule, self.name))

    def add_rule(self, name, func=None, before=False):
        self._add(name, func, self.rules, before)

    def _add(self, name, func, rulebook, before):
        if func is not None:
            name = Rule(name, func)
        if type(name) is str and func is None:
            name = Rule(name, lambda s: debug_msg('not implemented {0}'.format(name.name), verbose=VERBOSE))
        debug_msg('added rule {0}'.format(name.name))
        if before:
            rulebook.insert(0, name)
        else:
            rulebook.append(name)

    def add_rule_first(self, name, func=None, before=False):
        self._add(name, func, self.first_rules, before)

    def add_rule_last(self, name, func=None, before=False):
        self._add(name, func, self.last_rules, before)

    def follow(self, **kwargs):
        debug_msg('following the {0} rulebook'.format(self.name))
        #print(kwargs)
        res = self._follow_ruleset(self.first_rules, **kwargs)
        if res is None:
            res = self._follow_ruleset(self.rules, **kwargs)
            if res is None:
                res = self._follow_ruleset(self.last_rules, **kwargs)
        debug_msg('finished following the {0} rulebook'.format(self.name))
        return res

    def _follow_ruleset(self, ruleset, **kwargs):
        for rule in ruleset:
            #debug_msg('following \'{0}\' rule in {1} rulebook'.format(rule.name, self.name))
            #print('following ' + rule.name)
            try:
                result = rule.evaluate(self.world, **kwargs)
            except TypeError as e:
                #print(rule.name, e)
                result = rule.evaluate(self.world)
            if result is None:
                continue
            else:
                debug_msg('Rule outcome for \'{1}\' was {0}'.format(result, rule.name))
                return result
        return None


'''
    def say(self, msg, args):
        def multiple_replace(d, text):
            # Create a regular expression  from the dictionary keys
            regex = re.compile("(%s)" % "|".join(map(re.escape, d.keys())))

            # For each match, look-up corresponding value in dictionary
            return regex.sub(lambda mo: d[mo.string[mo.start():mo.end()]], text)
        if len(args) > 0:
            update_args = {}
            for arg in args:
                update_args['['+arg+']'] = args[arg].name
            new_msg = multiple_replace(update_args, msg)
        else:
            new_msg = msg
        print(new_msg)
        self.msg_log.append(new_msg)

    def last_message(self):
        return self.msg_log[-1]

    def set_title(self, t):
        self.title = t

    def section(self, num, name, release=True):
        self.sections[num] = (name, release)
        self.current['section'] = num

    def add_rulebook(self, rulebook):
        self.rulebooks[rulebook.name] = rulebook

    def add_rule(self, rulebook_name, rule_name, rule):
        rulebook = self.rulebooks[rulebook_name]
        rulebook.add_rule(rule_name, rule)

    def when_play_begins(self, rule_name='', rule=default_rule):
        self.add_rule(_WHEN_PLAY_BEGINS, rule_name, rule)

    def object(self, name, kind):
        id = generate_id(name)
        debug_msg('made a {0} called {1} ({2})'.format(kind, name, id))
        self.current[kind] = id
        return id

    def thing(self, name, **kwargs):
        id = self.object(name, 'thing')
        self.things[id] = Thing(name, **kwargs)
        return self.things[id]

    def room(self, name, **kwargs):
        id = self.object(name, 'room')
        self.rooms[id] = Room(name, **kwargs)
        return self.rooms[id]

    def player_carries(self, *args):
        pass

    def go(self):
        self._when_play_begins_rulebook.follow(self)
    '''