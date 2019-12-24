from traitlets import Unicode


class SeparateUnicode(Unicode):
    r"""A Unicode subclass to validate separate_in, separate_out, etc.

    This is a Unicode based trait that converts '0'->'' and ``'\\n'->'\n'``.
    """

    def validate(self, obj, value):
        """

        Parameters
        ----------
        obj :
        value :

        Returns
        -------

        """
        if value == "0":
            value = ""
        value = value.replace("\\n", "\n")
        return super(SeparateUnicode, self).validate(obj, value)
