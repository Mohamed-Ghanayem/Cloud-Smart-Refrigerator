import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import json
import subprocess
import os
import time
import threading

# Cognito Configuration
AWS_REGION = ''  # Replace with your AWS region
APP_CLIENT_ID = ''  # Replace with your App Client ID
APP_CLIENT_SECRET = ''  # Replace with your App Client Secret

# Create Cognito and Lambda Clients
cognito_client = boto3.client('cognito-idp', region_name=AWS_REGION)
lambda_client = boto3.client('lambda', region_name=AWS_REGION)  # Lambda client

def launch_gui_in_background(username):
    # Create the current_user.txt file and write the username to it
    global gui_process
    with open("current_user.txt", "w") as file:
        file.write(username)
    
    # Close the Florence keyboard before launching the GUI
    try:
        subprocess.run(["pkill", "-f", "florence"])  # Forcefully kill all Florence processes
        time.sleep(1)  # Wait for the process to terminate
    except Exception as e:
        pass  # Silently handle any errors

    # Launch GUI.py in the background using subprocess without blocking
    try:
        gui_process=subprocess.Popen(["python3.8", "GUI.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gui_process.wait()
    except Exception as e:
        pass  # Silently handle any errors

# Function to calculate SECRET_HASH
def calculate_secret_hash(username, app_client_id, app_client_secret):
    message = username + app_client_id
    secret_hash = hmac.new(
        bytes(app_client_secret, 'utf-8'),
        msg=bytes(message, 'utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(secret_hash).decode('utf-8')

# Function to call the Lambda for list initialization
def initialize_user_lists(username):
    try:
        lambda_payload = {"user_name": username}
        response = lambda_client.invoke(
            FunctionName='editUsersData',  
            InvocationType='RequestResponse',
            Payload=json.dumps(lambda_payload)
        )
        lambda_response = json.loads(response['Payload'].read().decode())
        if lambda_response.get('statusCode') == 201:
            messagebox.showinfo("Initialization", "User lists initialized successfully.")
        else:
            messagebox.showerror("Initialization Failed", f"Error: {lambda_response.get('body')}")
    except Exception as e:
        messagebox.showerror("Lambda Error", f"Error initializing user lists: {str(e)}")

# Signup Function
def signup(username, password, email):
    secret_hash = calculate_secret_hash(username, APP_CLIENT_ID, APP_CLIENT_SECRET)
    
    try:
        cognito_client.sign_up(
            ClientId=APP_CLIENT_ID,
            Username=username,
            Password=password,
            SecretHash=secret_hash,
            UserAttributes=[{'Name': 'email', 'Value': email}]
        )
        initialize_user_lists(username)  # Initialize lists for the user after successful signup
        messagebox.showinfo("Signup", "Account created successfully!")
    except ClientError as e:
        error_message = e.response['Error']['Message']
        messagebox.showerror("Signup Failed", error_message)

# Check if username exists function
def check_username_exists(username):
    try:
        cognito_client.admin_get_user(
            UserPoolId='eu-north-1_EEdcWimXd',  # Replace with your correct user pool ID
            Username=username
        )
        return True
    except cognito_client.exceptions.UserNotFoundException:
        return False

# Login Function
def login(username, password):
    secret_hash = calculate_secret_hash(username, APP_CLIENT_ID, APP_CLIENT_SECRET)  # Include SecretHash in login
    
    # Step 1: Check if the username exists
    if not check_username_exists(username):
        messagebox.showerror("Login Failed", "Username does not exist.")
        return

    # Step 2: If the username exists, proceed to authenticate the user
    try:
        response = cognito_client.initiate_auth(
            ClientId=APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash  # Include SECRET_HASH for login too
            }
        )
       
        # Close the Florence keyboard before launching the GUI
        try:
            subprocess.run(["pkill", "-f", "florence"])  # Forcefully kill all Florence processes
            time.sleep(1)  # Wait for the process to terminate
        except Exception as e:
            pass  # Silently handle any errors

        # Launch the GUI in the background
        launch_gui_in_background(username)

        # Hide the initial GUI after login
        root.withdraw()  # Hide the InitialGUI window
        root.update()  # Force update the GUI to ensure it's hidden

    except ClientError as e:
        error_message = e.response['Error']['Message']
        
        # Handle incorrect password error
        if "Incorrect username or password" in error_message:
            messagebox.showerror("Login Failed", "Incorrect password.")
        else:
            messagebox.showerror("Login Failed", error_message)

# Function to check if GUI.py has closed
def check_gui_closed():
    while True:
        if os.path.exists("GUI_closed.txt"):
            # Delete the GUI_closed.txt file
            os.remove("GUI_closed.txt")
            # Create a signal file to indicate that InitialGUI.py has closed
            with open("initial_gui_closed.txt", "w") as f:
                f.write("InitialGUI closed")
            root.destroy()  # Close the InitialGUI window
            break
        time.sleep(1)  # Check every second

def check_gui_logged_out():
    while True:
        if os.path.exists("GUI_logged_out.txt"):
            os.remove("GUI_logged_out.txt")
            root.destroy()  # Close the InitialGUI window
            break
        time.sleep(0.1)  # Check every second

# Function to open the on-screen keyboard
def open_on_screen_keyboard():
    try:
        # Open the on-screen keyboard (florence) in the background
        subprocess.Popen(["florence"])
    except FileNotFoundError:
        messagebox.showerror("Error", "On-screen keyboard not found. Please install florence.")

# Bind the on-screen keyboard to entry fields
def bind_keyboard_to_entry(entry):
    entry.bind("<FocusIn>", lambda event: open_on_screen_keyboard())

# Tkinter GUI
def main():
    def show_signup():
        login_frame.pack_forget()
        signup_frame.pack(side="left", anchor="w", padx=110)

    def show_login():
        signup_frame.pack_forget()
        login_frame.pack(side="left", anchor="w", padx=110)  

    def handle_signup():
        username = signup_username_entry.get()
        password = signup_password_entry.get()
        email = signup_email_entry.get()
        if username and password and email:
            signup(username, password, email)
        else:
            messagebox.showerror("Signup Error", "All fields are required!")

    def handle_login():
        username = login_username_entry.get()
        password = login_password_entry.get()
        if username and password:
            login(username, password)
        else:
            messagebox.showerror("Login Error", "Both fields are required!")

    global root
    root = tk.Tk()
    root.title("Smart Refrigerator")
    root.geometry("1024x600")  # Adjusted window size to 1024x600

    # Start the check_gui_closed function in a separate thread
    gui_check_thread = threading.Thread(target=check_gui_closed)
    gui_check_thread.daemon = True  # Ensure the thread terminates when the main program exits
    gui_check_thread.start()

    gui_logged_check_thread = threading.Thread(target=check_gui_logged_out)
    gui_logged_check_thread.daemon = True  # Ensure the thread terminates when the main program exits
    gui_logged_check_thread.start()

    # Load background image
    bg_image = Image.open("icons/background.jpeg")
    bg_image = bg_image.resize((1024, 600), Image.Resampling.LANCZOS)  # Resize to fit the window size
    bg_photo = ImageTk.PhotoImage(bg_image)

    # Add background image as a Label
    background_label = tk.Label(root, image=bg_photo)
    background_label.place(relwidth=1, relheight=1)  # Set it to cover the entire window

    # Styling (for buttons, labels, and frames)
    button_bg_color = "#4CAF50"
    button_fg_color = "white"
    label_font = ("Arial", 16)  # Increased font size for better readability
    button_font = ("Arial", 14, "bold")  # Increased button font size

    # Frame for Login title, image, and login form
    login_frame = tk.Frame(root, bg="#f2f2f2", bd=5)
    
    # Title and image
    title_frame = tk.Frame(login_frame, bg="#f2f2f2", bd=5)
    title_label = tk.Label(title_frame, text="Login", font=("Helvetica", 22, "bold"), fg="#333", bg="#f2f2f2")
    
    # Load and resize the image to fit next to "Login"
    smart_img = Image.open("icons/smart.png")
    smart_img = smart_img.resize((90, 90), Image.Resampling.LANCZOS)  # Resize the image to make it bigger
    smart_img_photo = ImageTk.PhotoImage(smart_img)
    image_label = tk.Label(title_frame, image=smart_img_photo, bg="#f2f2f2")

    # Pack the title and image side by side
    title_label.pack(side="left", padx=10)
    image_label.pack(side="left", padx=10)
    
    title_frame.pack(pady=20)  # Add space between title and login form

    # Login Form
    tk.Label(login_frame, text="Username", font=label_font, bg="#f2f2f2").pack()
    login_username_entry = tk.Entry(login_frame, font=label_font)
    login_username_entry.pack(pady=10)
    #bind_keyboard_to_entry(login_username_entry)  # Bind keyboard to username entry
    
    tk.Label(login_frame, text="Password", font=label_font, bg="#f2f2f2").pack()
    login_password_entry = tk.Entry(login_frame, show="*", font=label_font)
    login_password_entry.pack(pady=10)
    #bind_keyboard_to_entry(login_password_entry)  # Bind keyboard to password entry

    # Login Button
    tk.Button(login_frame, text="Login", command=handle_login, font=button_font, bg=button_bg_color, fg=button_fg_color).pack(pady=15, fill="x", padx=50)

    # Signup Link
    tk.Button(login_frame, text="                   Sign Up                   ", command=show_signup, font=button_font, bg=button_bg_color, fg=button_fg_color).pack(pady=15, fill="x", padx=50)

    # Signup Frame
    signup_frame = tk.Frame(root, bg="#f2f2f2", bd=5)
    tk.Label(signup_frame, text="Sign Up", font=("Helvetica", 22, "bold"), bg="#f2f2f2").pack(pady=30)
    tk.Label(signup_frame, text="Username", font=label_font, bg="#f2f2f2").pack()
    signup_username_entry = tk.Entry(signup_frame, font=label_font)
    signup_username_entry.pack(pady=10)
    #bind_keyboard_to_entry(signup_username_entry)  # Bind keyboard to signup username entry
    
    tk.Label(signup_frame, text="Password", font=label_font, bg="#f2f2f2").pack()
    signup_password_entry = tk.Entry(signup_frame, show="*", font=label_font)
    signup_password_entry.pack(pady=10)
    #bind_keyboard_to_entry(signup_password_entry)  # Bind keyboard to signup password entry
    
    tk.Label(signup_frame, text="Email", font=label_font, bg="#f2f2f2").pack()
    signup_email_entry = tk.Entry(signup_frame, font=label_font)
    signup_email_entry.pack(pady=10)
    #bind_keyboard_to_entry(signup_email_entry)  # Bind keyboard to email entry

    tk.Button(signup_frame, text="Sign Up", command=handle_signup, font=button_font, bg=button_bg_color, fg=button_fg_color).pack(pady=15, fill="x", padx=50)
    tk.Button(signup_frame, text="Already have an account? Login", command=show_login, font=button_font, bg=button_bg_color, fg=button_fg_color).pack(pady=15, fill="x", padx=50)

    # Initially show the login frame
    login_frame.pack(side="left", anchor="w", padx=110)

    root.mainloop()

if __name__ == "__main__":
    main()