import pymem
import pymem.process
import time
import os
import ctypes
import logging
from requests import get
from colorama import init, Fore
from packaging import version

# Initialize colorama for colored console output
init(autoreset=True)

class Logger:
    """Handles logging setup for the application."""

    LOG_DIRECTORY = os.path.expandvars(r'%LOCALAPPDATA%\Requests\ItsJesewe\crashes')
    LOG_FILE = os.path.join(LOG_DIRECTORY, 'bhop_logs.log')

    @staticmethod
    def setup_logging():
        """Set up the logging configuration with the default log level INFO."""
        os.makedirs(Logger.LOG_DIRECTORY, exist_ok=True)
        with open(Logger.LOG_FILE, 'w') as f:
            pass

        logging.basicConfig(
            level=logging.INFO,  # Default to INFO level logging
            format='%(levelname)s: %(message)s',
            handlers=[logging.FileHandler(Logger.LOG_FILE), logging.StreamHandler()]
        )

class Utility:
    """Contains utility functions for the application."""

    @staticmethod
    def set_console_title(title):
        ctypes.windll.kernel32.SetConsoleTitleW(title)

    @staticmethod
    def fetch_offsets():
        """Fetches offsets from the GitHub repository."""
        try:
            response = get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.hpp")
            if response.status_code == 200:
                offsets = response.text
                # Extract dwForceJump offset from the line containing "jump"
                for line in offsets.splitlines():
                    if "jump" in line:
                        # Extract the offset value after the last '=' symbol, and remove any trailing characters
                        offset_str = line.split('=')[-1].strip().rstrip(';')
                        offset = int(offset_str, 16)
                        return offset
            else:
                logging.error(f"{Fore.RED}Ei löytynyt offsettejä palvelimelta.")
        except Exception as e:
            logging.error(f"{Fore.RED}Ei löytynyt offsettejä.: {e}")
        return None


    @staticmethod
    def check_for_updates(current_version):
        """Checks for software updates on GitHub."""
        try:
            response = get("https://api.github.com/repos/Jesewe/cs2-bhop/tags")
            response.raise_for_status()
            latest_version = response.json()[0]["name"]
            if version.parse(latest_version) > version.parse(current_version):
                logging.warning(f"{Fore.YELLOW}New version available: {latest_version}. Please update for the latest fixes and features.")
            elif version.parse(current_version) > version.parse(latest_version):
                logging.info(f"{Fore.YELLOW}Kehittäjä versio: Käytät esi(eng. pre)versiota tai kehittäjäversiota.")
            else:
                logging.info(f"{Fore.GREEN}Käytät uusinta versiota.")
        except Exception as e:
            logging.error(f"{Fore.RED}Virhe tarkistaessa päivityksiä: {e}")

class Bhop:
    """Handles the bunnyhop functionality."""

    VERSION = "v1.0.2"

    def __init__(self):
        """Initializes the Bhop instance."""
        self.pm = None
        self.dwForceJump = Utility.fetch_offsets()
        self.client_base = None
        self.force_jump_address = None

    def initialize_pymem(self):
        """Initializes Pymem and attaches to the game process."""
        try:
            self.pm = pymem.Pymem("cs2.exe")
            logging.info(f"{Fore.GREEN}Liityttiin onnistuneesti cs2 prosessiin.")
        except pymem.exception.ProcessNotFound:
            logging.error(f"{Fore.RED}CS2 prosessia ei löytynyt. Varmista että peli on päällä.")
            return False
        except pymem.exception.PymemError as e:
            logging.error(f"{Fore.RED}Pythonin mem moduuli löysi virheen: {e}")
            return False
        except Exception as e:
            logging.error(f"{Fore.RED}Odottamaton virhe pythonin mem moduulin initialisaatiovaiheessa: {e}")
            return False
        return True 

    def get_client_module(self):
        """Retrieves the base address of the client.dll module."""
        try:
            if self.client_base is None:
                client_module = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
                if not client_module:
                    raise pymem.exception.ModuleNotFoundError("client.dll:ää ei löytynyt")
                self.client_base = client_module.lpBaseOfDll
                self.force_jump_address = self.client_base + self.dwForceJump  # Set the force jump address
        except pymem.exception.ModuleNotFoundError as e:
            logging.error(f"{Fore.RED}Virhe: {e}. Varmista että client.dll on ladattu.")
            return False
        except Exception as e:
            logging.error(f"{Fore.RED}Odottamaton virhe etsiessä moduulia (client.dll): {e}")
            return False
        return True  # Return True if the client module was successfully retrieved

    def start(self):
        """Starts the bunnyhop loop."""

        Utility.set_console_title(f"Hav0x CS2 Bhop {self.VERSION}")

        logging.info(f"{Fore.CYAN}Tarkistetaan päivityksiä...")
        Utility.check_for_updates(self.VERSION)

        logging.info(f"{Fore.CYAN}Haetaan offsettejä ja asiakasdataa...")

        logging.info(f"{Fore.CYAN}Haetaan cs2 prosessia. (cs2.exe)...")
        if not self.initialize_pymem():
            input(f"{Fore.RED}Paina entteriä quitataksesi...")
            return

        if not self.get_client_module():
            input(f"{Fore.RED}Paina entteriä quitataksesi...")
            return

        jump = False
        logging.info(f"{Fore.GREEN}Bhop alkoi.")


        while True:
            try:
                if ctypes.windll.user32.GetAsyncKeyState(0x20):  # Spacebar
                    if not jump:
                        time.sleep(0.01)
                        self.pm.write_int(self.force_jump_address, 65537)
                        jump = True
                    else:
                        time.sleep(0.01)
                        self.pm.write_int(self.force_jump_address, 256)
                        jump = False
            except Exception as e:
                logging.error(f"{Fore.RED}Odottamaton virhe: {e}")
                logging.error(f"{Fore.RED}Ilmoita tästä ongelmasta GitHub-tietovarastossa: https://github.com/Jesewe/cs2-triggerbot/issues")
                input(f"{Fore.RED}Paina entteriä quitataksesi...")

if __name__ == "__main__":
    Logger.setup_logging()
    bhop = Bhop()
    bhop.start()
