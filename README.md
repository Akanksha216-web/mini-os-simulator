Mini OS Simulator

Video Demo: https://youtu.be/xmib6fsiW1U

Description:

Mini OS Simulator is a web-based operating system simulation built using Python, Flask, SQLite, HTML, CSS, and Bootstrap. The goal of this project was to create a simplified operating system environment that allows users to interact with a virtual file system through both terminal-style commands and a graphical desktop interface. Users can register, log in, create folders and files, navigate directories, edit file contents, and manage their own isolated virtual workspace.

The inspiration for this project came from the desire to better understand how operating systems organize files and directories. While modern operating systems provide highly sophisticated file management systems, their underlying concepts can be difficult for beginners to visualize. This project attempts to simplify those ideas while still providing a realistic user experience. Instead of interacting with the real computer's file system, users work within a virtual file system stored entirely inside a SQLite database.

One of the main objectives of the project was to combine concepts from several areas of computer science that were covered throughout CS50. These concepts include web development with Flask, database design using SQLite, user authentication, session management, hierarchical data structures, recursion, and front-end development using HTML and CSS.

The central component of the project is the virtual file system. Files and folders are stored in a database table called "files". Each entry contains information such as its name, type, owner, parent directory, and file contents. The "parent_id" field allows folders to contain other folders and files, creating a tree-like structure similar to that used in real operating systems. Rather than creating actual folders on the computer, the application reconstructs the directory hierarchy using database relationships.

Users interact with the system through a terminal interface. Several commands are supported, including "ls", "mkdir", "touch", "cd", and "rm". The "ls" command displays the contents of the current directory. The "mkdir" command creates a new folder. The "touch" command creates a new file. The "cd" command allows users to move between directories, while "rm" removes files or folders. Together, these commands simulate the basic functionality available in many command-line operating systems.

In addition to terminal commands, the project includes a desktop-style graphical interface. Files and folders are displayed as icons that can be clicked to perform actions. Clicking a folder navigates into that directory, while clicking a file opens a simple text editor. This dual-interface approach was chosen because it makes the project more intuitive and visually engaging while still preserving the educational value of command-line interaction.

The file editor allows users to open files and modify their contents. When a file is saved, its contents are stored directly in the database. This feature transforms files from simple placeholders into meaningful objects capable of storing information. Because file contents are persisted in the database, users can close the application, return later, and continue working with the same files.

User authentication is another important part of the project. New users can register an account, while existing users can log in using their credentials. Passwords are not stored as plain text. Instead, the application uses the SHA-256 hashing algorithm to transform passwords into hash values before storing them in the database. During login, the entered password is hashed again and compared with the stored hash. Although this demonstrates the concept of password hashing, SHA-256 alone is not recommended for production password storage because it is not designed to resist password-guessing attacks. A dedicated password-hashing algorithm, such as scrypt or Argon2, would be more appropriate for a production application.

Session management is implemented using Flask-Session. When users log in successfully, session variables store information such as the user's ID and current working directory. This allows the application to maintain state across requests and provide each user with an individual virtual workspace. File and folder queries use ownership information to restrict access to the current user's data.

## Project Structure

The project consists of several files, each serving a specific purpose:

- **`app.py`**: Contains the main Flask application, route definitions, terminal command processing, file and folder management, and database interactions.
- **`helpers.py`**: Contains utility functions, including the `login_required` decorator, which restricts access to routes that require authentication.
- **`schema.sql`**: Defines the database schema used to store user accounts, files, folders, and other application data.
- **`init_db.py`**: Initializes the SQLite database by executing the SQL statements in `schema.sql`.
- **`requirements.txt`**: Lists the Python packages required to run the application.
- **`templates/`**: Contains the HTML templates used to render the login page, registration page, terminal, file editor, and other interface components.
- **`static/`**: Contains static resources, including CSS stylesheets and other front-end assets.

## Design Decisions

One design decision I spent time considering was how to represent the file system. Initially, I explored using Python classes such as `Directory` and `File` to store data in memory. While this approach worked for simple testing, it lacked persistence because data would disappear when the application stopped running. I ultimately chose a database-driven design because it provides persistent storage and allows users to retain their files between sessions.

Another design choice involved supporting both terminal commands and graphical navigation. While either approach could have worked independently, combining both provided a more complete experience. Users who prefer command-line interaction can manage their files through commands, while users who prefer visual navigation can interact with icons and clickable folders.

## Installation and Usage

### Prerequisites

- Python 3
- pip

### Setup Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/Akanksha216-web/mini-os-simulator.git
   ```

2. Navigate to the project directory:

   ```bash
   cd mini-os-simulator
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:

   ```bash
   python init_db.py
   ```

   **Note:** Run this command when setting up a fresh database. Check `schema.sql` before rerunning it if you already have data you want to preserve.

5. Start the application:

   ```bash
   python app.py
   ```

6. Open your browser and visit:

   `http://127.0.0.1:5000`

7. Register an account or log in to begin using the virtual file system.

## Limitations

Mini OS Simulator is an educational simulation rather than a real operating system. Files and folders are stored in an SQLite database instead of the host computer's actual file system. The terminal supports a limited set of predefined commands and does not execute arbitrary operating system commands.

The application demonstrates fundamental concepts in operating systems, database management, web development, and user authentication. It is not intended for production use.

## Conclusion

Building Mini OS Simulator helped me develop a deeper understanding of file system organization, hierarchical data structures, database persistence, and session management in web applications. By combining terminal-style commands with graphical navigation, the project provides an interactive way to explore fundamental operating system concepts while applying the programming and problem-solving skills developed throughout CS50.