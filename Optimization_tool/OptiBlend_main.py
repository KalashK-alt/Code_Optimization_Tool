# optiblend6-senior
import os
import re
import timeit
import tkinter as tk
import tracemalloc
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext

import matplotlib.pyplot as plt
import pandas as pd

from clone_code import detect_clones, convert_to_clean_code
from dead_code import remove_dead_code
from invariant_analysis import move_loop_invariants_outside_loop


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self,event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        # Create the tooltip window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")

        # Create a label inside the tooltip window
        label = tk.Label(self.tooltip_window, text=self.text, background="#ffffe0", relief="solid", borderwidth=1)
        label.pack(ipadx=1)

    def hide_tooltip(self,event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def count_lines(code):
    return len([line for line in code.split('\n') if line.strip()])


def show_line_remove_message(original, removed):
    messagebox.showinfo("Line Count", f"original lines: {original}\nremoved lines: {removed}")


def save_file(code_to_save):
    downloads_path = str(Path.home() / "Downloads")
    cleaned_file_path = os.path.splitext(entry_path.get())[0] + "_cleaned.py"
    with open(cleaned_file_path, "w") as f:
        f.write(code_to_save)
    messagebox.showinfo("File saved", f"file saved successfully at: \n{cleaned_file_path}")


def browse_file():
    filename = filedialog.askopenfilename()
    if filename:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, filename)
        display_selected_code(filename)
        check_enable_buttons()


def display_selected_code(filename):
    with open(filename, 'r') as file:
        selected_code_text.delete(1.0, tk.END)
        selected_code_text.insert(tk.END, file.read())
        check_enable_buttons()


rl = 0
ol = 0
dcl = 0
ccl = 0
ial = 0
tb = 0
ta = 0
mb = 0
ma = 0


def detect_dead_code():
    global rl, ol, dcl, tb, ta, mb, ma
    file_path = entry_path.get()
    with open(file_path, 'r') as file:
        before_lines = count_lines(file.read())
        rl = before_lines
    with open(file_path, 'r') as file:
        code = file.read()
        a, b, c = remove_dead_code(code)
        ol = count_lines(a)
        dcl = rl - ol
        tb = execute_code_timed(code)
        ta = execute_code_timed(a)
        mb = execute_code_memory(code)
        ma = execute_code_memory(a)
    eliminated_code_text.delete(1.0, tk.END)
    eliminated_code_text.insert(tk.END, b)
    removed_lines = count_lines(b)
    print(c)
    if previewD(code, a, c):
        show_line_remove_message(before_lines, removed_lines)
        show_clean_code(a)


def detect_code_clones():
    global rl, ol, ccl, tb, ta, mb, ma
    file_path = entry_path.get()
    with open(file_path, 'r') as file:
        code = file.read()

    before_lines = count_lines(code)  # Count total lines before
    rl = before_lines
    b = convert_to_clean_code(code)
    ol = count_lines(b)
    tb = execute_code_timed(code)
    ta = execute_code_timed(b)
    mb = execute_code_memory(code)
    ma = execute_code_memory(b)
    ccl = rl - ol

    clones = detect_clones(code)  # Get the list of clones with line numbers

    # Prepare a string representation of the clones for display
    clone_info = ""
    for clone in clones:
        clone_info += f"Clone detected in function '{clone['name']}' from line {clone['start_line']} to {clone['end_line']}.\n"
        clone_info += f"Similar to function '{clone['similar_to']}' from line {clone['similar_start']} to {clone['similar_end']}.\n\n"

    eliminated_code_text.delete(1.0, tk.END)
    eliminated_code_text.insert(tk.END, clone_info)  # Display the clone information

    # Calculate how many lines are involved in the clones
    removed_lines = sum(clone['end_line'] - clone['start_line'] + 1 for clone in clones)

    if previewC(code, clones, b):  # Pass the clone data to the preview function
        show_line_remove_message(before_lines, removed_lines)  # Show the number of removed lines
        show_clean_code(b)


def detect_invariants():
    global rl, ol, ial, tb, ta, mb, ma
    file_path = entry_path.get()
    with open(file_path, 'r') as file:
        code = file.read()
        opt_code, moved_lines = move_loop_invariants_outside_loop(code)
    rl = ol = count_lines(code)
    ial = len(moved_lines)
    tb = execute_code_timed(code)
    ta = execute_code_timed(opt_code)
    mb = execute_code_memory(code)
    ma = execute_code_memory(opt_code)
    if previewI(code, opt_code, moved_lines):
        show_clean_code(opt_code)


def detect_optimized_code():
    global rl, ol, dcl, ccl, ial, tb, ta, mb, ma
    file_path = entry_path.get()
    with open(file_path, 'r') as file:
        code = file.read()
    before_lines = count_lines(code)
    rl = before_lines
    clean, dead_code, c = remove_dead_code(code)
    dcl = before_lines - count_lines(clean)
    optimized_code, ml = move_loop_invariants_outside_loop(clean)
    ial = len(ml)
    clone_code = convert_to_clean_code(optimized_code)
    detected_clones = detect_clones(optimized_code)
    ccl = count_lines(optimized_code) - count_lines(clone_code)
    ol = count_lines(clone_code)
    tb = execute_code_timed(code)
    ta = execute_code_timed(clone_code)
    mb = execute_code_memory(code)
    ma = execute_code_memory(clone_code)

    eliminated_code_text.delete(1.0, tk.END)
    eliminated_code_text.insert(tk.END, f"Dead Code:\n{dead_code}\n\nDetected Clones:\n{detected_clones}")

    removed_lines = count_lines(dead_code) + (count_lines(code) - count_lines(clone_code)) - 1

    if previewCA(code, detected_clones, c, ml, clone_code):
        show_line_remove_message(before_lines, removed_lines)
        show_clean_code(optimized_code)


def normalize_line(line):
    """
    Normalize a line of code by:
    - Removing extra spaces around operators.
    - Removing extra spaces between tokens.
    - Unifying quotes (convert single quotes to double quotes).
    - Removing comments for comparison.
    - Trimming leading and trailing whitespace.
    """
    # Remove extra spaces around operators and between tokens
    line = re.sub(r'\s*([=+\-*/()])\s*', r'\1', line)

    # Replace single quotes with double quotes for consistency
    line = line.replace("'", '"')

    # Remove any inline comments for comparison
    line_without_comment = line.split('#')[0].strip()

    # Remove multiple spaces between tokens and trim leading/trailing spaces
    return ' '.join(line_without_comment.split()).strip()


def execute_code_timed(code, runs=40):
    # Prepare the code for execution
    setup_code = """
import time
"""

    # Measure execution time using timeit, multiple runs to stabilize results
    try:
        # Run the code multiple times and get the average time
        execution_time = timeit.timeit(stmt=code, setup=setup_code, number=runs) / runs  # Average time per run
    except Exception as e:
        messagebox.showerror("Execution Error", f"Error executing code: {e}")
        execution_time = 0  # Set execution time to 0 if there's an error

    return execution_time


def execute_code_memory(code):
    # Prepare the code for execution
    setup_code = """
import tracemalloc
"""

    # Start memory tracking using tracemalloc
    try:
        tracemalloc.start()

        # Measure the memory usage by executing the code block
        timeit.timeit(stmt=code, setup=setup_code, number=1)  # Number of executions is 1

        # Capture memory statistics
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()  # Stop the tracemalloc tracking

        memory_usage = peak  # Peak memory usage during code execution (in bytes)

    except Exception as e:
        messagebox.showerror("Execution Error", f"Error executing code: {e}")
        memory_usage = 0  # Set memory usage to 0 if there's an error

    return memory_usage


def previewCA(code, clones, removed_lines, moved_lines, oc):
    rem_window = tk.Toplevel(root)
    rem_window.title("Preview Code")
    rem_window.geometry("600x600")

    result = tk.BooleanVar(value=False)

    def next_pressed():
        result.set(True)
        rem_window.destroy()

    def cancel_pressed():
        result.set(False)
        rem_window.destroy()

    def show_graph():
        before_exec_time = execute_code_timed(code)
        after_exec_time = execute_code_timed(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_exec_time, after_exec_time]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.show()

    def show_space_graph():
        before_memory = execute_code_memory(code)
        after_memory = execute_code_memory(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_memory, after_memory]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Memory Usage Comparison')
        plt.ylabel('Memory (bytes)')
        plt.show()

    next_btn = tk.Button(rem_window, text="Next", command=next_pressed, bg="#008080", fg="white", relief="flat")
    next_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    cancel_btn = tk.Button(rem_window, text="Cancel", command=cancel_pressed, bg="#FF6347", fg="white", relief="flat")
    cancel_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    graph_btn = tk.Button(rem_window, text="Show Time Graph", command=show_graph, bg="#FFA500", fg="white",
                          relief="flat")
    graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    space_graph_btn = tk.Button(rem_window, text="Show Space Graph", command=show_space_graph, bg="#32CD32", fg="white",
                                relief="flat")
    space_graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    r_text = scrolledtext.ScrolledText(rem_window, font=("Arial", 10), bg="#DDDDDD", relief="flat")
    r_text.pack(expand=True, fill="both")

    # Normalize: remove leading/trailing spaces, collapse multiple spaces, strip comments
    raw_code_lines = code.split('\n')

    # Normalize the code (e.g., remove unnecessary spaces)
    raw_code_lines = [normalize_line(line) for line in raw_code_lines]

    for clone in clones:
        start_line = clone["start_line"]
        end_line = clone["end_line"]

        # Add the cloned lines with different formatting
        for i in range(start_line - 1, end_line):  # ast uses 1-based line numbers
            r_text.insert(tk.END, raw_code_lines[i] + "\n", "dead")

        # Insert the rest of the code normally
    for i, line in enumerate(raw_code_lines):
        if i < len(raw_code_lines):
            if not any(clone["start_line"] - 1 <= i <= clone["end_line"] - 1 for clone in clones):
                r_text.insert(tk.END, line + "\n", "clean")

    # Display the raw code, with moved lines highlighted in blue
    for line_num, raw_line in enumerate(raw_code_lines, start=1):
        if line_num in moved_lines:
            r_text.insert(tk.END, raw_line + "\n", "Invariant")  # Highlight moved lines in blue
        else:
            r_text.insert(tk.END, raw_line + "\n", "clean")  # All other lines in black
    # Display each line, highlighting removed lines in red
    for idx, line in enumerate(raw_code_lines, start=1):
        if idx in removed_lines:
            # Highlight removed lines in red
            r_text.insert(tk.END, line + "\n", "dead")
        else:
            # Normal lines in black
            r_text.insert(tk.END, line + "\n", "clean")

    r_text.tag_configure("clean", foreground="black")
    r_text.tag_configure("dead", foreground="red")
    r_text.tag_configure("Invariant", foreground="green")
    r_text.tag_configure("comment", foreground="black", font=("Arial", 10, "bold"))

    rem_window.wait_window()
    return result.get()


def previewC(code, clones, oc):
    rem_window = tk.Toplevel(root)
    rem_window.title("Preview Code")
    rem_window.geometry("600x600")

    result = tk.BooleanVar(value=False)

    def next_pressed():
        result.set(True)
        rem_window.destroy()

    def cancel_pressed():
        result.set(False)
        rem_window.destroy()

    def show_graph():
        before_exec_time = execute_code_timed(code)
        after_exec_time = execute_code_timed(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_exec_time, after_exec_time]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.show()

    def show_space_graph():
        before_memory = execute_code_memory(code)
        after_memory = execute_code_memory(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_memory, after_memory]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Memory Usage Comparison')
        plt.ylabel('Memory (bytes)')
        plt.show()

    next_btn = tk.Button(rem_window, text="Next", command=next_pressed, bg="#008080", fg="white", relief="flat")
    next_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    cancel_btn = tk.Button(rem_window, text="Cancel", command=cancel_pressed, bg="#FF6347", fg="white", relief="flat")
    cancel_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    graph_btn = tk.Button(rem_window, text="Show Time Graph", command=show_graph, bg="#FFA500", fg="white",
                          relief="flat")
    graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    space_graph_btn = tk.Button(rem_window, text="Show Space Graph", command=show_space_graph, bg="#32CD32", fg="white",
                                relief="flat")
    space_graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    r_text = scrolledtext.ScrolledText(rem_window, font=("Arial", 10), bg="#DDDDDD", relief="flat")
    r_text.pack(expand=True, fill="both")

    code_lines = code.split('\n')

    # Highlight the cloned sections
    for clone in clones:
        start_line = clone["start_line"]
        end_line = clone["end_line"]

        # Add the cloned lines with different formatting
        for i in range(start_line - 1, end_line):  # ast uses 1-based line numbers
            r_text.insert(tk.END, code_lines[i] + "\n", "dead")

    # Insert the rest of the code normally
    for i, line in enumerate(code_lines):
        if i < len(code_lines):
            if not any(clone["start_line"] - 1 <= i <= clone["end_line"] - 1 for clone in clones):
                r_text.insert(tk.END, line + "\n", "clean")

    r_text.tag_configure("clean", foreground="black")
    r_text.tag_configure("dead", foreground="blue")

    rem_window.wait_window()
    return result.get()


def previewD(code, oc, removed_lines):
    rem_window = tk.Toplevel(root)
    rem_window.title("Preview Code")
    rem_window.geometry("600x600")

    result = tk.BooleanVar(value=False)

    def next_pressed():
        result.set(True)
        rem_window.destroy()

    def cancel_pressed():
        result.set(False)
        rem_window.destroy()

    def show_graph():
        before_exec_time = execute_code_timed(code)
        after_exec_time = execute_code_timed(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_exec_time, after_exec_time]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.show()

    def show_space_graph():
        before_memory = execute_code_memory(code)
        after_memory = execute_code_memory(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_memory, after_memory]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Memory Usage Comparison')
        plt.ylabel('Memory (bytes)')
        plt.show()

    next_btn = tk.Button(rem_window, text="Next", command=next_pressed, bg="#008080", fg="white", relief="flat")
    next_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    cancel_btn = tk.Button(rem_window, text="Cancel", command=cancel_pressed, bg="#FF6347", fg="white", relief="flat")
    cancel_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    graph_btn = tk.Button(rem_window, text="Show Time Graph", command=show_graph, bg="#FFA500", fg="white",
                          relief="flat")
    graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    space_graph_btn = tk.Button(rem_window, text="Show Space Graph", command=show_space_graph, bg="#32CD32", fg="white",
                                relief="flat")
    space_graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    r_text = scrolledtext.ScrolledText(rem_window, font=("Arial", 10), bg="#DDDDDD", relief="flat")
    r_text.pack(expand=True, fill="both")

    # Split the original code into lines
    raw_code_lines = code.split('\n')

    # Display each line, highlighting removed lines in red
    for idx, line in enumerate(raw_code_lines, start=1):
        if idx in removed_lines:
            # Highlight removed lines in red
            r_text.insert(tk.END, line + "\n", "dead")
        else:
            # Normal lines in black
            r_text.insert(tk.END, line + "\n", "clean")

    # Configure text styles
    r_text.tag_configure("clean", foreground="black")
    r_text.tag_configure("dead", foreground="red")

    rem_window.wait_window()
    return result.get()


def previewI(code, oc, moved_lines):
    print(moved_lines)
    rem_window = tk.Toplevel(root)
    rem_window.title("Preview Code")
    rem_window.geometry("600x600")

    result = tk.BooleanVar(value=False)

    def next_pressed():
        result.set(True)
        rem_window.destroy()

    def cancel_pressed():
        result.set(False)
        rem_window.destroy()

    def show_graph():
        before_exec_time = execute_code_timed(code)
        after_exec_time = execute_code_timed(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_exec_time, after_exec_time]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Execution Time Comparison')
        plt.ylabel('Time (seconds)')
        plt.show()

    def show_space_graph():
        before_memory = execute_code_memory(code)
        after_memory = execute_code_memory(oc)
        times = ['Before Optimization', 'After Optimization']
        values = [before_memory, after_memory]

        plt.bar(times, values, color=['red', 'green'])
        plt.title('Memory Usage Comparison')
        plt.ylabel('Memory (bytes)')
        plt.show()

    next_btn = tk.Button(rem_window, text="Next", command=next_pressed, bg="#008080", fg="white", relief="flat")
    next_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    cancel_btn = tk.Button(rem_window, text="Cancel", command=cancel_pressed, bg="#FF6347", fg="white", relief="flat")
    cancel_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    graph_btn = tk.Button(rem_window, text="Show Time Graph", command=show_graph, bg="#FFA500", fg="white",
                          relief="flat")
    graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    space_graph_btn = tk.Button(rem_window, text="Show Space Graph", command=show_space_graph, bg="#32CD32", fg="white",
                                relief="flat")
    space_graph_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    r_text = scrolledtext.ScrolledText(rem_window, font=("Arial", 10), bg="#DDDDDD", relief="flat")
    r_text.pack(expand=True, fill="both")

    # Split the code into lines
    raw_code_lines = code.split('\n')

    # Normalize the code (e.g., remove unnecessary spaces)
    raw_code_lines = [normalize_line(line) for line in raw_code_lines]

    # Display the raw code, with moved lines highlighted in blue
    for line_num, raw_line in enumerate(raw_code_lines, start=1):
        if line_num in moved_lines:
            r_text.insert(tk.END, raw_line + "\n", "moved")  # Highlight moved lines in blue
        else:
            r_text.insert(tk.END, raw_line + "\n", "clean")  # All other lines in black

    # Configure text tag styles
    r_text.tag_configure("clean", foreground="black")
    r_text.tag_configure("moved", foreground="blue", font=("Arial", 10, "italic"))

    rem_window.wait_window()
    return result.get()


def show_clean_code(c):
    rem_window = tk.Toplevel(root)
    rem_window.title("Filtered code")
    rem_window.geometry("600x400")

    save_btn = tk.Button(rem_window, text="Save code", command=lambda: save_file(c), bg="#008080", fg="white",
                         relief="flat")
    save_btn.pack(side=tk.BOTTOM, padx=(0, 5), ipady=5)

    r_text = scrolledtext.ScrolledText(rem_window, font=("Arial", 10), bg="#DDDDDD", relief="flat")
    r_text.pack(expand=True, fill="both")
    r_text.insert(tk.END, c)


def apply_style(window):
    window.config(bg="#CCCCCC")


def reset():
    entry_path.delete(0, tk.END)
    selected_code_text.delete(1.0, tk.END)
    eliminated_code_text.delete(1.0, tk.END)
    entry_path.insert(0, "Enter file path...")
    button_dead_code.config(state="disabled")
    button_code_clones.config(state="disabled")
    button_invariants.config(state="disabled")
    button_optimized_code.config(state="disabled")


def check_enable_buttons():
    file_path = entry_path.get()
    selected_code = selected_code_text.get(1.0, tk.END).strip()
    if file_path and selected_code:
        button_dead_code.config(state="normal")
        button_code_clones.config(state="normal")
        button_invariants.config(state="normal")
        button_optimized_code.config(state="normal")
    else:
        button_dead_code.config(state="disabled")
        button_code_clones.config(state="disabled")
        button_invariants.config(state="disabled")
        button_optimized_code.config(state="disabled")


def update(rl, ol, dcl, ccl, ial, tb, ta, mb, ma, file_name='optimization_results.xlsx'):
    # Define the column headers
    columns = ['Test Case No', 'Code Before Optimization Lines', 'Code After Optimization Lines',
               'Dead Code Lines', 'Code Clone Lines', 'Invariant Lines',
               'Execution Time Before (s)', 'Execution Time After (s)',
               'Memory Utilization Before (MB)', 'Memory Utilization After (MB)']

    # Check if file exists
    if os.path.exists(file_name):
        # If file exists, load the existing data
        df = pd.read_excel(file_name)
        # Get the last test case number and increment it
        test_case_no = df['Test Case No'].max() + 1
    else:
        # If file doesn't exist, create an empty DataFrame with column headers
        df = pd.DataFrame(columns=columns)
        test_case_no = 1  # Start with test case number 1

    # Create a new row with the provided values
    new_row = pd.DataFrame({
        'Test Case No': [test_case_no],
        'Code Before Optimization Lines': [rl],
        'Code After Optimization Lines': [ol],
        'Dead Code Lines': [dcl],
        'Code Clone Lines': [ccl],
        'Invariant Lines': [ial],
        'Execution Time Before (s)': [tb],
        'Execution Time After (s)': [ta],
        'Memory Utilization Before (MB)': [mb],
        'Memory Utilization After (MB)': [ma]
    })

    # Append the new row to the DataFrame using pd.concat
    df = pd.concat([df, new_row], ignore_index=True)

    # Save the updated DataFrame back to the Excel file
    df.to_excel(file_name, index=False)

    print(f"Test case {test_case_no} added successfully.")

def resetv():
    global rl, ol, dcl, ccl, ial, tb, ta, mb, ma
    rl = 0
    ol = 0
    dcl = 0
    ccl = 0
    ial = 0
    tb = 0
    ta = 0
    mb = 0
    ma = 0


root = tk.Tk()
root.title("OptiBlend")
root.config(bg="#001F3F")

window_width = root.winfo_screenwidth() // 2
window_height = root.winfo_screenheight() // 2
root.geometry(f"{window_width}x{window_height}")

frame_file = tk.Frame(root, bg="#CCCCCC", relief="groove", bd=2)
frame_file.pack(padx=10, pady=(10, 5), fill="x")

entry_path = tk.Entry(frame_file, bg="#DDDDDD", relief="flat")

entry_path.insert(0, "Enter file path...")
entry_path.bind("<FocusIn>", lambda event: entry_path.delete(0, tk.END))
entry_path.bind("<FocusOut>",
                lambda event: entry_path.insert(0, "Enter file path...") if not entry_path.get() else None)
entry_path.pack(side=tk.LEFT, padx=(5, 0), ipady=5, fill="x", expand=True)

button_browse = tk.Button(frame_file, text="Browse", command=browse_file, bg="#008080", fg="white", relief="flat")
button_browse.pack(side=tk.LEFT, padx=(0, 5), ipady=5)
ToolTip(button_browse, "Browse for a file")

frame_selected_code = tk.Frame(root, bg="#CCCCCC", relief="groove", bd=2)
frame_selected_code.pack(padx=10, pady=5, fill="both", expand=True)

selected_code_label = tk.Label(frame_selected_code, text="Selected Code:", bg="#CCCCCC")
selected_code_label.pack(anchor="w", padx=5, pady=(5, 0))

selected_code_text = scrolledtext.ScrolledText(frame_selected_code, bg="#DDDDDD", relief="flat", height=10, width=80)
selected_code_text.pack(fill="both", expand=True, padx=5)
selected_code_text.bind("<KeyRelease>", lambda event: check_enable_buttons())

frame_buttons = tk.Frame(root, bg="#001F3F")
frame_buttons.pack(padx=10, pady=5, fill="x")

button_dead_code = tk.Button(frame_buttons, text="Dead Code Elimination", command=detect_dead_code, bg="#008080",
                             fg="white", relief="flat", state="disabled")
button_dead_code.grid(row=0, column=0, padx=(0, 5))
ToolTip(button_dead_code, "Detect and remove dead code")

button_code_clones = tk.Button(frame_buttons, text="Code Cloning", command=detect_code_clones, bg="#008080", fg="white",
                               relief="flat", state="disabled")
button_code_clones.grid(row=0, column=1, padx=(0, 5))
ToolTip(button_code_clones, "Detect and remove code clones")

button_invariants = tk.Button(frame_buttons, text="Detect Invariants", command=detect_invariants, bg="#008080",
                              fg="white", relief="flat", state="disabled")
button_invariants.grid(row=0, column=2, padx=(0, 5))
ToolTip(button_invariants, "Detect and remove loop invariants")

button_optimized_code = tk.Button(frame_buttons, text="Combined Analysis", command=detect_optimized_code, bg="#008080",
                                  fg="white", relief="flat", state="disabled")
button_optimized_code.grid(row=0, column=3)




button_optimized_code.grid(row=0, column=3, padx=(0, 5))
ToolTip(button_optimized_code,
        "Combined analysis: Dead Code Elimination, Code Cloning Detection, and Loop Invariant Analysis")

button_reset = tk.Button(frame_buttons, text="Reset", command=reset, bg="#FF5733", fg="white", relief="flat")
button_reset.grid(row=0, column=4, padx=(0, 5))
ToolTip(button_reset, "Reset all inputs")

button_save = tk.Button(
    frame_buttons,
    text="Save Results to Excel",
    command=lambda: update(rl, ol, dcl, ccl, ial, tb, ta, mb, ma),  # Use lambda to defer execution
    bg="#008080",
    fg="white",
    relief="flat"
)

button_save.grid(row=0, column=5, padx=(0, 5))

button_reset = tk.Button(frame_buttons, text="Resetglobals", command=resetv, bg="#FF5733", fg="white", relief="flat")
button_reset.grid(row=0, column=4, padx=(0, 5))



frame_eliminated_code = tk.Frame(root, bg="#CCCCCC", relief="groove", bd=2)
frame_eliminated_code.pack(padx=10, pady=5, fill="both", expand=True)

eliminated_code_label = tk.Label(frame_eliminated_code, text="Eliminated Code:", bg="#CCCCCC")
eliminated_code_label.pack(anchor="w", padx=5, pady=(5, 0))

eliminated_code_text = scrolledtext.ScrolledText(frame_eliminated_code, bg="#DDDDDD", relief="flat", height=10,
                                                 width=80)
eliminated_code_text.pack(fill="both", expand=True, padx=5)


root.mainloop()
