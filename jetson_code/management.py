import time
import os
import subprocess

def run_image_classification():
    os.system("python3 image_classification.py")

def main():
    # Start the InitialGUI.py script
    gui_process = subprocess.Popen(["python3.8", "InitialGUI.py"])
    if os.path.exists("initial_gui_closed.txt"):
        os.remove("initial_gui_closed.txt")
    try:
        while True:

            if gui_process.poll() is not None:
                print("InitialGUI.py has terminated. Exiting...")
                break  # Exit the loop if InitialGUI.py is no longer running
            # Check for the initial_gui_closed.txt file
            if os.path.exists("initial_gui_closed.txt"):
                # Delete the initial_gui_closed.txt file
                os.remove("initial_gui_closed.txt")
                print("InitialGUI.py has terminated. Exiting...")
                break  # Exit the loop

            # Check for management signals
            if os.path.exists("management_signal.txt"):
                with open("management_signal.txt", "r") as f:
                    signal = f.read().strip()

                if signal == "In button clicked" or signal == "Out button clicked":
                    run_image_classification()

                os.remove("management_signal.txt")

            time.sleep(1)
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nTerminating the application...")
    finally:
        # Ensure the GUI process is terminated when the script exits
        if gui_process.poll() is None:  # Check if the process is still running
            gui_process.terminate()
            gui_process.wait()  # Wait for the process to terminate
        print("Application terminated.")

if __name__ == "__main__":
    main()