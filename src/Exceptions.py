import eons

# All builder errors
class BuildError(Exception, metaclass=eons.ActualType): pass


# Exception used for miscellaneous build errors.
class OtherBuildError(BuildError, metaclass=eons.ActualType): pass


# Project types can be things like "lib" for library, "bin" for binary, etc. Generally, they are any string that evaluates to a different means of building code.
class ProjectTypeNotSupported(BuildError, metaclass=eons.ActualType): pass
