from colorama import Fore, init

init(convert=True)


class Colors:
    """It's a class that contains a bunch of constants that represent colors."""

    HEADER = Fore.MAGENTA
    OKBLUE = Fore.BLUE
    OKCYAN = Fore.CYAN
    OKGREEN = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    ENDC = Fore.RESET
    BOLD = Fore.LIGHTBLACK_EX
