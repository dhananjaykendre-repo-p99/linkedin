import sys
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import date

from app.core.linkedin_system import LinkedInSystem
from app.models.member import Member
from app.models.experience import Experience
from app.models.education import Education


class ConsoleContext(ABC):
    """
    Interface defining the CLI application's operating context.
    Enforces the Dependency Inversion Principle (DIP) by letting command classes
    rely on this abstraction rather than the concrete ConsoleApp.
    """

    @property
    @abstractmethod
    def system(self) -> LinkedInSystem:
        """Access the central LinkedInSystem."""
        pass

    @property
    @abstractmethod
    def current_member(self) -> Optional[Member]:
        """Get the currently logged-in member."""
        pass

    @current_member.setter
    @abstractmethod
    def current_member(self, member: Optional[Member]) -> None:
        """Set the currently logged-in member."""
        pass

    @abstractmethod
    def print_header(self, title: str) -> None:
        """Utility to print a clear, structured header."""
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        """Utility to get non-empty input from user."""
        pass

    @abstractmethod
    def get_optional_input(self, prompt: str, default: str = "") -> str:
        """Utility to get optional input from user."""
        pass

    @abstractmethod
    def select_option(self, prompt: str, options: List[str]) -> int:
        """Utility to show a menu and get selected index (1-based)."""
        pass


class ConsoleApp(ConsoleContext):
    """
    Concrete console application runner. Manages input/output streams,
    active user session state, and coordinates the execution loop.
    """

    def __init__(self):
        self._system = LinkedInSystem.get_instance()
        self._current_member: Optional[Member] = None
        self._bootstrap_demo_data()

    @property
    def system(self) -> LinkedInSystem:
        return self._system

    @property
    def current_member(self) -> Optional[Member]:
        return self._current_member

    @current_member.setter
    def current_member(self, member: Optional[Member]) -> None:
        self._current_member = member

    def print_header(self, title: str) -> None:
        print("\n" + "=" * 50)
        print(f" {title.upper()} ".center(50, "="))
        print("=" * 50)

    def get_input(self, prompt: str) -> str:
        while True:
            try:
                value = input(f"{prompt}: ").strip()
                if value:
                    return value
                print("Error: Input cannot be empty. Please try again.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting application.")
                sys.exit(0)

    def get_optional_input(self, prompt: str, default: str = "") -> str:
        try:
            value = input(f"{prompt} [{default}]: ").strip()
            return value if value else default
        except (KeyboardInterrupt, EOFError):
            print("\nExiting application.")
            sys.exit(0)

    def select_option(self, prompt: str, options: List[str]) -> int:
        while True:
            print(f"\n{prompt}")
            for idx, opt in enumerate(options, 1):
                print(f" [{idx}] {opt}")
            
            try:
                choice_str = input("Select an option: ").strip()
                if not choice_str:
                    continue
                choice = int(choice_str)
                if 1 <= choice <= len(options):
                    return choice
                print(f"Error: Invalid option. Choose between 1 and {len(options)}.")
            except ValueError:
                print("Error: Please enter a valid number.")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting application.")
                sys.exit(0)

    def _bootstrap_demo_data(self) -> None:
        """Bootstrap the application with standard mock data for ease of testing."""
        # Create Alice
        alice = Member.Builder("Alice", "alice@example.com") \
            .with_password("password") \
            .with_summary("Senior Software Engineer with 10 years of experience.") \
            .add_experience(Experience("Sr. Software Engineer", "Google", date(2018, 1, 1), None)) \
            .add_experience(Experience("Software Engineer", "Microsoft", date(2014, 6, 1), date(2017, 12, 31))) \
            .add_education(Education("Princeton University", "M.S. in Computer Science", 2012, 2014)) \
            .build()

        # Create Bob
        bob = Member.Builder("Bob", "bob@example.com") \
            .with_password("password") \
            .with_summary("Product Manager at Stripe.") \
            .add_experience(Experience("Product Manager", "Stripe", date(2020, 2, 1), None)) \
            .add_education(Education("MIT", "B.S. in Business Analytics", 2015, 2019)) \
            .build()

        # Create Charlie
        charlie = Member.Builder("Charlie", "charlie@example.com") \
            .with_password("password") \
            .build()

        self._system.register_member(alice)
        self._system.register_member(bob)
        self._system.register_member(charlie)

        # Preloaded relationship: Alice sends connection request to Bob and Charlie
        req1 = self._system.send_connection_request(alice, bob)
        self._system.send_connection_request(alice, charlie)

        # Bob accepts request
        self._system.accept_connection_request(req1)

        # Bob posts something
        self._system.create_post(bob.get_id(), "Excited to share we've launched our new feature! #productmanagement")

    def run(self) -> None:
        # Import commands dynamically to avoid circular import issues
        from app.console.commands import (
            RegisterCommand, LoginCommand, SearchMembersCommand, ExitCommand,
            ViewProfileCommand, UpdateProfileCommand, SendConnectionRequestCommand,
            ViewConnectionsCommand, ViewNotificationsCommand, CreatePostCommand,
            ViewNewsFeedCommand, LogoutCommand
        )

        anonymous_commands = [
            LoginCommand(),
            RegisterCommand(),
            SearchMembersCommand(),
            ExitCommand()
        ]

        authenticated_commands = [
            ViewProfileCommand(),
            UpdateProfileCommand(),
            CreatePostCommand(),
            ViewNewsFeedCommand(),
            SendConnectionRequestCommand(),
            ViewConnectionsCommand(),
            ViewNotificationsCommand(),
            LogoutCommand()
        ]

        self.print_header("Welcome to LinkedIn Console")
        print("Prepopulated users available for testing:")
        print("  - Alice (alice@example.com, password: password)")
        print("  - Bob (bob@example.com, password: password)")
        print("  - Charlie (charlie@example.com, password: password)")

        while True:
            if self._current_member is None:
                # Anonymous state menu
                options = [cmd.get_name() for cmd in anonymous_commands]
                choice = self.select_option("MAIN MENU", options)
                cmd = anonymous_commands[choice - 1]
                cmd.execute(self)
            else:
                # Authenticated state menu
                member_name = self._current_member.get_name()
                options = [cmd.get_name() for cmd in authenticated_commands]
                choice = self.select_option(f"LOGGED IN AS: {member_name.upper()}", options)
                cmd = authenticated_commands[choice - 1]
                cmd.execute(self)


if __name__ == "__main__":
    app = ConsoleApp()
    app.run()
