import csv
import io
from collections import OrderedDict
from inspect import signature
from typing import Dict, Any, Optional, Union, Callable, Tuple, List

# A dynamic entry value can be:
#   1) A function:      f() -> object
#   2) A method:        f(self) -> object
#   3) A simple object
#   4) None

DynEntryValue = Optional[Union[Callable[[], object], Callable[[object], object], object]]

# Set this to 'True' to debug possible settings of '_var' when it should be 'var'
warn_mode = True

dynprops_dialect = 'DynProps'


def _register_dynprops_dialect(sep: Optional[str]=None) -> None:
    if sep is None:
        sep = '\t'
    elif len(sep) != 1:
        raise ValueError("Separator must be a single charactor")
    if dynprops_dialect in csv.list_dialects():
        csv.unregister_dialect(dynprops_dialect)
    # noinspection PyTypeChecker
    csv.register_dialect(dynprops_dialect, csv.excel_tab, delimiter=sep, lineterminator="")


class DynEntry:
    def __init__(self, type_: type, is_global: bool=False, default_value: DynEntryValue=None):
        """ Dynamic property entry

        :param type_: Property type -- will be used in the future for type checking
        :param is_global: True means preperty is a singleton. False is class or instance level
        :param default_value: Default value if not overridden
        """
        self.type = type_
        self.is_global = is_global
        self.default_value = default_value


# Property name and associated property
# key parents_key - insert parent elements here
#     ordered_dict_token - ignore - used to fix an issue in OrderedDict
DynEntries = Dict[str, Optional[DynEntry]]
parents_key = ""


# Global - identifies an element as a singleton
class _Global:
    def __getitem__(self, arg: type) -> DynEntry:
        return DynEntry(arg, True)


# A Local property can be set on the class or instance level
class _Local:
    def __getitem__(self, arg: type) -> DynEntry:
        return DynEntry(arg, False)


Local = _Local()
Global = _Global()


# Parent indicates where inherited properties appear.  If omitted they appear at the end
class Parent:
    pass


class DynPropsMeta(type):
    """ Class level attributes and methods for DynProps class """

    def __new__(mcs, typename: str, bases: Tuple, ns: Dict):
        """ Don't add attributes for dynamic properties """

        special_things: List[str] = [k for k, v in ns['__annotations__'].items() if isinstance(v, DynEntry)] \
            if '__annotations__' in ns else []

        # __annotations__ are NOT inherited here so we need to look back to find the parent's DynEntries
        if len(bases) > 0 and isinstance(bases[0], DynPropsMeta):
            special_things += bases[0]._keys
        base_ns = {k: v for k, v in ns.items() if k not in special_things}
        return type.__new__(mcs, typename, bases, base_ns)

    def __init__(cls, cls_name: str, args, kwargs) -> None:
        """ Convert the property definitions into actual attributes on thc class level """

        # There is an obscure issue with OrderedDict identity -- for some reason we have to add
        # a unique value to the dictionary for it to achieve self awareness
        cls._props = OrderedDict()
        cls._dyn_parent: DynProps = cls.__mro__[1] if getattr(cls.__mro__[1], '_props', None) is not None else None
        cls._keys = []

        # Set up all of the dynamic property entries
        cls._xfer_annotations(kwargs)

        # Add any class level definitions as the default values
        for k, v in list(kwargs.items()):
            if k in cls._props:
                cls._props[k].default_value = v
                del kwargs[k]

        cls._clear()                # Propagate defaults to actual values
        super().__init__(cls_name, args, kwargs)

    @property
    def _separator(cls) -> Optional[str]:
        return None

    @_separator.setter
    def _separator(cls, sep):
        _register_dynprops_dialect(sep)
        cls._csv_writer = csv.writer(cls._io_stream, dialect=dynprops_dialect)

    def _xfer_annotations(cls, kwargs: Dict) -> None:
        """ Create the DynEntries list from the type (and possibly) values """

        proplist = OrderedDict()
        proplist[parents_key] = None             # Parent properties got at the top by default

        # Note that annotations are inherited
        for k, v in cls.__annotations__.items():
            if isinstance(v, DynEntry):
                proplist[k] = DynEntry(v.type, False, v.default_value) if not v.is_global else v
            elif v is Parent:                   # Explicitly declared parent
                assert cls._dyn_parent, "No parent exists"
                del proplist[parents_key]
                proplist[parents_key] = None

        # Merge with the parent DynEntries
        for k, v in proplist.items():
            cls._props[k] = v
            if k == parents_key:
                for parent_key in getattr(cls._dyn_parent, '_keys', []):
                    if parent_key in kwargs and cls._dyn_parent._get_prop(parent_key).is_global:
                        raise AttributeError(f"{parent_key} must be set on the base level")
                    if parent_key not in proplist:
                        cls._keys.append(parent_key)
            else:
                cls._keys.append(k)

    def _get_prop(self, item) -> Optional[DynEntry]:
        """ A '_' suffix on a dynobject means that you want to bypass reification """
        return self._props[item] if item in self._props else \
            self._props[item[:-1]] if item[:-1] in self._props else \
            self._dyn_parent._get_prop(item) if self._dyn_parent else None

    def __setattr__(self, key, value):
        """ There is only one attribute -- setting does not override it """
        if key in self._props:
            return super().__setattr__('_' + key, value)           # Super because of line below
        elif key.startswith('_') and self._get_prop(key[1:]):
            raise ValueError(f"{key} is not settable - use {key[1:]} instead")
        p = self._get_prop(key)
        if p:
            # Parent property
            if p.is_global:
                raise ValueError(f"{key} can only be set at declaring class level")
            else:
                super().__setattr__('_' + key, value)
        else:
            super().__setattr__(key, value)

    def __getattr__(self, item):
        if item in self._props:
            att = super().__getattribute__('_' + item)
            att_parms = list(signature(att).parameters) if callable(att) else []
            return att(self) if len(att_parms) == 1 and 'self' in att_parms else att() \
                if callable(att) else att.reify() if getattr(att, 'reify', None) else att
        return getattr(self._dyn_parent, item) if self._get_prop(item) else super().__getattribute__(item)


class DynProps(metaclass=DynPropsMeta):
    """ Dynamic Properties base class
    """
    _sql_string_delimiter: str = '"'
    _sql_string_delimiter_escape: str = r'\"'    # Change to double quote for Oracle
    _sql_null_text: str = ""                     # Null value representation

    _io_stream = io.StringIO()
    # noinspection PyTypeChecker
    _register_dynprops_dialect()
    _csv_writer = csv.writer(_io_stream, dialect=dynprops_dialect)

    _props: DynEntries = OrderedDict()          # Names of represented elements
    _keys: List[str] = []
    _dyn_parent: Optional["DynProps"] = None    # Parent

    @classmethod
    def _head(cls) -> str:
        """ Return a tsv/csv header """
        cls._io_stream.seek(0)
        cls._io_stream.truncate(0)
        cls._csv_writer.writerow(cls._keys)
        return cls._io_stream.getvalue()

    def _freeze(self) -> Dict[str, object]:
        """ Return an ordered dictionary of key/value tuples

        :return: OrderedDict
        """
        rval = OrderedDict()
        for k in self._keys:
            v = self.__getattr__(k)
            rval[k] = v.reify() if getattr(v, 'reify', None) else v
        return rval

    @classmethod
    def _clear(cls) -> None:
        """ Reset all properties back to their null (None) value """
        for k, v in cls._props.items():
            if k != parents_key:
                if v.default_value is not None or not cls._dyn_parent or k not in cls._dyn_parent._keys:
                    setattr(cls, k, v.default_value)

    # TODO: Escape the separators and any other noise (can we use SQL escape here?)
    @classmethod
    def _escape(cls, txt: str) -> str:
        """ Escape txt for inclusion in SQL delimited text

        :param txt: text to escape
        :return: escaped text
        """
        return txt.replace(cls._sql_string_delimiter, cls._sql_string_delimiter_escape)

    def __str__(self) -> str:
        obj_val = ', '.join([f"{k}:'{v}'" for k, v in self._freeze().items()])
        return f"{self.__class__.__name__}({obj_val})"

    def _delimited(self) -> str:
        """ Return a delimited representation of the object """
        self._io_stream.seek(0)
        self._io_stream.truncate(0)
        self._csv_writer.writerow(self._freeze().values())
        return self._io_stream.getvalue()

    def __lt__(self, other: "DynProps") -> bool:
        if not isinstance(other, DynProps):
            return NotImplemented
        return self._delimited() < other._delimited()

    def __eq__(self, other: "DynProps") -> bool:
        if not isinstance(other, DynProps):
            return NotImplemented
        return self._delimited() == other._delimited()

    def __getattr__(self, item: str) -> Any:
        """ Class properties are actually carried with '_' prefix """
        p = self.__class__._get_prop(item)
        if p:
            if p.is_global:
                return getattr(self.__class__, item)
            else:
                no_reify = item.endswith('_')
                if no_reify:
                    item = item[:-1]
                att = super().__getattribute__('_'+item)
                att_parms = list(signature(att).parameters) if callable(att) else []
                return att(self) if len(att_parms) == 1 and 'self' in att_parms else att() \
                    if callable(att) else att.reify() if getattr(att, 'reify', None) and not no_reify else att
        return super().__getattribute__(item)

    def __setattr__(self, key, value) -> None:
        """ Do not allow class level properties to be set on the instance level

        :param key: property to set
        :param value: value
        """
        p = self.__class__._get_prop(key[1:] if key.startswith('_') else key)
        if p:
            if key.startswith('_') and warn_mode:
                print(f"Issue setting {key}?")
            if p.is_global:
                raise ValueError(f"{key} is a class only property")
            else:
                super().__setattr__(('' if key.startswith('_') else '_')+key, value)
        else:
            super().__setattr__(key, value)


def sql_string_delimiter_esc(esc: Optional[str] = None) -> str:
    """ Get or set the SQL string delimiter escape code """
    rval = DynProps._sql_string_delimiter_escape
    if esc is not None:
        DynProps._sql_string_delimiter_escape = esc
    return rval


def clear(cls: type(DynProps)) -> None:
    cls._clear()


def heading(cls: type(DynProps)) -> str:
    """ Return the tsv/csv heading for cls """
    return cls._head()


def as_dict(inst: DynProps) -> Dict[str, object]:
    """ Return the dictionary representation of inst """
    return inst._freeze()


def row(inst: DynProps) -> str:
    """ Return the tsv/csv representation of inst """
    return inst._delimited()
