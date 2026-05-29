import sys
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, TYPE_CHECKING

from app.models.member import Member
from app.models.experience import Experience
from app.models.education import Education
from app.core.enums import ConnectionStatus

if TYPE_CHECKING:
    from app.console.console_app import ConsoleContext


class ConsoleCommand(ABC):
    """
    Abstract Command class in the Command Design Pattern.
    Defines the standard execution contract for all CLI interactive menu options,
    enforcing SRP and OCP.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Returns the menu label for this command."""
        pass

    @abstractmethod
    def execute(self, context: 'ConsoleContext') -> None:
        """Executes the specific behavior of this command."""
        pass


# ==========================================
# ANONYMOUS COMMANDS
# ==========================================

class LoginCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Log In"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Member Login")
        email = context.get_input("Enter Email")
        password = context.get_input("Enter Password")

        member = context.system.get_member_by_email(email)
        if member and member.password == password:
            context.current_member = member
            print(f"\nWelcome back, {member.get_name()}!")
        else:
            print("\nError: Invalid email or password.")


class RegisterCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Register New Account"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Member Registration")
        name = context.get_input("Enter Full Name")
        email = context.get_input("Enter Email Address")
        
        # Check if email is already taken
        if context.system.get_member_by_email(email):
            print("\nError: An account with this email is already registered.")
            return

        password = context.get_input("Enter Password")
        summary = context.get_optional_input("Enter Professional Summary (Optional)")

        builder = Member.Builder(name, email).with_password(password)
        if summary:
            builder.with_summary(summary)

        new_member = builder.build()
        context.system.register_member(new_member)
        print(f"\nRegistration successful! You can now log in.")


class SearchMembersCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Search Registered Members"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Search Members")
        query = context.get_input("Enter search query (name)")
        
        results = context.system.search_member_by_name(query)
        if not results:
            print("\nNo matching members found.")
            return

        print(f"\nSearch results for '{query}':")
        for member in results:
            summary = member.get_profile().summary or "No summary"
            print(f" - {member.get_name()} ({member.get_email()}) | {summary}")


class ExitCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Exit Application"

    def execute(self, context: 'ConsoleContext') -> None:
        print("\nThank you for using LinkedIn Console. Goodbye!")
        sys.exit(0)


# ==========================================
# AUTHENTICATED COMMANDS
# ==========================================

class LogoutCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Log Out"

    def execute(self, context: 'ConsoleContext') -> None:
        print(f"\nLogged out successfully. Goodbye, {context.current_member.get_name()}!")
        context.current_member = None


class ViewProfileCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "View My Profile"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("My Professional Profile")
        context.current_member.display_profile()


class UpdateProfileCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Update My Profile"

    def execute(self, context: 'ConsoleContext') -> None:
        while True:
            context.print_header("Update Profile Menu")
            choice = context.select_option("Select update operation:", [
                "Set Profile Summary",
                "Add Professional Experience",
                "Add Education Details",
                "Back to Member Menu"
            ])

            if choice == 1:
                summary = context.get_input("Enter new summary")
                context.current_member.get_profile().set_summary(summary)
                print("\nProfile summary updated.")
            elif choice == 2:
                title = context.get_input("Enter Job Title")
                company = context.get_input("Enter Company Name")
                
                # Input dates
                start_str = context.get_input("Enter Start Date (YYYY-MM-DD)")
                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                except ValueError:
                    print("Error: Invalid date format. Using today's date.")
                    start_date = date.today()

                end_str = context.get_optional_input("Enter End Date (YYYY-MM-DD) or press Enter if current job")
                end_date = None
                if end_str:
                    try:
                        end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                    except ValueError:
                        print("Error: Invalid date format. Set to None (Current).")

                exp = Experience(title, company, start_date, end_date)
                context.current_member.get_profile().add_experience(exp)
                print("\nExperience added to profile.")
            elif choice == 3:
                school = context.get_input("Enter School / University Name")
                degree = context.get_input("Enter Degree / Field of Study")
                
                try:
                    start_year = int(context.get_input("Enter Start Year (YYYY)"))
                    end_year = int(context.get_input("Enter End Year (YYYY)"))
                except ValueError:
                    print("Error: Invalid year. Using default years (2020-2024).")
                    start_year = 2020
                    end_year = 2024

                edu = Education(school, degree, start_year, end_year)
                context.current_member.get_profile().add_education(edu)
                print("\nEducation added to profile.")
            else:
                break


class SendConnectionRequestCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Send Connection Request"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Send Connection Request")
        query = context.get_input("Search for members by name")

        results = context.system.search_member_by_name(query)
        # Exclude self and members who are already connections
        valid_targets = [
            m for m in results 
            if m.get_id() != context.current_member.get_id() 
            and m not in context.current_member.get_connections()
        ]

        if not valid_targets:
            print("\nNo connectable members found matching that search.")
            return

        options = [f"{m.get_name()} ({m.get_email()})" for m in valid_targets]
        choice = context.select_option("Select member to send connection request:", options)
        
        target_member = valid_targets[choice - 1]
        
        # Verify no duplicate active request
        active_request_exists = False
        for req in context.system.connection_service.connection_requests.values():
            if (req.get_from_member().get_id() == context.current_member.get_id() and 
                req.get_to_member().get_id() == target_member.get_id()):
                active_request_exists = True
                break

        if active_request_exists:
            print(f"\nError: You have already sent a pending connection request to {target_member.get_name()}.")
        else:
            context.system.send_connection_request(context.current_member, target_member)


class ViewConnectionsCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "View My Connections"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("My Connected Network")
        connections = context.current_member.get_connections()
        if not connections:
            print("  You have not connected with anyone yet.")
            return

        for idx, member in enumerate(connections, 1):
            summary = member.get_profile().summary or "No summary"
            print(f" [{idx}] {member.get_name()} ({member.get_email()}) | {summary}")


class ViewNotificationsCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "View Notifications & Requests"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Notifications & Requests")

        # 1. Show regular unread notifications
        context.current_member.view_notifications()

        # 2. Show pending connection requests
        pending_requests = [
            (req_id, req) for req_id, req in context.system.connection_service.connection_requests.items()
            if req.get_to_member().get_id() == context.current_member.get_id() 
            and req.get_status() == ConnectionStatus.PENDING
        ]

        print("\n--- Pending Connection Requests ---")
        if not pending_requests:
            print("  No pending connection requests.")
            return

        for idx, (_, req) in enumerate(pending_requests, 1):
            from_name = req.get_from_member().get_name()
            from_email = req.get_from_member().get_email()
            print(f" [{idx}] {from_name} ({from_email}) wants to connect.")

        respond = context.select_option("Do you want to respond to a request?", ["Yes", "No"])
        if respond == 1:
            try:
                choice_str = context.get_input(f"Enter request index (1-{len(pending_requests)})")
                choice_idx = int(choice_str)
                if 1 <= choice_idx <= len(pending_requests):
                    req_id, req = pending_requests[choice_idx - 1]
                    action = context.select_option(
                        f"Respond to {req.get_from_member().get_name()}:",
                        ["Accept Connection", "Decline Connection", "Cancel"]
                    )
                    if action == 1:
                        context.system.accept_connection_request(req_id)
                        print(f"You are now connected with {req.get_from_member().get_name()}.")
                    elif action == 2:
                        context.system.reject_connection_request(req_id)
                else:
                    print("Error: Invalid choice.")
            except ValueError:
                print("Error: Please enter a valid number.")


class CreatePostCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "Share a Post"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("Create a Post")
        content = context.get_input("What is on your mind?")
        
        context.system.create_post(context.current_member.get_id(), content)


class ViewNewsFeedCommand(ConsoleCommand):
    def get_name(self) -> str:
        return "View My News Feed"

    def execute(self, context: 'ConsoleContext') -> None:
        context.print_header("My News Feed")

        feed_posts = []
        for connection in context.current_member.get_connections():
            connection_posts = context.system.news_feed_service.get_member_posts(connection)
            feed_posts.extend(connection_posts)

        from app.strategies.feed_sorting_strategy import ChronologicalSortStrategy
        sorted_posts = ChronologicalSortStrategy().sort(feed_posts)

        if not sorted_posts:
            print("  Your news feed is empty. Connect with other members or wait for them to post.")
            return

        for idx, post in enumerate(sorted_posts, 1):
            print("\n" + "-" * 50)
            print(f" [{idx}] POST BY: {post.get_author().get_name().upper()} (at {post.get_created_at().strftime('%Y-%m-%d %H:%M')})")
            print(f" Content: {post.get_content()}")
            print(f" Likes: {len(post.get_likes())} | Comments: {len(post.get_comments())}")
            if post.get_comments():
                print(" Comments:")
                for c in post.get_comments():
                    print(f"   * {c.get_author().get_name()}: {c.get_text()}")
            print("-" * 50)

        interact = context.select_option("Would you like to interact with a post?", ["Yes", "No"])
        if interact == 1:
            try:
                post_str = context.get_input(f"Enter post number (1-{len(sorted_posts)})")
                post_idx = int(post_str)
                if 1 <= post_idx <= len(sorted_posts):
                    selected_post = sorted_posts[post_idx - 1]
                    action = context.select_option(
                        f"Choose action for post by {selected_post.get_author().get_name()}:",
                        ["Like Post", "Write a Comment", "Back"]
                    )
                    if action == 1:
                        # Add like
                        selected_post.add_like(context.current_member)
                    elif action == 2:
                        # Add comment
                        comment_text = context.get_input("Type your comment")
                        selected_post.add_comment(context.current_member, comment_text)
                else:
                    print("Error: Invalid post selection.")
            except ValueError:
                print("Error: Please enter a valid number.")
