from .Launcher import Launcher
from ..ProcessExecution import ProcessExecution
from ..ResourceResolver import ResourceResolver

class Bin(Launcher):
    """
    Binary launcher implementation.
    """

    def __init__(self, *args, **kwargs):
        """
        Create a bin launcher.
        """
        super(Bin, self).__init__(*args, **kwargs)

        self.__resourceResolver = ResourceResolver(self.env())

    def _perform(self):
        """
        Implement the execution of the binary launcher.
        """
        executable = self.__resourceResolver.resolve(self.config('executable'))
        args = self.config('args') if 'args' in self.configNames() else []

        processArgs = [
            executable
        ]
        processArgs += args

        return ProcessExecution(
            processArgs,
            self.env(),
            shell=True
        )

    @classmethod
    def requiredOptionNames(cls):
        """
        Return a list of required options for the launcher implementation.
        """
        return super(Bin, cls).requiredOptionNames() + [
            'executable'
        ]


# registering launcher
Launcher.register(Bin, 'bin')
