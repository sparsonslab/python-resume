from __future__ import annotations # To allow type hints on Quantity


import numbers


class Quantity:
    """ A quantity - i.e. a value with dimensional units.

    Allows basic math (addition, multiplication, exponentiation) with
    quantities, whilst units are calculated automatically.

    In general, a unit can be represented as,
    (10^n x u)^p
    where,
    n: int | str
        The unit's prefix (exponent or equivalent milli/micro, etc).
        see Quantity.UNIT_PREFIXS.
    u: str
        The unit name.
    p: number
        The unit's dimensional exponent.
        3 for cubed, -1 for inverse, etc.

    For example a cubic centimeter has (n, u, p) = (-2, 'm', 3)

    Attributes
    ----------
    value: number | numpy.ndarray
        The value.
    units: ((n, u, p), ...)
        The units.
    base_units: {u: p, ....}
        The base SI units - i.e. where u = kg, s or m.
    multiplier: number
        The base-ten exponent applied to convert self.value into base units.
        i.e. value(base_units) = value(units) x 10^multiplier
    """
    # -------------------------------------------------------------------------
    # Look-up values.
    # -------------------------------------------------------------------------

    DERIVED_UNITS = {
        "Pa": ((0, "kg", 1), (0, "m", -1), (0, "s", -2)),
        # Electrical
        "Ohm": ((0, "kg", 1), (0, "m", 2), (0, "s", -3), (0, "A", -2)),
        "S": ((0, "kg", -1), (0, "m", -2), (0, "s", 3), (0, "A", 2)),
        "V": ((0, "kg", 1), (0, "m", 2), (0, "s", -3), (0, "A", -1)),
        "F": ((0, "kg", -1), (0, "m", -2), (0, "s", 4), (0, "A", 2)),
        "C": ((0, "s", 1), (0, "A", 1)),
        # Energy, force, etc.
        'J': ((0, "kg", 1), (0, "m", 2), (0, "s", -2)),
        "N": ((0, 'kg', 1), (0, 'm', 1), (0, 's', -2)),
        "W": ((0, "kg", 1), (0, "m", 2), (0, "s", -3)),
        # Non-compound
        "L": ((-1, "m", 3),),
        "g": ((-3, 'kg', 1),),
        "Hz": ((0, "s", -1),),
    }

    UNIT_PREFIXS = {
        'a': -18,
        'f': -15,
        'p': -12,
        'n': -9,
        'mu': -6,
        'm': -3,
        'c': -2,
        'd': -1,
        'da': 1,
        'h': 2,
        'k': 3,
        'M': 6,
        'G': 9,
        'T': 12,
        'P': 15
    }

    # -------------------------------------------------------------------------
    # Construction
    # -------------------------------------------------------------------------

    def __init__(self, value, *units):
        self.value = value
        self.units = [self._normalize_unit(unit) for unit in units]
        self.multiplier, self.base_units = Quantity.base_units(*self.units)

    def _normalize_unit(self, unit):
        """ Normalise a unit argument into (exponent, name, dimension) tuple.
        """
        def types_match(values, types):
            if len(values) != len(types):
                return False
            return all([isinstance(v, t) for v, t in zip(values, types)])

        def try_number(value):
            try:
                return int(value)
            except ValueError:
                pass
            try:
                return float(value)
            except ValueError:
                pass
            return value

        # Just the unit name or a period-delimited unit.
        if isinstance(unit, str):
            if "," in unit:
                split_unit = [try_number(p) for p in unit.split(",")]
                return self._normalize_unit(tuple(split_unit))
            return 0, unit, 1
        # The name and dimension
        if types_match(unit, [str, numbers.Real]):
            return 0, unit[0], unit[1]
        # The exponent and name ...
        if types_match(unit, [int, str]):
            return unit[0], unit[1], 1
        if types_match(unit, [str, str]):
            return unit[0], unit[1], 1
        # Full specification ...
        if types_match(unit, [int, str, numbers.Real]):
            return unit
        if types_match(unit, [str, str, numbers.Real]):
            return unit

        raise ValueError(f"{unit} is not a correct unit argument.")

    @property
    def base_value(self) -> float:
        """ The quantity's value in base SI units.
        """
        return self.value * 10 ** self.multiplier

    @staticmethod
    def tuple_base_units(base_units):
        return [(0, u, p) for u, p in base_units.items()]

    def tupled_base_units(self):
        return [(0, u, p) for u, p in self.base_units.items()]

    # -------------------------------------------------------------------------
    # Unit conversion
    # -------------------------------------------------------------------------

    def commensurable(self, other: Quantity) -> bool:
        """ The quantity is commensurable with another. """
        return self.base_units == other.base_units

    def conversion_factor(self, other: Quantity) -> float:
        """ The conversion factor for multiplying a value from one set of units to another. """
        return 10**(self.multiplier - other.multiplier)

    def same_units_as(self, other: Quantity) -> Quantity:
        """ Convert to the units of another quantity. """
        return self.convert_units(*other.units)

    def to_base_units(self) -> Quantity:
        return Quantity(self.base_value, *self.tupled_base_units())

    def convert_units(self, *other_units) -> Quantity:
        """ Convert the quantity into other units.

        Parameters
        ----------
        *other_units: tuples
            The (n, u, p) unit tuples to be converted to.

        Returns
        -------
        Quantity:
            The quantity in the other units.
        """
        other = Quantity(1, *other_units)
        if not self.commensurable(other):
            raise TypeError(f"Cannot convert {self.base_units} to {other.base_units}")
        other.value = self.value * self.conversion_factor(other)
        return other

    # -------------------------------------------------------------------------
    # Printing
    # -------------------------------------------------------------------------

    def to_string(self, latex=False) -> str:
        """ Convert te quantity to a string for display.

        Parameters
        ----------
        latex: bool
            Convert to a LaTeX string.

        Return
        ------
        str:
            The quantity.
        """
        def format_unit(unit) -> str:
            """ String of a unit tuple."""
            n, u, p = unit
            y = "^{" if latex else "^"
            z = "}" if latex else ""

            if isinstance(n, int):
                s = u if n == 0 else f"(10{y}{n}{z}.{u})"
            else:
                s = f"{n}{u}"
            if p != 1:
                try:
                    s += f"{y}{int(p)}{z}"
                except ValueError:
                    s += f"{y}{p}{z}"
            return s

        unit_str = ".".join([format_unit(unit) for unit in self.units])
        blank = "\:" if latex else " "
        full_str = str(self.value) + blank + unit_str
        if latex:
            return r"$" + full_str + r"$"
        return full_str

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return str(self)

    # -------------------------------------------------------------------------
    # Base unit calculation.
    # -------------------------------------------------------------------------

    @staticmethod
    def _add_to_dict(d, k, v):
        """ Add a value to value in a dictionary.
        """
        if k in d:
            d[k] += v
        else:
            d[k] = v

    @staticmethod
    def base_units(*compound_unit) -> tuple[int, dict]:
        """ Transform a compound unit to base-SI units.

        Parameters
        ----------
        *compound_unit: (int, str, int), ...
            A 'compound' unit made up of a set of
            (m, u, p) units of the form (10^m u)^p.
            e.g. cm^3 = (-2, 'm', 3)
            e.g. mL = (-3, 'L', 1)

        Returns
        -------
        multiplier: int
            10^m applied to a value in the original units, to give
            its value in the transformed units. aka "conversion factor".
        units: {str: int, ....}
            The transformed units. u^p
        """
        multiplier = 0
        units = {}
        for unit in compound_unit:

            # Decompose unit.
            if not isinstance(unit, tuple) or len(unit) != 3:
                continue
            n, u, p = unit

            # Convert string prefix to int.
            if isinstance(n, str):
                if n in Quantity.UNIT_PREFIXS:
                    n = Quantity.UNIT_PREFIXS[n]
                else:
                    raise KeyError(f"{n} is not a recognised unit prefix.")

            # Derived unit.
            #    (10^n u)^p
            # => (10^n [10^m u1^q1 u2^q2 ...])^p
            # => (10^n+m u1^q1 u2^q2 ...)^p
            # => 10^(n+m)p u1^q1p u2^q2p ...
            if u in Quantity.DERIVED_UNITS:
                m, uq = Quantity.base_units(*Quantity.DERIVED_UNITS[u])
                multiplier += (n + m) * p
                for u, q in uq.items():
                    Quantity._add_to_dict(units, u, q * p)

            # Base unit.
            #    (10^n u)^p
            # => 10^np u^p
            else:
                multiplier += n * p
                Quantity._add_to_dict(units, u, p)

        return multiplier, {u: p for u, p in units.items() if p != 0}

    # -------------------------------------------------------------------------
    # Mathematical operators
    # -------------------------------------------------------------------------

    def _base_unit_set(self, other: Quantity):
        """ Yield the union of the base units of (self, other) with exponents.

        Yields
        ------
        u: str
            The unit.
        p: int
            The exponent for self.
        q: int
            The exponent for other.
        """
        for u in set(
                list(self.base_units.keys()) + list(other.base_units.keys())):
            yield u, self.base_units.get(u, 0), other.base_units.get(u, 0)

    def __eq__(self, other: Quantity) -> Quantity:
        """ Commensurability of two quantities. """
        return self.commensurable(other)

    def __add__(self, other: Quantity) -> Quantity:
        """ Add a quantity. """
        if not self.commensurable(other):
            raise TypeError(f"Cannot add {self} and {other}.")

        value = self.base_value + other.base_value
        units = self.tupled_base_units()
        return Quantity(value, *units)

    def __sub__(self, other: Quantity) -> Quantity:
        """ Subtract a quantity. """
        if not self.commensurable(other):
            raise TypeError(f"Cannot subtract {other} from {self}.")

        value = self.base_value - other.base_value
        units = self.tupled_base_units()
        return Quantity(value, *units)

    def __mul__(self, other: Quantity) -> Quantity:
        """ Multiply by a quantity. """
        value = self.base_value * other.base_value
        units = [
            (0, u, p + q)
            for u, p, q in self._base_unit_set(other)
            if p + q != 0
        ]
        return Quantity(value, *units)

    def __truediv__(self, other: Quantity) -> Quantity:
        """ Divide by a quantity. """
        value = self.base_value / other.base_value
        units = [
            (0, u, p - q)
            for u, p, q in self._base_unit_set(other)
            if p - q != 0
        ]
        return Quantity(value, *units)

    def __pow__(self, z) -> Quantity:
        """ Raise to an exponent. """
        if not isinstance(z, numbers.Real):
            raise TypeError("Exponent must be a real number.")

        value = self.base_value ** z
        units = [
            (0, u, p * z)
            for u, p in self.base_units.items()
            if p * z != 0
        ]
        return Quantity(value, *units)

    def apply(self, foo) -> Quantity:
        """ Apply a function to the value. """
        return Quantity(foo(self.value), *self.units)
