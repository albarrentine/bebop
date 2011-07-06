'''
Created on Jan 19, 2011

@author: al
'''

from lxml import etree
from lxml import builder
from lxml import objectify
from collections import defaultdict, deque, MutableSet
import os
import inspect
from UserDict import DictMixin

try:
    from thread import get_ident as _get_ident
except ImportError:
    from dummy_thread import get_ident as _get_ident

try:
    from _abcoll import KeysView, ValuesView, ItemsView
except ImportError:
    pass


__E = objectify.ElementMaker(annotate=False)

# Simple class to replace None default arguments, inspired by WebHelpers
class NotGiven:
    pass

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)


def memoize(f):
    arg_cache = {}
    def _new_f(arg):
        cache_it = True
        try:
            cached = arg_cache.get(arg, None)
            if cached is not None:
                return cached
        except TypeError:
            cache_it = False
        uncached = f(arg)
        if cache_it:
            arg_cache[arg] = uncached
        return uncached
    return _new_f

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def to_camelcase(s):
    return ''.join([token.title() if i > 0 else token.lower()
                    for i, token in enumerate(s.split('_'))])

def join_with_separator(separators, param, separator):
    separators[param] = separator
    def _with_func(f):
        return f
    return _with_func

@memoize
def _stringify(obj):
    # TODO: write your own PyObject > string conversion
    # or find a better way to do this
    return __E._dummy_node(obj).text

def _sorted_update(elem, d):
    elem.attrib.update(sorted(d.iteritems()))

def get_class(obj):
    if inspect.isclass(obj):
        return obj
    else:
        return obj.__class__

def _collect_dependencies(obj, deps=defaultdict(set), refs=defaultdict(int)):
    for attr, value in obj.__dict__.iteritems():
        # Dependencies are XML orderings, so we don't care about non-XMLable attributes
        if hasattr(value, 'dependency'):
            # deps[SolrFieldTypes]=set(UniqueKey('foo'))
            deps[get_class(value.dependency)].add(value)
            # ref_counts[elem]==1 means that elem is waiting on 1 node to complete
            refs[value]+=1

        if hasattr(value, 'to_xml'):
            deps, refs = _collect_dependencies(value, deps, refs)
        elif hasattr(value, '__iter__') and hasattr(iter(value).next(), 'to_xml'):
            for val in value:
                deps, refs = _collect_dependencies(val, deps, refs)

    return deps, refs

def _to_xml(node):
    root=None
    # Topsort: schedule items with no dependers
    # Queue items are a tuple of (obj, parent)
    q=deque([(node, None)])
    dependency_graph, ref_counts = _collect_dependencies(node)

    #[q.append((value,node)) for value in node.__dict__.itervalues() if hasattr(value, 'to_xml') and ref_counts[value] == 0]

    while q:
        obj, parent = q.popleft()

        element = etree.Element(obj.tag)
        if obj is node:
            root=element

        definitions = {}
        options = {}
        for attr, transformed in obj.required.iteritems():
            definitions[transformed] = _stringify(getattr(obj, attr))

        for attr, value in obj.__dict__.iteritems():
            if attr in obj.required:
                definitions[obj.required[attr]] = _stringify(value)
            elif attr in obj.optional:
                options[obj.optional[attr]] = _stringify(value)
            elif attr=='value':
                element.text=_stringify(value)
            # For referencing elements without throwing them in the schema, use an underscore
            elif attr.startswith('_'):
                continue
            # Append children (recursive, but we don't need many levels)
            elif hasattr(value, 'to_xml') and not hasattr(value, 'dependency'):
                q.append((value, element))
            # Example: filters
            # TODO: are there any use cases where this is not the expected behavior?
            elif hasattr(value, '__iter__'):
                i = iter(value)
                first = i.next()
                del(i)
                if hasattr(first, 'to_xml') and not hasattr(value, 'dependency'):
                    #parent_node = parent if hasattr(first, 'dependency') else element
                    q.extend([(child, element) for child in value])


        _sorted_update(element, definitions)
        _sorted_update(element, options)



        cls = get_class(obj)
        if cls in dependency_graph:
            for dep in dependency_graph[cls]:
                ref_counts[dep]-=1
                if ref_counts[dep]==0:
                    q.appendleft((dep, parent))
            del(dependency_graph[cls])

        if parent is not None:
            parent.append(element)



    return root

class BaseSolrXMLElement(object):
    required = {}
    options = []
    tag = None
    ref_count = 0

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

        # So class.to_xml will call _to_xml(cls) and self.to_xml will call _to_xml(self)
        self.to_xml = self.instance_to_xml

    def instance_to_xml(self):
        return _to_xml(self)


    @classmethod
    def to_xml(cls):
        return _to_xml(cls)


    @classproperty
    @classmethod
    def optional(cls):
        return dict([(attr, to_camelcase(attr))
                     for attr in cls.options])

def single_value_tag(tag, value):
    return BaseSolrXMLElement(tag=tag, value=value)

class SingleValueTagsMixin(BaseSolrXMLElement):
    def __init__(self, camelcase=True, **kw):
        for attr, val in kw.iteritems():
            if val is NotGiven:
                continue
            if hasattr(val, 'to_xml'):
                # Ignore XML elements so they can be mixed in freely
                setattr(self, attr, val)
                continue

            tag = to_camelcase(attr) if camelcase else attr
            element = single_value_tag(tag, val)
            setattr(self, attr, element)

        super(SingleValueTagsMixin, self).__init__()

class NamedSingleValueTagsMixin(SingleValueTagsMixin):
    def __init__(self, **kw):
        for attr, value in kw.iteritems():
            value.name = attr
        super(NamedSingleValueTagsMixin, self).__init__(**kw)


# OrderedSet, generally useful collection

KEY, PREV, NEXT = range(3)

class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[PREV]
            curr[NEXT] = end[PREV] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[NEXT] = next
            next[PREV] = prev

    def __iter__(self):
        end = self.end
        curr = end[NEXT]
        while curr is not end:
            yield curr[KEY]
            curr = curr[NEXT]

    def __reversed__(self):
        end = self.end
        curr = end[PREV]
        while curr is not end:
            yield curr[KEY]
            curr = curr[PREV]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = next(reversed(self)) if last else next(iter(self))
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def __del__(self):
        self.clear()                    # remove circular references



# Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
# Passes Python2.7's test suite and incorporates all the latest updates.

class OrderedDict(dict):
    'Dictionary that remembers insertion order'
    # An inherited dict maps keys to values.
    # The inherited dict provides __getitem__, __len__, __contains__, and get.
    # The remaining methods are order-aware.
    # Big-O running times for all methods are the same as for regular dictionaries.

    # The internal self.__map dictionary maps keys to links in a doubly linked list.
    # The circular doubly linked list starts and ends with a sentinel element.
    # The sentinel element never gets deleted (this simplifies the algorithm).
    # Each link is stored as a list of length three:  [PREV, NEXT, KEY].

    def __init__(self, *args, **kwds):
        '''Initialize an ordered dictionary.  Signature is the same as for
        regular dictionaries, but keyword arguments are not recommended
        because their insertion order is arbitrary.

        '''
        if len(args) > 1:
            raise TypeError('expected at most 1 arguments, got %d' % len(args))
        try:
            self.__root
        except AttributeError:
            self.__root = root = []                     # sentinel node
            root[:] = [root, root, None]
            self.__map = {}
        self.__update(*args, **kwds)

    def __setitem__(self, key, value, dict_setitem=dict.__setitem__):
        'od.__setitem__(i, y) <==> od[i]=y'
        # Setting a new item creates a new link which goes at the end of the linked
        # list, and the inherited dictionary is updated with the new key/value pair.
        if key not in self:
            root = self.__root
            last = root[0]
            last[1] = root[0] = self.__map[key] = [last, root, key]
        dict_setitem(self, key, value)

    def __delitem__(self, key, dict_delitem=dict.__delitem__):
        'od.__delitem__(y) <==> del od[y]'
        # Deleting an existing item uses self.__map to find the link which is
        # then removed by updating the links in the predecessor and successor nodes.
        dict_delitem(self, key)
        link_prev, link_next, key = self.__map.pop(key)
        link_prev[1] = link_next
        link_next[0] = link_prev

    def __iter__(self):
        'od.__iter__() <==> iter(od)'
        root = self.__root
        curr = root[1]
        while curr is not root:
            yield curr[2]
            curr = curr[1]

    def __reversed__(self):
        'od.__reversed__() <==> reversed(od)'
        root = self.__root
        curr = root[0]
        while curr is not root:
            yield curr[2]
            curr = curr[0]

    def clear(self):
        'od.clear() -> None.  Remove all items from od.'
        try:
            for node in self.__map.itervalues():
                del node[:]
            root = self.__root
            root[:] = [root, root, None]
            self.__map.clear()
        except AttributeError:
            pass
        dict.clear(self)

    def popitem(self, last=True):
        '''od.popitem() -> (k, v), return and remove a (key, value) pair.
        Pairs are returned in LIFO order if last is true or FIFO order if false.

        '''
        if not self:
            raise KeyError('dictionary is empty')
        root = self.__root
        if last:
            link = root[0]
            link_prev = link[0]
            link_prev[1] = root
            root[0] = link_prev
        else:
            link = root[1]
            link_next = link[1]
            root[1] = link_next
            link_next[0] = root
        key = link[2]
        del self.__map[key]
        value = dict.pop(self, key)
        return key, value

    # -- the following methods do not depend on the internal structure --

    def keys(self):
        'od.keys() -> list of keys in od'
        return list(self)

    def values(self):
        'od.values() -> list of values in od'
        return [self[key] for key in self]

    def items(self):
        'od.items() -> list of (key, value) pairs in od'
        return [(key, self[key]) for key in self]

    def iterkeys(self):
        'od.iterkeys() -> an iterator over the keys in od'
        return iter(self)

    def itervalues(self):
        'od.itervalues -> an iterator over the values in od'
        for k in self:
            yield self[k]

    def iteritems(self):
        'od.iteritems -> an iterator over the (key, value) items in od'
        for k in self:
            yield (k, self[k])

    def update(*args, **kwds):
        '''od.update(E, **F) -> None.  Update od from dict/iterable E and F.

        If E is a dict instance, does:           for k in E: od[k] = E[k]
        If E has a .keys() method, does:         for k in E.keys(): od[k] = E[k]
        Or if E is an iterable of items, does:   for k, v in E: od[k] = v
        In either case, this is followed by:     for k, v in F.items(): od[k] = v

        '''
        if len(args) > 2:
            raise TypeError('update() takes at most 2 positional '
                            'arguments (%d given)' % (len(args),))
        elif not args:
            raise TypeError('update() takes at least 1 argument (0 given)')
        self = args[0]
        # Make progressively weaker assumptions about "other"
        other = ()
        if len(args) == 2:
            other = args[1]
        if isinstance(other, dict):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, 'keys'):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value
        for key, value in kwds.items():
            self[key] = value

    __update = update  # let subclasses override update without breaking __init__

    __marker = object()

    def pop(self, key, default=__marker):
        '''od.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised.

        '''
        if key in self:
            result = self[key]
            del self[key]
            return result
        if default is self.__marker:
            raise KeyError(key)
        return default

    def setdefault(self, key, default=None):
        'od.setdefault(k[,d]) -> od.get(k,d), also set od[k]=d if k not in od'
        if key in self:
            return self[key]
        self[key] = default
        return default

    def __repr__(self, _repr_running={}):
        'od.__repr__() <==> repr(od)'
        call_key = id(self), _get_ident()
        if call_key in _repr_running:
            return '...'
        _repr_running[call_key] = 1
        try:
            if not self:
                return '%s()' % (self.__class__.__name__,)
            return '%s(%r)' % (self.__class__.__name__, self.items())
        finally:
            del _repr_running[call_key]

    def __reduce__(self):
        'Return state information for pickling'
        items = [[k, self[k]] for k in self]
        inst_dict = vars(self).copy()
        for k in vars(OrderedDict()):
            inst_dict.pop(k, None)
        if inst_dict:
            return (self.__class__, (items,), inst_dict)
        return self.__class__, (items,)

    def copy(self):
        'od.copy() -> a shallow copy of od'
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, iterable, value=None):
        '''OD.fromkeys(S[, v]) -> New ordered dictionary with keys from S
        and values equal to v (which defaults to None).

        '''
        d = cls()
        for key in iterable:
            d[key] = value
        return d

    def __eq__(self, other):
        '''od.__eq__(y) <==> od==y.  Comparison to another OD is order-sensitive
        while comparison to a regular mapping is order-insensitive.

        '''
        if isinstance(other, OrderedDict):
            return len(self)==len(other) and self.items() == other.items()
        return dict.__eq__(self, other)

    def __ne__(self, other):
        return not self == other

    # -- the following methods are only used in Python 2.7 --

    def viewkeys(self):
        "od.viewkeys() -> a set-like object providing a view on od's keys"
        return KeysView(self)

    def viewvalues(self):
        "od.viewvalues() -> an object providing a view on od's values"
        return ValuesView(self)

    def viewitems(self):
        "od.viewitems() -> a set-like object providing a view on od's items"
        return ItemsView(self)

# Copied from paste.util.multidict
class MultiDict(DictMixin):
    """
    An ordered dictionary that can have multiple values for each key.
    Adds the methods getall, getone, mixed, and add to the normal
    dictionary interface.
    """

    def __init__(self, *args, **kw):
        if len(args) > 1:
            raise TypeError(
                "MultiDict can only be called with one positional argument")
        if args:
            if hasattr(args[0], 'iteritems'):
                items = list(args[0].iteritems())
            elif hasattr(args[0], 'items'):
                items = args[0].items()
            else:
                items = list(args[0])
            self._items = items
        else:
            self._items = []
        self._items.extend(kw.iteritems())

    def __getitem__(self, key):
        for k, v in self._items:
            if k == key:
                return v
        raise KeyError(repr(key))

    def __setitem__(self, key, value):
        try:
            del self[key]
        except KeyError:
            pass
        self._items.append((key, value))

    def add(self, key, value):
        """
        Add the key and value, not overwriting any previous value.
        """
        self._items.append((key, value))

    def getall(self, key):
        """
        Return a list of all values matching the key (may be an empty list)
        """
        result = []
        for k, v in self._items:
            if key == k:
                result.append(v)
        return result

    def getone(self, key):
        """
        Get one value matching the key, raising a KeyError if multiple
        values were found.
        """
        v = self.getall(key)
        if not v:
            raise KeyError('Key not found: %r' % key)
        if len(v) > 1:
            raise KeyError('Multiple values match %r: %r' % (key, v))
        return v[0]

    def mixed(self):
        """
        Returns a dictionary where the values are either single
        values, or a list of values when a key/value appears more than
        once in this dictionary.  This is similar to the kind of
        dictionary often used to represent the variables in a web
        request.
        """
        result = {}
        multi = {}
        for key, value in self._items:
            if key in result:
                # We do this to not clobber any lists that are
                # *actual* values in this dictionary:
                if key in multi:
                    result[key].append(value)
                else:
                    result[key] = [result[key], value]
                    multi[key] = None
            else:
                result[key] = value
        return result

    def dict_of_lists(self):
        """
        Returns a dictionary where each key is associated with a
        list of values.
        """
        result = {}
        for key, value in self._items:
            if key in result:
                result[key].append(value)
            else:
                result[key] = [value]
        return result

    def __delitem__(self, key):
        items = self._items
        found = False
        for i in range(len(items)-1, -1, -1):
            if items[i][0] == key:
                del items[i]
                found = True
        if not found:
            raise KeyError(repr(key))

    def __contains__(self, key):
        for k, v in self._items:
            if k == key:
                return True
        return False

    has_key = __contains__

    def clear(self):
        self._items = []

    def copy(self):
        return MultiDict(self)

    def setdefault(self, key, default=None):
        for k, v in self._items:
            if key == k:
                return v
        self._items.append((key, default))
        return default

    def pop(self, key, *args):
        if len(args) > 1:
            raise TypeError, "pop expected at most 2 arguments, got "\
                              + repr(1 + len(args))
        for i in range(len(self._items)):
            if self._items[i][0] == key:
                v = self._items[i][1]
                del self._items[i]
                return v
        if args:
            return args[0]
        else:
            raise KeyError(repr(key))

    def popitem(self):
        return self._items.pop()

    def update(self, other=None, **kwargs):
        if other is None:
            pass
        elif hasattr(other, 'items'):
            self._items.extend(other.items())
        elif hasattr(other, 'keys'):
            for k in other.keys():
                self._items.append((k, other[k]))
        else:
            for k, v in other:
                self._items.append((k, v))
        if kwargs:
            self.update(kwargs)

    def __repr__(self):
        items = ', '.join(['(%r, %r)' % v for v in self._items])
        return '%s([%s])' % (self.__class__.__name__, items)

    def __len__(self):
        return len(self._items)

    ##
    ## All the iteration:
    ##

    def keys(self):
        return [k for k, v in self._items]

    def iterkeys(self):
        for k, v in self._items:
            yield k

    __iter__ = iterkeys

    def items(self):
        return self._items[:]

    def iteritems(self):
        return iter(self._items)

    def values(self):
        return [v for k, v in self._items]

    def itervalues(self):
        for k, v in self._items:
            yield v