import re
import sys
import select
import subprocess

class ProcessExecution(object):
    """
    Executes a process.
    """

    # regex: any alpha numeric, underscore and dash characters are allowed.
    __validateShellArgRegex = re.compile("^[\w_-]*$")

    def __init__(self, args, env={}, shell=True, cwd=None, redirectStderrToStdout=False):
        """
        Create a ProcessExecution object.

        The constructor signature tries mimic the features available by subprocess.Popen.
        """
        self.__stdout = []
        self.__stderr = []
        self.__shell = shell
        self.__cwd = cwd
        self.__redirectStderrToStdout = redirectStderrToStdout

        self.__setArgs(args)
        self.__setEnv(env)
        self.__createProcess()

    def isShell(self):
        """
        Return the process should run through a shell session.
        """
        return self.__shell

    def env(self):
        """
        Return the environment for the process.
        """
        return self.__env

    def cwd(self):
        """
        Return the current working directory used to launch the process.
        """
        return self.__cwd

    def args(self):
        """
        Return a list of arguments used by the process.
        """
        return self.__args

    def stderr(self):
        """
        Return a list of stderr messages.
        """
        return self.__stderr

    def stdout(self):
        """
        Return a list of stdout messages.
        """
        return self.__stdout

    def redirectStderrToStdout(self):
        """
        Return a boolean telling if the stderr stream should be redirected to stdout.
        """
        return self.__redirectStderrToStdout

    def executionSuccess(self):
        """
        Return a boolean if the execution has been sucessfull.
        """
        return self.exitStatus() == 0

    def exitStatus(self):
        """
        Return the exist status about the process.
        """
        return self.__process.returncode

    def pid(self):
        """
        Return the process id.
        """
        return self.__process.pid

    def execute(self):
        """
        Execute the process.
        """
        # we want all stream messages to keep going
        # up to system's stream in realtime, instead of
        # showing them only when execution is done
        # (subprocess/communicate default behaviour)
        # https://stackoverflow.com/questions/12270645
        while True:
            cancel = True
            reads = [
                self.__process.stdout.fileno()
            ]

            if self.__process.stderr:
                reads.append(self.__process.stderr.fileno())

            try:
                cancel = self.__readProcessOutput(reads)

            except KeyboardInterrupt:
                reason = ' KeyboardInterrupt\n'
                sys.stderr.write(reason)
                self.__stderr.append(reason)
                break

            if cancel and self.__process.poll() is not None:
                break

        # closing streams
        self.__process.stdout.close()
        if self.__process.stderr:
            self.__process.stderr.close()

    def __readProcessOutput(self, reads):
        """
        Read the process output by looking at stdout and stderr.

        Return a boolean telling the if process has collected any information
        from both stdout or stderr.
        """
        hasOutput = True
        ret = select.select(reads, [], [])
        for fd in ret[0]:
            if fd == self.__process.stdout.fileno():
                read = self.__streamValue(self.__process.stdout)
                sys.stdout.write(read)
                self.__stdout.append(read)

                if len(read):
                    hasOutput = False

            if self.__process.stderr and fd == self.__process.stderr.fileno():
                read = self.__streamValue(self.__process.stderr)
                sys.stderr.write(read)
                self.__stderr.append(read)

                if len(read):
                    hasOutput = False

        return hasOutput

    def __setArgs(self, args):
        """
        Set a list of arguments that should be used by the process.
        """
        assert isinstance(args, list), "Invalid args list!"

        self.__args = list(args)

    def __setEnv(self, env):
        """
        Set the environment for the process.
        """
        self.__env = dict(env)

    def __createProcess(self):
        """
        Create a process that later should be executed through {@link run}.
        """
        stderrStream = subprocess.STDOUT if self.redirectStderrToStdout() else subprocess.PIPE

        executableArgs = ' '.join(map(str, self.__sanitizeShellArgs(self.args()))) if self.isShell() else self.args()
        self.__process = subprocess.Popen(
            executableArgs,
            stdout=subprocess.PIPE,
            stderr=stderrStream,
            shell=self.isShell(),
            env=self.env(),
            cwd=self.cwd()
        )

    @staticmethod
    def __streamValue(stream):
        """
        Return a string value from the stream.
        """
        read = stream.readline()
        if not isinstance(read, str):
            read = read.decode("utf_8")
        return read

    @staticmethod
    def __sanitizeShellArgs(args):
        """
        Sanitize shell args by escaping shell special characters.
        """
        result = []

        for index, arg in enumerate(args):

            # we need to avoid to escape the first argument otherwise, it will be
            # interpreted as string rather than a command.
            if index == 0 or ProcessExecution.__validateShellArgRegex.match(arg):
                result.append(arg)
            else:
                result.append('"{}"'.format(arg.replace('"', '\\"')))

        return result
