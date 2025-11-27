import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import subprocess
import os
import json
from datetime import datetime
import time
import re
from tkinter import messagebox
from datetime import datetime, timedelta
from item_manager import Expired, ExpiringSoon, InStock, Shopping, DefaultList
import sys

root = tk.Tk()
root.title("Smart Refrigerator")
root.geometry("1024x600")
root.configure(bg='#f0f0f0')

# Get the current user from the current_user.txt file
def get_current_user():
    if os.path.exists("current_user.txt"):
        with open("current_user.txt", "r") as file:
            return file.read().strip()
    return None

# Get the current user
user_name = get_current_user()
if not user_name:
    messagebox.showerror("Error", "No user logged in. Please log in first.")
    root.destroy()
    exit()

# Initialize ItemManager instances with the user's name
Is = InStock("in_stock_list", user_name)
es = ExpiringSoon("expiring_soon_list", user_name)
ex = Expired("expired_list", user_name)
sh = Shopping("shopping_list", user_name)
default_list = DefaultList(user_name)

if os.path.exists("current_user.txt"):
    os.remove("current_user.txt")

# Function to enter fullscreen
def enter_fullscreen(event=None):
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.overrideredirect(True)

# Function to exit fullscreen
def exit_fullscreen(event=None):
    root.attributes("-fullscreen", False)
    root.attributes("-topmost", False)
    root.overrideredirect(False)

# Bind the F1 key to enter fullscreen
root.bind("<F1>", enter_fullscreen)

# Bind the Escape key to exit fullscreen
root.bind("<Escape>", exit_fullscreen)

button_frame = tk.Frame(root, bg='#f0f0f0')
button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky='n')

recognized_item_path = "recognized_item.txt"
recognition_terminated_path = "recognition_terminated.txt"

# Translation list
translation_list = {
    "Granny Smith": "Apple",
    "cucumber": "Cucumber",
    "cuke": "Cucumber",
    "cucumber, cuke": "Cucumber",
    "pineapple": "Pineapple",
    "ananas": "Pineapple",
    "lemon": "Lemon",
    "banana": "Banana",
    "dough": "Lemon",
    "spaghetti": "Lemon",
    "spaghetti squash": "Lemon"
}

# Custom styles
HEADER_FONT = ("Roboto", 24, "bold")
BUTTON_FONT = ("Roboto", 14, "bold")
LABEL_FONT = ("Roboto", 16)
INPUT_FONT = ("Roboto", 14)

def on_enter(e, button, color):
    button['background'] = color

def on_leave(e, button, color):
    button['background'] = color

def inform_management():
    # Function to inform the management file when the "In" button is clicked
    with open("management_signal.txt", "w") as signal_file:
        signal_file.write("In button clicked")

def in_button_click():
    if os.path.exists(recognition_terminated_path):
        os.remove(recognition_terminated_path)
    inform_management()
    while not os.path.exists("recognition_terminated.txt"):
        time.sleep(0.1)  # Check every 100 milliseconds

    display_recognized_item()

def out_button_click():
    if os.path.exists(recognition_terminated_path):
        os.remove(recognition_terminated_path)
    inform_management()
    while not os.path.exists("recognition_terminated.txt"):
        time.sleep(0.1)  # Check every 100 milliseconds

    display_recognized_item(out=True)

def display_recognized_item(out=False):
    if os.path.exists(recognized_item_path):
        with open(recognized_item_path, "r") as file:
            recognized_item = file.read().strip()
        confirmation_window(recognized_item, out)
    else:
        confirmation_window("No recognized item found.", out)
    
    # Delete the recognition_terminated.txt file if it exists
    if os.path.exists(recognition_terminated_path):
        os.remove(recognition_terminated_path)

def confirmation_window(recognized_item, out):
    disable_main_gui()
    recognized_item = translate_item(recognized_item)
    # Check if recognized_item is valid
    

    confirm_window = tk.Toplevel(root)
    confirm_window.title("Confirmation")
    confirm_window.geometry("770x250")
    confirm_window.transient(root)
    confirm_window.grab_set()
    confirm_window.focus_set()
    confirm_window.configure(bg='#ffffff')

    tk.Label(confirm_window, text=f"The recognized item is: {recognized_item}. Please confirm or decline.", font=LABEL_FONT, fg="black", bg='#ffffff',height=3).pack(pady=20)
    confirm_button = tk.Button(confirm_window, text="Confirm", bg="#4CAF50", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=11, height=2)
    decline_button = tk.Button(confirm_window, text="Decline", command=lambda: [confirm_window.destroy(), decline()], bg="#f44336", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=11, height=2)
    add_manually_button = tk.Button(confirm_window, text="Add Manually" if not out else "Remove Manually", command=lambda: [confirm_window.destroy(), add_manually() if not out else remove_manually()], bg="#FFC107", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=12, height=2)
    confirm_button.pack(side=tk.LEFT, padx=40, pady=10, ipadx=10, anchor=tk.CENTER)
    add_manually_button.pack(side=tk.RIGHT, padx=40, pady=10, ipadx=10, anchor=tk.CENTER)
    decline_button.pack(side=tk.RIGHT, padx=20, pady=10, ipadx=10, anchor=tk.CENTER)

    if out:
        confirm_button.config(command=lambda: [confirm_out(recognized_item), confirm_window.destroy()])
    else:
        confirm_button.config(command=lambda: [confirm_in(recognized_item), confirm_window.destroy()])
    enable_main_gui()

def translate_item(item_name):
    return translation_list.get(item_name, item_name)

def is_valid_item_name(item_name):
    # Check if the item name is empty
    if not item_name:
        return False
    # Check if the item name is too long
    if len(item_name) > 50:
        return False
    # Check if the item name is in the list of valid refrigerator items (case-insensitive)
    existing_items = Is.get_items()
    lower_item_name = item_name.lower()
    return lower_item_name in [item['name'].lower() for item in existing_items]

def remove_manually():
    item_name = ask_for_input("Please enter the item name", center_confirm=True, validate_name=True)
    if item_name:
        item_name=item_name.lower().capitalize()
        translated_item = translate_item(item_name)
        if not Is.has_item(translated_item):
            messagebox.showerror("Item Not Found", f"There is no such item '{translated_item}' inside the refrigerator.")
            close_confirmation()
            return
        amount = ask_for_input("Please enter the quantity to remove from the refrigerator", skip_allowed=True, validate_amount=True,remove_item=True)

        if amount.lower() == "skip" :
            # If user skips entering the amount
            Is.remove_item_by_name(translated_item)
            es.remove_item_by_name(translated_item)
            ex.remove_item_by_name(translated_item)
            if not sh.has_item(translated_item):
                sh.add_item(translated_item, "1", "N/A", datetime.now().strftime("%d/%m/%Y"))
        else:
            amount = int(amount)
            if amount <= 0 or amount >= 20:
                messagebox.showerror("Invalid Amount", "Amount must be a positive integer less than 20.")
                return

            # Decrease the item's amount in stock list
            current_amount = int(Is.get_item_amount(translated_item))
            new_amount = current_amount - amount

            if new_amount <= 0:
                Is.remove_item_by_name(translated_item)
                if ex.has_item(translated_item):
                    ex.remove_item_by_name(translated_item)
                if es.has_item(translated_item):
                    es.remove_item_by_name(translated_item)    
                if not sh.has_item(translated_item):
                    sh.add_item(translated_item, "1", "N/A", datetime.now().strftime("%d/%m/%Y"))
            else:
                Is.update_item(translated_item, new_amount)
                es.update_item(translated_item, new_amount)
                ex.update_item(translated_item, new_amount)

    close_confirmation()
    
def add_manually():
    item_name = ask_for_input("Please enter the item name", center_confirm=True, validate_name=True, source='add_manually')
    if item_name:
        item_name = item_name.lower().capitalize()
        translated_item = translate_item(item_name)
        existing_items = Is.get_items()
        default_items = default_list.get_items()
        
        if translated_item not in default_items:
            response = messagebox.askyesno("Add to Default List", f"The item '{translated_item}' does not exist in the default list. Do you want to add it?")
            if response:
                # Add the item to the default list in DynamoDB (if applicable)
                pass
            else:
                messagebox.showerror("Item Not Added", f"The item '{translated_item}' was not added to the default list.")
                return
        if Is.has_item(translated_item):
            tk.messagebox.showinfo("Item Exists", f"The item '{translated_item}' is already inside the refrigerator.")
            return

        amount = ask_for_input("Please enter amount", skip_allowed=True, validate_amount=True, source='add_manually')
        if amount == "skip" or amount == "":
            amount = "1"
        expiration_date = ask_for_input("Please enter expiration date (DD/MM/YYYY)", placeholder="DD/MM/YYYY", skip_allowed=True, validate_date=True, source='add_manually',skipingExpiriationDate=True)
        if expiration_date == "skip" or expiration_date == "":
            expiration_date = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
        entry_date = datetime.now().strftime("%d/%m/%Y")
        Is.add_item(translated_item, amount, expiration_date, entry_date)
        sh.remove_item_by_name(translated_item)
        ex.remove_item_by_name(translated_item)
        update_defaulListBox(default_treeview)
        close_confirmation()

def confirm_in(recognized_item, source=None):
    translated_item = translate_item(recognized_item)
    if source != 'add_manually' and not is_valid_item_name(translated_item):
        messagebox.showerror("Invalid Item", f"The recognized item '{translated_item}' cannot be saved in the refrigerator.")
        return
    #translate_item = translate_item.lower().capitalize()
    if Is.has_item(translated_item):
            tk.messagebox.showinfo("Item Exists", f"The item '{translated_item}' is already inside the refrigerator.")
            return
    amount = ask_for_input("Please enter amount", skip_allowed=True, validate_amount=True, source=source)
    if amount == "skip" or amount == "":
        amount = "1"
    expiration_date = ask_for_input("Please enter expiration date (DD/MM/YYYY)", placeholder="DD/MM/YYYY", skip_allowed=True, validate_date=True, source=source,skipingExpiriationDate=True)
    if expiration_date == "skip" or expiration_date == "":
        expiration_date = (datetime.now() + timedelta(days=10)).strftime("%d/%m/%Y")
    entry_date = datetime.now().strftime("%d/%m/%Y")
    Is.add_item(translated_item, amount, expiration_date, entry_date)
    sh.remove_item_by_name(translated_item)
    ex.remove_item_by_name(translated_item)
    close_confirmation()

def confirm_out(recognized_item):
    translated_item = translate_item(recognized_item)
    translated_item.lower().capitalize
    # Check if the item exists in the stock list
    if not Is.has_item(translated_item):
        messagebox.showerror("Item Not Found", f"There is no such item '{translated_item}' inside the refrigerator.")
        close_confirmation()
        return

    # Ask for the amount to exit
    amount = ask_for_input("Please enter the quantity to remove from the refrigerator", skip_allowed=True, validate_amount=True,remove_item=True)

    if amount.lower() == "skip" :
        # If user skips entering the amount
        Is.remove_item_by_name(translated_item)
        es.remove_item_by_name(translated_item)
        ex.remove_item_by_name(translated_item)
        if not sh.has_item(translated_item):
            sh.add_item(translated_item, "1", "N/A", datetime.now().strftime("%d/%m/%Y"))
    else:
        amount = int(amount)
        if amount <= 0 or amount >= 20:
            messagebox.showerror("Invalid Amount", "Amount must be a positive integer less than 20.")
            return

        # Decrease the item's amount in stock list
        current_amount = int(Is.get_item_amount(translated_item))
        new_amount = current_amount - amount

        if new_amount <= 0:
            Is.remove_item_by_name(translated_item)
            if ex.has_item(translated_item):
                    ex.remove_item_by_name(translated_item)
            if es.has_item(translated_item):
                es.remove_item_by_name(translated_item)
            if not sh.has_item(translated_item):
                sh.add_item(translated_item, "1", "N/A", datetime.now().strftime("%d/%m/%Y"))
        else:
            Is.update_item(translated_item, new_amount)
            es.update_item(translated_item, new_amount)
            ex.update_item(translated_item, new_amount)

    close_confirmation()

def close_confirmation():
    enable_main_gui()

def get_recognized_item():
    with open(recognized_item_path, "r") as file:
        return file.read().strip()

def ask_for_input(prompt, placeholder="", skip_allowed=False, center_confirm=False, validate_name=False, validate_amount=False, validate_date=False, source=None, remove_item=False,skipingExpiriationDate=False):
    # Open the on-screen keyboard with error handling
    try:
        keyboard_process = subprocess.Popen(["florence"])
    except FileNotFoundError:
        tk.messagebox.showerror("Error", "On-screen keyboard not found. Please install florence.")
        return ""

    input_window = tk.Toplevel(root)
    input_window.title("Input")
    input_window.geometry("650x200")
    input_window.transient(root)
    input_window.grab_set()
    input_window.focus_set()
    input_window.configure(bg='#ffffff')

    tk.Label(input_window, text=prompt, font=LABEL_FONT, fg="black", bg='#ffffff').pack(pady=10)

    input_entry = tk.Entry(input_window, font=INPUT_FONT)
    input_entry.pack(pady=10)
    input_entry.insert(0, placeholder)
    input_entry.bind("<FocusIn>", lambda event: on_entry_click(event, placeholder))
    input_entry.bind("<FocusOut>", lambda event: on_focus_out(event, placeholder))

    result = tk.StringVar()

    def close_keyboard():
        if keyboard_process:
            subprocess.run(["pkill", "florence"])

    def on_confirm():
        entered_value = input_entry.get().strip()
        if not entered_value:
            tk.messagebox.showerror("Invalid Input", "Input cannot be empty.")
            return
        if validate_name and source != "add_manually" and not is_valid_item_name(entered_value):
            tk.messagebox.showerror("Invalid Input", "Please enter a valid refrigerator item.")
            return
        if validate_date and not is_valid_date(entered_value):
            tk.messagebox.showerror("Invalid Input", "Please enter a valid expiration date in DD/MM/YYYY format.")
            return
        if validate_amount:
            try:
                amount = int(entered_value)
                if amount <= 0 or amount >= 20:
                    tk.messagebox.showerror("Invalid Input", "Amount must be a positive integer less than 20.")
                    return
            except ValueError:
                tk.messagebox.showerror("Invalid Input", "Amount must be a positive integer less than 20.")
                return
        result.set(entered_value)
        input_window.destroy()
        close_keyboard()
        enable_main_gui()

    confirm_button = tk.Button(input_window, text="Confirm", command=on_confirm, bg="#4CAF50", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=8, height=1)

    if center_confirm:
        confirm_button.pack(pady=10, anchor=tk.CENTER)
    else:
        confirm_button.pack(side=tk.LEFT, padx=80, pady=10, ipadx=10, anchor=tk.CENTER)

    if skip_allowed:
        def on_skip():
            result.set("skip")
            input_window.destroy()
            close_keyboard()
            enable_main_gui()
        if remove_item:
            skip_button = tk.Button(input_window, text="Remove All", command=on_skip, bg="#FFC107", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=8, height=1)
        elif skipingExpiriationDate:
            skip_button = tk.Button(input_window, text="Skip (10 Days)", command=on_skip, bg="#FFC107", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=10, height=1)
        else:
            skip_button = tk.Button(input_window, text="Skip", command=on_skip, bg="#FFC107", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=8, height=1)

        skip_button.pack(side=tk.RIGHT, padx=80, pady=10, ipadx=10, anchor=tk.CENTER)

    def on_close():
        result.set("")
        input_window.destroy()
        close_keyboard()
        enable_main_gui()

    input_window.protocol("WM_DELETE_WINDOW", on_close)

    input_window.wait_window()
    return result.get()

def open_on_screen_keyboard():
    os_type = platform.system()
    if os_type == "Windows":
        os.system("start osk")  # Open On-Screen Keyboard on Windows
    elif os_type == "Linux":
        os.system("onboard &")  # Open On-Screen Keyboard on Linux (make sure 'onboard' is installed)
    elif os_type == "Darwin":  # macOS
        os.system("open -a KeyboardViewer")

    # Reapply full-screen mode
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)

def on_entry_click(event, placeholder):
    if event.widget.get() == placeholder:
        event.widget.delete(0, "end")
        event.widget.insert(0, "")

def on_focus_out(event, placeholder):
    if event.widget.get() == "":
        event.widget.insert(0, placeholder)

def decline():
    close_confirmation()

def update_InStockList(treeview):
    for row in treeview.get_children():
        treeview.delete(row)
    items = Is.get_items()
    for item in items:
        treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def update_expringSoonListBox(treeview):
    for row in treeview.get_children():
        treeview.delete(row)
    items = es.get_items()
    for item in items:
        treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def update_shoppingistBox(treeview):
    for row in treeview.get_children():
        treeview.delete(row)
    items = sh.get_items()
    for item in items:
        shopping_list_treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def update_expiredListBox(treeview):
    for row in treeview.get_children():
        treeview.delete(row)
    items = ex.get_items()
    for item in items:
        treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def update_defaulListBox(treeview):
    for row in treeview.get_children():
        treeview.delete(row)
    default_items = default_list.get_items()  # Fetch default items from DynamoDB
    for item in default_items:
        treeview.insert("", "end", values=(item,))  # Insert the item name directly

def update_expiring_soon():
    today = datetime.now().date()
    in_stock_items = Is.get_items()
    expiring_soon_items = es.get_items()

    for item in in_stock_items:
        expiration_date = item["expiration_date"]
        entry_date = datetime.strptime(item["entry_date"], "%d/%m/%Y").date()

        if expiration_date.lower() == "n/a":
            expiration_date = entry_date + timedelta(days=10)
        else:
            expiration_date = datetime.strptime(expiration_date, "%d/%m/%Y").date()

        days_until_expiration = (expiration_date - today).days

        if 0 < days_until_expiration <= 5:
            already_in_expiring_soon = any(
                es_item["name"] == item["name"] and 
                es_item["expiration_date"] == item["expiration_date"] 
                for es_item in expiring_soon_items
            )
            if already_in_expiring_soon:
                continue
            else:
                show_notification(f"Item '{item['name']}' is expiring soon !", font_color="orange")
            es.add_item(
                    item["name"],
                    item["amount"],
                    item["expiration_date"],
                    item["entry_date"]
                )

def check_and_move_expired_items():
    today = datetime.now().date()
    expiring_soon_items = es.get_items()
    expired_items = ex.get_items()
    items_to_remove = []

    for es_item in expiring_soon_items:
        expiration_date = es_item["expiration_date"]
        entry_date = datetime.strptime(es_item["entry_date"], "%d/%m/%Y").date()

        if expiration_date.lower() == "n/a":
            expiration_date = entry_date + timedelta(days=10)
        else:
            expiration_date = datetime.strptime(expiration_date, "%d/%m/%Y").date()

        if today >= expiration_date:
            if not any(
                expired_item["name"] == es_item["name"] and 
                expired_item["amount"] == es_item["amount"] and 
                expired_item["expiration_date"] == es_item["expiration_date"]
                for expired_item in expired_items
            ):
                ex.add_item(
                    es_item["name"],
                    es_item["amount"],
                    es_item["expiration_date"],
                    es_item["entry_date"]
                )
                sh.add_item(
                    es_item["name"],
                    es_item["amount"],
                    es_item["expiration_date"],
                    es_item["entry_date"]
                )
                # Show notification for expired item
                show_notification(f"Item '{es_item['name']}' has expired!", font_color="red")

            items_to_remove.append(es_item)

    for item in items_to_remove:
        es.remove_item(
            item["name"],
            item["amount"],
            item["expiration_date"]
        )

def periodic_update():
    update_expiring_soon()
    check_and_move_expired_items()
    update_expiredListBox(expired_treeview)
    update_expringSoonListBox(expiring_soon_treeview)
    update_shoppingistBox(shopping_list_treeview)
    update_InStockList(in_stock_treeview)
    update_defaulListBox(default_treeview)  # Update the default list periodically
    
    root.after(1000, periodic_update)  # Call the function every 60 seconds (60000 milliseconds)

def update_default_list(item_name):
    # Add item to default list in DynamoDB (if applicable)
    pass

def show_list_buttons():
    hide_all_lists()  # Hide any open lists
    list_button_frame.grid()
    x_button.grid(row=0, column=1, sticky='ne')

def close_list():
    hide_all_lists()
    show_list_buttons()
    hide_main_gui_buttons()
    add_button.grid_remove()
    remove_button.grid_remove()

def hide_all_lists():
    treeviews = [default_treeview, in_stock_treeview, expiring_soon_treeview, expired_treeview, shopping_list_treeview]
    for treeview in treeviews:
        treeview.grid_remove()
    list_close_button.grid_remove()

def hide_main_gui_buttons():
    in_button.grid_remove()
    out_button.grid_remove()
    advanced_options_button.grid_remove()

def show_main_gui_buttons():
    in_button.grid(row=0, column=0, padx=10, pady=10)
    out_button.grid(row=0, column=1, padx=10, pady=10)
    advanced_options_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

def show_advanced_options():
    hide_main_gui_buttons()
    list_button_frame.grid()
    x_button.grid(row=0, column=1, sticky='ne')

def hide_advanced_options():
    list_button_frame.grid_remove()
    x_button.grid_remove()
    show_main_gui_buttons()

def disable_main_gui():
    in_button.config(state="disabled")
    out_button.config(state="disabled")
    advanced_options_button.config(state="disabled")

def enable_main_gui():
    in_button.config(state="normal")
    out_button.config(state="normal")
    advanced_options_button.config(state="normal")

# Load and resize images
def load_image(path, size):
    img = Image.open(path)
    img = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

def show_list(treeview):
    hide_advanced_options()  # Hide the advanced options list
    treeview.grid(row=1, column=0, columnspan=2, sticky='nsew')
    if treeview == default_treeview:
        scrollbar_DF.grid(row=1, column=2, sticky='ns')
    if treeview == in_stock_treeview:
        scrollbar_IS.grid(row=1, column=2, sticky='ns')    
    if treeview == shopping_list_treeview:
        scrollbar_SL.grid(row=1, column=2, sticky='ns')
    if treeview == expired_treeview:
        scrollbar_E.grid(row=1, column=2, sticky='ns')
    if treeview == expiring_soon_treeview:
        scrollbar_ES.grid(row=1, column=2, sticky='ns')
    
    list_close_button.grid(row=0, column=1, sticky='ne')
    if treeview == default_treeview:
        add_button.grid(row=2, column=0, pady=(10, 20))  # Changed row index to 2
        remove_button.grid(row=2, column=1, pady=(10, 20))  # Changed row index to 2
    else:
        add_button.grid_remove()
        remove_button.grid_remove()

def close_list():
    hide_all_lists()
    show_list_buttons()
    hide_main_gui_buttons()
    scrollbar_DF.grid_remove()
    scrollbar_IS.grid_remove()
    scrollbar_SL.grid_remove()
    scrollbar_E.grid_remove()
    scrollbar_ES.grid_remove()
    add_button.grid_remove()
    remove_button.grid_remove()

def add_item_to_default_list():
    item_name = ask_for_input("Please enter the item name to add", center_confirm=True)
    if item_name:
        item_name = item_name.lower().capitalize()
        existing_items = default_list.get_items()
        if item_name in existing_items:
            tk.messagebox.showerror("Duplicate Item", f"Item '{item_name}' is already in the default list.")
            return
        default_list.add_item(item_name)  # Add the item to the default list in DynamoDB
        update_defaulListBox(default_treeview)  # Refresh the default list view


def remove_item_from_default_list():
    item_name = ask_for_input("Please enter the item you want to remove", center_confirm=True)
    if item_name:
        item_name = item_name.lower().capitalize()
        existing_items = default_list.get_items()
        if item_name not in existing_items:
            tk.messagebox.showerror("Item doesn't exist", f"Item '{item_name}' isn't in the default list.")
            return
        default_list.remove_item(item_name)  # Add the item to the default list in DynamoDB
        update_defaulListBox(default_treeview)  # Refresh the default list view


def center_treeview(treeview):
    treeview.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=100)  # Add padx to center
    add_button.grid(row=2, column=0, pady=(10, 20), columnspan=2, sticky='ew')  # Center the buttons
    remove_button.grid(row=2, column=1, pady=(10, 20), columnspan=2, sticky='ew')  # Center the buttons

def is_valid_date(date_str):
    try:
        exp_date = datetime.strptime(date_str, "%d/%m/%Y")
        if exp_date <= datetime.now():
            return False
        return True
    except ValueError:
        return False

notification_count = 0  # Global counter for notifications

def show_notification(message, duration=6000, font_color="black"):
    global notification_count

    notification_window = tk.Toplevel(root)
    notification_window.title("Notification")
    window_width = 450
    window_height = 40
    
    # Screen resolution
    screen_width = 1024
    screen_height = 600
    
    # Calculate the position for the notification window
    notification_x = screen_width - window_width
    notification_y = notification_count * (window_height + 10)  # Stagger notifications vertically
    
    # Ensure the notifications do not go off-screen
    if notification_y + window_height > screen_height:
        notification_y = screen_height - window_height

    notification_window.geometry(f"{window_width}x{window_height}+{notification_x}+{notification_y}")
    notification_window.overrideredirect(True)  # Remove window decorations
    notification_window.attributes("-topmost", True)  # Ensure it stays on top

    # Load the image
    image = Image.open("icons/expired.png")
    image = image.resize((30, 30),Image.Resampling.LANCZOS)  # Resize the image to fit the window
    image_tk = ImageTk.PhotoImage(image)

    # Enlarge the font size and make it bold
    large_font = ("Helvetica", 16, "bold")

    # Create the label
    notification_label = tk.Label(notification_window, text=message, font=large_font, bg="#f0f0f0", fg=font_color, image=image_tk, compound='left', padx=10, pady=10, wraplength=window_width-70)
    notification_label.image = image_tk  # Keep a reference to avoid garbage collection
    notification_label.pack(expand=True, fill=tk.BOTH)

    def hide_notification():
        global notification_count
        notification_window.destroy()
        notification_count -= 1  # Decrement the counter when the notification is hidden

    notification_window.after(duration, hide_notification)
    notification_count += 1  # Increment the counter when a new notification is shown

icon_size = (64, 64)
button_size = (160, 160)

default_img = load_image("icons/default_list.png", icon_size)
in_stock_img = load_image("icons/in_stock.png", icon_size)
expiring_soon_img = load_image("icons/soon_expired.png", icon_size)
expired_img = load_image("icons/expired.png", icon_size)
shopping_list_img = load_image("icons/shopping_list.png", icon_size)

in_img = load_image("icons/in.png", (200, 200))
out_img = load_image("icons/out.png", button_size)

# UI Elements
header = tk.Label(root, text="Smart Refrigerator", font=HEADER_FONT, fg="black", bg='#f0f0f0')
header.grid(row=0, column=0, columnspan=2, pady=10, sticky='n')

button_frame = tk.Frame(root, bg='#f0f0f0')
button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky='n')

in_button = tk.Button(button_frame, text="In", image=in_img, compound=tk.TOP, width=300, height=300, command=in_button_click, bg="#4CAF50", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
in_button.grid(row=0, column=0, padx=10, pady=10)

out_button = tk.Button(button_frame, text="Out", image=out_img, compound=tk.TOP, width=300, height=300, command=out_button_click, bg="#f44336", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
out_button.grid(row=0, column=1, padx=10, pady=10)

advanced_options_button = tk.Button(button_frame, text="Advanced Options", command=show_advanced_options, bg="#FF8C00", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
advanced_options_button.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='ew')

list_button_frame = tk.Frame(root, bg='#f0f0f0')
list_button_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky='n')
list_button_frame.grid_remove()  # Hide initially

item_label = tk.Label(root, text="", font=LABEL_FONT, fg="black", bg='#f0f0f0')
item_label.grid(row=2, column=0, columnspan=2, pady=10, sticky='n')

notification_label = tk.Label(root, text="", font=LABEL_FONT, fg="red", bg='#f0f0f0')
notification_label.grid(row=0, column=2, padx=10, pady=10, sticky='ne')
notification_label.grid_remove()  # Hide initially

root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

add_button = tk.Button(root, text="Add Item", command=add_item_to_default_list, bg="#4CAF50", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
remove_button = tk.Button(root, text="Remove Item", command=remove_item_from_default_list, bg="#f44336", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)

add_button.grid_remove()
remove_button.grid_remove()

# Treeviews and Close Button
def create_treeview(columns, headings, style):
    treeview = ttk.Treeview(root, columns=columns, show="headings", selectmode="browse")
    for col, heading in zip(columns, headings):
        treeview.heading(col, text=heading, anchor='center')
        treeview.column(col, anchor='center', stretch=tk.YES)  # Stretch columns to fill space
    treeview.tag_configure('default', background='white')
    return treeview

default_treeview = create_treeview(["item"], ["Item"], "Default.Treeview")
default_treeview.grid(row=1, column=1, columnspan=2, sticky='nsew')
default_treeview.grid_remove()

scrollbar_DF = ttk.Scrollbar(root, orient="vertical", command=default_treeview.yview)
default_treeview.configure(yscrollcommand=scrollbar_DF.set)

in_stock_treeview = create_treeview(["item", "amount", "expiration_date", "entry_date"], ["Item", "Amount", "Expiration Date", "Entry Date"], "InStock.Treeview")
in_stock_treeview.grid(row=0, column=0, sticky='nsew')
in_stock_treeview.grid_remove()

scrollbar_IS = ttk.Scrollbar(root, orient="vertical", command=in_stock_treeview.yview)
in_stock_treeview.configure(yscrollcommand=scrollbar_IS.set)

expiring_soon_treeview = create_treeview(["item", "amount", "expiration_date", "entry_date"], ["Item", "Amount", "Expiration Date","Entry Date"], "ExpiringSoon.Treeview")
expiring_soon_treeview.grid(row=0, column=1, sticky='nsew')
expiring_soon_treeview.grid_remove()

scrollbar_ES = ttk.Scrollbar(root, orient="vertical", command=expiring_soon_treeview.yview)
expiring_soon_treeview.configure(yscrollcommand=scrollbar_ES.set)

expired_treeview = create_treeview(["item", "amount", "expiration_date","entry_date"], ["Item", "Amount", "Expiration Date","Entry Date"], "Expired.Treeview")
expired_treeview.grid(row=1, column=0, sticky='nsew')
expired_treeview.grid_remove()

scrollbar_E = ttk.Scrollbar(root, orient="vertical", command=expired_treeview.yview)
expired_treeview.configure(yscrollcommand=scrollbar_E.set)

shopping_list_treeview = create_treeview(["item"], ["Item"], "ShoppingList.Treeview")
shopping_list_treeview.grid(row=1, column=1, sticky='nsew')
shopping_list_treeview.grid_remove()

scrollbar_SL = ttk.Scrollbar(root, orient="vertical", command=shopping_list_treeview.yview)
shopping_list_treeview.configure(yscrollcommand=scrollbar_SL.set)

# Renamed close button for list content
list_close_button = tk.Button(root, text="Close", command=close_list, bg="#f44336", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
list_close_button.grid(row=0, column=1, sticky='ne')
list_close_button.grid_remove()

# Advanced Options Buttons
def create_list_button(frame, image, text, command, bg_color):
    button = tk.Button(frame, text=text, image=image, compound=tk.TOP, command=command, bg=bg_color, fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0, width=400, height=120)
    button.bind("<Enter>", lambda e: on_enter(e, button, bg_color))
    button.bind("<Leave>", lambda e: on_leave(e, button, bg_color))
    return button

default_button = create_list_button(list_button_frame, default_img, "Default List", lambda: show_list(default_treeview), "#2196F3")
in_stock_button = create_list_button(list_button_frame, in_stock_img, "In Stock", lambda: show_list(in_stock_treeview), "#4CAF50")
expiring_soon_button = create_list_button(list_button_frame, expiring_soon_img, "Expiring Soon", lambda: show_list(expiring_soon_treeview), "#FFC107")
expired_button = create_list_button(list_button_frame, expired_img, "Expired", lambda: show_list(expired_treeview), "#f44336")
shopping_list_button = create_list_button(list_button_frame, shopping_list_img, "Shopping List", lambda: show_list(shopping_list_treeview), "#E91E63")

# Adjusting layout to reduce space between buttons and make them longer
in_stock_button.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
shopping_list_button.grid(row=0, column=1, padx=10, pady=10, sticky='ew')
expired_button.grid(row=1, column=0, padx=10, pady=10, sticky='ew')
expiring_soon_button.grid(row=1, column=1, padx=10, pady=10, sticky='ew')
default_button.grid(row=2, column=0, columnspan=2, padx=200, pady=10, sticky='ew')

# Advanced Options Close Button
x_button = tk.Button(root, text="X", command=hide_advanced_options, bg="#f44336", fg="white", font=BUTTON_FONT, relief=tk.FLAT, bd=0)
x_button.grid(row=0, column=1, sticky='ne')
x_button.grid_remove()

def add_scrollbar(treeview):
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=scrollbar.set)
    treeview.grid(row=1, column=0, columnspan=2, sticky='nsew')
    scrollbar.grid(row=1, column=2, sticky='ns')
    return scrollbar

# Load in-stock items from in_stock list
def load_in_stock_items():
    items = Is.get_items()
    for item in items:
        in_stock_treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

# Load in-stock items from expiring_soon
def load_expiring_soon_items():
    items = es.get_items()
    for item in items:
        expiring_soon_treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def load_expired_items():
    items = ex.get_items()
    for item in items:
        expired_treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

def load_shopping_items():
    items = sh.get_items()
    for item in items:
        shopping_list_treeview.insert("", "end", values=(item['name'], item['amount'], item['expiration_date'], item['entry_date']))

load_in_stock_items()
load_expiring_soon_items()
load_expired_items()
load_shopping_items()

def load_default_items():
    for row in default_treeview.get_children():
        default_treeview.delete(row)
    default_items = default_list.get_items()  # Fetch default items from DynamoDB
    for item in default_items:
        default_treeview.insert("", "end", values=(item,))  # Insert the item name directly

load_default_items()

def on_closing():
    # Create a signal file to indicate that GUI.py has closed
    with open("GUI_closed.txt", "w") as f:
        f.write("GUI closed")
    root.destroy()  # Close the GUI window

# Bind the "X" button to the on_closing function
root.protocol("WM_DELETE_WINDOW", on_closing)

def logout():
    # Ask for confirmation
    response = messagebox.askyesno("Log Out", "Are you sure you want to log out?")
    if response:
        with open("GUI_logged_out.txt", "w") as f:
                f.write("GUI_logged_out")
        global gui_process
        time.sleep(2)
        gui_process = subprocess.Popen(["python3.8", "management.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        root.destroy()

# Add the logout button
logout_img = load_image("icons/logout.png", (40, 40))  # Resize the icon to 32x32 pixels
logout_button = tk.Button(root, image=logout_img, command=logout, bg="#f0f0f0", relief=tk.FLAT, bd=0)
logout_button.image = logout_img  # Keep a reference to avoid garbage collection
logout_button.place(x=10, y=530)  # Position the button in the bottom-left corner

root.after(1000, periodic_update) 
root.mainloop()